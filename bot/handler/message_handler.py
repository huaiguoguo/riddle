import datetime
import re
from typing import List, Dict, Any
from decimal import Decimal

import sqlmodel
from sqlalchemy.orm import load_only
from sqlmodel import select, col, update as modelUpdate
from telegram import Update, ForceReply, ChatMemberUpdated, ChatMember, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext

from config.config import get_config
from helper.helper import printlog
from helper.keyboard import keyboard
from orm import check_user_whether, get_session, get_history_issue_only_leopard, get_bet_flow_rebate
from orm.models import FaUser, FaBetting, FaIssue, FaViolation
from utils import filter_emoji, generate_symbol, china_timezone, str_replace, get_value_by_key
from logger import log_except


async def delete_message(context: CallbackContext) -> None:
    try:
        user_message, notice_message = context.job.data
        await user_message.delete()
        await notice_message.delete()
    except Exception as e:
        await log_except(e, True)


async def offense_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    notice_message = await update.message.reply_html("不要发送包含 emoji 表情的消息!")
    try:
        context.job_queue.run_once(delete_message, when=2, data=(update.message, notice_message))
    except Exception as e:
        await log_except(e)


def check_message(message_text) -> list[dict[Any, int]]:
    pattern = r"([\u4e00-\u9fff]{1,2})\s*?(\d{1,5})"
    # pattern = r'([\u4e00-\u9fa5]{1,2})\s*?(\d{2,5})'
    matches = re.findall(pattern, message_text)
    result = [{key: int(value)} for key, value in matches]
    return result


def bet_failed(user_money, bet_cmd, bet_money) -> str:
    bet_min = get_config().get('bet_min')
    bet_max = get_config().get('bet_max')
    bet_office_cmd = get_config().get('bet_office_cmd')

    if bet_cmd not in bet_office_cmd:
        return '投注失败! 投注指令不正确, 请查看群公告!'
        # await bet_rule_notice(update, context, notice_text=notice_text, chat_id=chat_id)
    elif bet_min > bet_money or bet_money > bet_max:
        return f'投注失败! 投注金额范围({bet_min}-{bet_max})!'
        # await bet_rule_notice(update, context, notice_text=notice_text, chat_id=chat_id)
    elif user_money < bet_money:
        return f"投注失败! 余额不足, 当前余额：{user_money}!"

    return ''


async def conform_to_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, pattern_list) -> None:
    text = update.message.text.strip()
    chat_id = update.message.chat.id
    member_id = update.effective_user.id
    current_timestamp = int(datetime.datetime.now(china_timezone).timestamp())

    try:
        break_all = False
        bet_times = 0
        bet_total_money = Decimal(0)
        bet_num_list = []
        with get_session() as session:
            # 查询用户余额是够本次投注
            faUser_wait_statement = select(FaUser).options(load_only('id', 'money')).where(FaUser.tg_uid == member_id, FaUser.tg_chat_id == chat_id)
            user_result = session.exec(faUser_wait_statement).first()
            user_money_after_reduce_bet_money = Decimal(user_result.money)

            # 查询当前正在进行的期数  col(FaBetting.bet_cmd).in_([])
            issue_wait_statement = select(FaIssue).options(load_only('is_lock', 'issue_num')).where(FaIssue.status == 1).order_by(col(FaIssue.id).desc()).limit(1)
            issue_result = session.exec(issue_wait_statement).first()

            if issue_result is None:
                await bet_rule_notice(update, context, notice_text='封盘开奖中,请勿投注.', chat_id=chat_id)
                return None

            if issue_result.is_lock in [1, 2]:
                await bet_rule_notice(update, context, notice_text='已封盘, 禁止投注.', chat_id=chat_id)
                return None

            for index, bet_dict in enumerate(pattern_list):
                for bet_cmd, bet_money in bet_dict.items():
                    bet_money = Decimal(bet_money)
                    if user_money_after_reduce_bet_money < bet_money:
                        break_all = True
                        if bet_times > 0:
                            bet_times_text = f"余额不足, 仅前{bet_times}注 投注成功!"
                        else:
                            bet_times_text = f"余额不足,投注失败!"
                            break_all = True
                        await update.message.reply_html(bet_times_text)
                        break

                    notice_text = bet_failed(user_money_after_reduce_bet_money, bet_cmd, bet_money)
                    if notice_text != '':
                        break_all = True
                        await update.message.reply_html(notice_text)
                    else:
                        bet_office_cmd_odds = get_config().get('bet_office_cmd_odds')
                        bet_office_lattery_odds = bet_office_cmd_odds.get(bet_cmd)
                        bet_cmd_china = bet_cmd
                        if len(bet_cmd_china.strip()) < 2:
                            bet_cmd_china = bet_cmd_china.ljust(5, ' ')

                        if index == len(pattern_list) - 1:
                            content = f"{bet_cmd_china} {bet_money} ({bet_office_lattery_odds})"
                        else:
                            content = f"{bet_cmd_china} {bet_money} ({bet_office_lattery_odds})\n"
                        bet_num_list.append(content)
                        bet_times += 1
                        user_money_after_reduce_bet_money -= bet_money
                        bet_total_money += bet_money
                        faBetting = FaBetting(tg_chat_id=chat_id, uid=user_result.id, tg_uid=member_id, bet_cmd=bet_cmd, bet_money=bet_money, bet_text=text, bet_issue=issue_result.issue_num, lottery_odds=bet_office_lattery_odds, created_at=current_timestamp)
                        session.add(faBetting)
                if break_all:
                    break

            if break_all is False:
                # 扣用户余额
                user_result.money -= bet_total_money
                suc_bet_num_str = ''.join([*bet_num_list])
                await bet_suc_send_msg(update, user_result.money, issue_result.issue_num, suc_bet_num_str)
                session.commit()
    except Exception as e:
        await log_except(e, True)


async def compliance_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_chat_title = update.message.chat.title
    tg_chat_id = update.message.chat.id
    tg_uid = update.effective_user.id
    tg_first_name = update.effective_user.first_name
    tg_username = update.effective_user.username

    # member_name = update.effective_user.mention_html()
    # member_username = update.effective_user.full_name

    printlog('过来了.....', update.effective_chat.id)

    try:
        await check_user_whether(tg_chat_id, tg_chat_title, tg_uid, tg_first_name, tg_username, cause_id=0, cause_first_name='', cause_username='')
        text = update.message.text.strip().replace(' ', '')
        if text is None or text == '':
            await bet_rule_notice(update, context, notice_text=f'投注失败! 投注内容不正确, 请看群公告!', chat_id=tg_chat_id)
        else:
            pattern_list = check_message(text)
            printlog(f"\n\nmember_id:{tg_first_name}\nmember_name:{tg_first_name}\npattern_list: {pattern_list}\n\n")
            if pattern_list:
                await is_pattern_message(pattern_list, update, context)
            else:
                if text == '历史':
                    history_list = await get_history_issue_only_leopard(limit=20)
                    await update.message.reply_html(text=''.join(history_list))
                elif text == '反水':
                    bet_flow_rebate_msg = await get_bet_flow_rebate(tg_uid, tg_chat_id)
                    await update.message.reply_html(text=''.join(bet_flow_rebate_msg))
                else:
                    await update.message.delete()
                    with get_session() as session:
                        current_timestamp = int(datetime.datetime.now(china_timezone).timestamp())
                        wait_add = FaViolation(tg_uid=tg_uid, tg_chat_id=tg_chat_id, msg_text=text, created_at=current_timestamp)
                        session.add(wait_add)
                        session.commit()
    except Exception as e:
        await log_except(e, True)


async def is_pattern_message(pattern_list, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(pattern_list) == 1:
        first_item = pattern_list[0]
        dict_to_tuple = list(first_item.items())
        tuple_result = dict_to_tuple[0]
        if tuple_result[0] == '历史':
            notice_text = ''
            limit_max = get_value_by_key('history_limit_max', 'config.yaml')
            if tuple_result[1] < limit_max:
                limit_max = tuple_result[1]
            history_list = await get_history_issue_only_leopard(limit=limit_max)
            await update.message.reply_html(text=''.join([notice_text, *history_list]))
        else:
            await conform_to_cmd(update, context, pattern_list)
    else:
        await conform_to_cmd(update, context, pattern_list)


# 投注指令 或 金额不在区间   专用方法
async def bet_rule_notice(update: Update, context: ContextTypes.DEFAULT_TYPE, notice_text: str, chat_id: int) -> None:
    notice_message = await update.message.reply_html(f"{notice_text}")
    context.job_queue.run_once(callback=bet_rule_job, when=3, chat_id=chat_id, data=(update.message, notice_message))


# 投注指令 或 金额不在区间   专用任务
async def bet_rule_job(context: CallbackContext) -> None:
    try:
        user_message, notice_message = context.job.data
        await user_message.delete()
        await notice_message.delete()
    except Exception as e:
        await log_except(e, True)


async def bet_suc_send_msg(update, after_money, issue_num, suc_bet_num_str) -> None:
    user = update.effective_user

    # 将 InlineKeyboardMarkup 对象添加到消息中
    reply_markup = InlineKeyboardMarkup(keyboard)

    username = str_replace(user.full_name).replace(' ', '')

    notice_suc_uid = f"Id: {user.id}\n"
    notice_suc_username = f"昵称: {username}\n"
    notice_suc_issue_num = f"期号: {issue_num}\n"
    notice_suc_one = f"下注: \n"
    notice_suc_bet_num_str = f"{generate_symbol('-', 20)}\n{suc_bet_num_str}\n{generate_symbol('-', 20)}\n"
    notice_suc_balance = f"当前余额: {after_money}"

    all_notice = ''.join([notice_suc_uid, notice_suc_username, notice_suc_issue_num, notice_suc_one, notice_suc_bet_num_str, notice_suc_balance])

    # 投注成功后发消息
    await update.message.reply_html(
        # f"你好,{user.mention_html()} {chat_type}!",
        f"{all_notice}",
        # reply_markup=ForceReply(selective=False),
        reply_markup=reply_markup
    )


async def handler_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    # chat_id = "ttt"
    with get_session() as session:
        try:
            chat_id = context.bot_data["tg_chat_id"]

            tg_uid = update.effective_user.id
            tg_chat_id = update.message.chat_id
            if update.message.chat_id == chat_id:
                printlog(f"""-----------收到请求信息=======
                内容: {update.message.text}
                tg_uid: {tg_uid}
                chat_id: {chat_id}
                effective_chat: {update.effective_chat}
                update.message.chat_id: {update.message.chat_id}
                """)
                wait_statement = select(FaUser).options(load_only('id', 'tg_uid', 'tg_chat_id')).where(FaUser.tg_uid == tg_uid, FaUser.tg_chat_id == tg_chat_id).limit(1)
                user_result = session.exec(wait_statement).first()
                if user_result and user_result.status == 'disabled':
                    notice_msg = await update.message.reply_text(f"您已被禁言!")
                    context.job_queue.run_once(delete_message, when=datetime.timedelta(seconds=3), data=(update.message, notice_msg))
                else:
                    chat_type = update.message.chat.type
                    if chat_type == 'private':
                        await update.message.reply_text(f'pc!')
                    elif chat_type in ['group', 'supergroup']:
                        message_text = update.message.text
                        filter_result = await filter_emoji(message_text)
                        if filter_result is False:
                            await compliance_process(update, context)
                        else:
                            await offense_process(update, context)
            else:
                printlog(f"-----------收到请求信息【不是指定群,不开放】======= \n内容: {update.message.text}\nchat_id: {chat_id}\nupdate.message.chat_id: {update.message.chat_id}")
                await update.message.reply_text(f"你好, 暂时未开放!")
        except Exception as e:
            await log_except(e, True)


# 投注
async def det() -> None:
    pass


# 上分
async def recharge_list() -> None:
    pass


# 查记录
async def touzhu_list() -> None:
    pass


# 查余额
async def find_balace() -> None:
    pass


# 禁言
async def group_ban() -> None:
    pass
    # chat_id = -1001833046994
    # await update.effective_chat.set_title(title="技术交流群abc花木成畦手自栽花木成畦手自栽")
    # await update.effective_chat.set_description(description="这是机器人更改的群描述sadfasdttttt")
    # await update.effective_chat.set_administrator_custom_title(user_id=user.id, custom_title="测试头衔")
    # permissions = ChatPermissions(can_send_messages=False)
    # await context.bot.setChatPermissions(chat_id=update.effective_chat.id, permissions=permissions)

    # permissions = ChatPermissions(can_send_messages=False)
    # try:
    #     # 设置禁言持续时间
    #     mute_duration = datetime.timedelta(minutes=1)  # 禁言 1 分钟
    #     until_date = datetime.datetime.now() + mute_duration
    #     # await update.effective_chat.restrict_member(user_id=user.id, permissions=permissions)
    #     await context.bot.set_chat_permissions(chat_id=chat_id, permissions=permissions)
    # except Exception as e:
    #     print(e)
    # print("its a test")


async def animation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # 获取用户点击的消息
    query = update.callback_query

    # 判断消息是否为 GIF 图片
    if query.message.animation:
        # 发送tip消息
        await context.bot.send_message(chat_id=query.message.chat_id, text='tip消息')


async def gif_handler(update: Update, context: CallbackContext) -> None:
    message = update.message
    if message.document.mime_type == 'video/mp4':
        await update.message.reply_text('Thanks for the GIF!')  # Send a notice message
    else:
        await update.message.reply_text('Please send me a GIF only.')  # Send an error message


# # 处理群组消息
async def handler_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # 获取消息的聊天ID、消息ID和消息内容
    # logger_instance().info(update.chat_member.difference())
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    message_text = update.message.text
    message_thread_id = update.message.message_thread_id
    # 对消息进行处理，例如将其转换为大写
    processed_message = message_text
    # 回复消息
    await context.bot.send_message(chat_id=chat_id, reply_to_message_id=message_id, message_thread_id=message_thread_id, text=processed_message)
