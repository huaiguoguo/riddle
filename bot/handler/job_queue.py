import datetime
import telegram
from sqlalchemy.orm import load_only
from telegram import ChatPermissions, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from sqlmodel import col, select

from helper.keyboard import keyboard
from logger import log_except
from orm.models import FaIssue
from orm import get_session, get_open_result_str
from orm import update_dice, generate_sealing_line, whether_not
from utils import china_timezone, get_value_by_key
from utils import generate_symbol
from helper.helper import printlog


async def lib_start_issue(context):
    issue_number = await whether_not()
    printlog(f'\n\n\n开始新一期, 其号:{issue_number} ')

    start_issue_msg = f"{generate_symbol('❗️', 3)}{issue_number}期{generate_symbol('❗️', 3)}"
    advert_value = get_value_by_key('start_issue_advert', 'config.yaml')

    up_down_score = get_value_by_key('up_down_score', 'config.yaml')
    customer_service = get_value_by_key('customer_service', 'config.yaml')

    advert_value = advert_value.replace("${up_down_score}", str(up_down_score)).replace("${customer_service}", customer_service)

    advert_value_str = f"""{advert_value}"""

    start_issue_msg = ''.join([start_issue_msg, advert_value_str])
    is_send = await context.bot.send_message(context.job.chat_id, start_issue_msg, reply_markup=InlineKeyboardMarkup(keyboard))
    printlog(f'新一期开盘提示消息 是否 发送成功: {type(is_send)}')

    mute_duration = datetime.timedelta(seconds=0)
    context.job_queue.run_once(operater_unban, when=mute_duration, chat_id=context.job.chat_id)


# 解禁
async def lib_operater_unban(context) -> None:
    chat_id = context.job.chat_id
    normal_permissions = ChatPermissions(can_send_messages=True)
    is_unban = await context.bot.set_chat_permissions(chat_id, normal_permissions)
    printlog(f'***** unban:{is_unban}   ')

    # 70秒后开始提示: 20秒后封盘
    mute_duration = datetime.timedelta(seconds=75)
    context.job_queue.run_once(notice_ban_after_second, when=mute_duration, chat_id=context.job.chat_id)


async def lib_notice_ban_after_second(context):
    chat_id = context.job.chat_id
    message = f"{generate_symbol('*', 3)}即将封盘(别卡点投注){generate_symbol('*', 3)}\n"
    open_open_bet_person = f"⏰{generate_symbol(' ', 5)}20秒后停止投注{generate_symbol(' ', 5)}⏰\n"

    bet_flow_rebate_ratio = get_value_by_key('bet_flow_rebate_ratio', 'config.yaml')
    notice_ban_after_second_advert = get_value_by_key('notice_ban_after_second_advert', 'config.yaml')
    notice_ban_after_second_advert = notice_ban_after_second_advert.replace("${bet_flow_rebate_ratio}", str(bet_flow_rebate_ratio))

    notice_ban_after_second_advert_str = f"""{notice_ban_after_second_advert}"""

    msg_text = ''.join([message, open_open_bet_person, notice_ban_after_second_advert_str])
    await context.bot.send_message(chat_id=chat_id, text=msg_text)

    mute_duration = datetime.timedelta(seconds=20)
    context.job_queue.run_once(operater_ban, when=mute_duration, chat_id=chat_id)


# 禁群
async def lib_operater_ban(context: CallbackContext) -> None:
    chat_id = context.job.chat_id
    mute_permissions = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
        can_change_info=False,
        can_invite_users=False,
        can_pin_messages=False,
    )
    is_ban = await context.bot.set_chat_permissions(chat_id, mute_permissions)
    printlog(f'***** ban:{is_ban}    ')

    mute_duration = datetime.timedelta(seconds=0)
    context.job_queue.run_once(send_line, when=mute_duration, chat_id=chat_id)


async def lib_send_line(context):
    chat_id = context.job.chat_id
    msg_text_arr = await generate_sealing_line()
    if not msg_text_arr:
        msg_text_arr = []
        message_line = f"{generate_symbol('*', 8)}封*盘*线{generate_symbol('*', 8)}\n🚫停止下注, 请核对账单\n🚫是否下注成功以账单为准\n"
        msg_text_arr.append(message_line)

    printlog(f'发送封盘线 ')
    await context.bot.send_message(chat_id=chat_id, text=''.join([*msg_text_arr]))

    mute_duration = datetime.timedelta(seconds=0)
    context.job_queue.run_once(send_dice_once, when=mute_duration, chat_id=chat_id)


async def lib_send_dice_once(context):
    printlog('发送第1个筛子开始')
    chat_id = context.job.chat_id
    dice_message_onec = await context.bot.send_dice(chat_id)
    printlog('发送第1个筛子结束')

    # 更新记录中的第1个结果和总和
    await update_dice(dice_message_onec.dice.value, 1)

    printlog('准备执行第2个筛子发送 [任务]')
    mute_duration = datetime.timedelta(seconds=0)
    context.job_queue.run_once(send_dice_twice, when=mute_duration, chat_id=chat_id)


async def lib_send_dice_twice(context):
    printlog('发送第2个筛子开始')
    chat_id = context.job.chat_id
    dice_message_twice = await context.bot.send_dice(chat_id)
    printlog('发送第2个筛子结束')

    # 更新记录中的第2个结果和总和
    await update_dice(dice_message_twice.dice.value, 2)

    printlog('准备执行第3个筛子发送 [任务]')
    mute_duration = datetime.timedelta(seconds=0)
    context.job_queue.run_once(send_dice_thirce, when=mute_duration, chat_id=chat_id)


async def lib_send_dice_thirce(context):
    chat_id = context.job.chat_id
    printlog('发送第3个筛子开始')
    dice_message_thirce = await context.bot.send_dice(chat_id)
    printlog('发送第3个筛子结束')

    # 更新记录中的第3个结果和总和
    await update_dice(dice_message_thirce.dice.value, 3)

    printlog('准备执行开奖 6秒后 [任务]')
    mute_duration = datetime.timedelta(seconds=5)
    # context.job_queue.run_once(send_open_bet, when=mute_duration, chat_id=chat_id, data=(dice_message_onec, dice_message_twice, dice_message_thirce))
    context.job_queue.run_once(send_open_bet, when=mute_duration, chat_id=chat_id)


# -----------------------------------------------------------------------任务开始----------------------------------------
# 开始新一期投注
async def start_issue(context):
    try:
        await lib_start_issue(context)
    except telegram.error.NetworkError as e:
        await log_except(e, True)
        printlog(f'start_issue()遇到<telegram.error.NetworkError>异常, 重试. ', 5)
        await lib_start_issue(context)
    except Exception as e:
        await log_except(e, True)


# 解禁群
async def operater_unban(context):
    try:
        await lib_operater_unban(context)
    except telegram.error.NetworkError as e:
        await log_except(e, True)
        printlog(f'operater_ban()遇到NetworkError异常, 重试. ')
        await lib_operater_unban(context)
    except Exception as e:
        await log_except(e, True)


# 提示准备封盘 发筛子
async def notice_ban_after_second(context: CallbackContext):
    printlog(f'提示20秒后 准备封盘 发筛子-----')
    try:
        await lib_notice_ban_after_second(context)
    except telegram.error.NetworkError as e:
        await log_except(e, True)
        printlog(f'notice_ban_after_second()遇到NetworkError异常, 重试!  ', 5)
        await lib_notice_ban_after_second(context)
    except Exception as e:
        await log_except(e, True)


# 禁群
async def operater_ban(context):
    try:
        await lib_operater_ban(context)
    except telegram.error.NetworkError as e:
        await log_except(e, True)
        printlog(f'operater_ban()遇到NetworkError异常, 重试. ')
        await lib_operater_ban(context)
    except Exception as e:
        await log_except(e, True)


# 发送封盘线 禁群
async def send_line(context):
    try:
        await lib_send_line(context)
    except telegram.error.NetworkError as e:
        await log_except(e, True)
        printlog(f'send_line()遇到NetworkError异常, 重试! ', 5)
        await lib_send_line(context)
    except Exception as e:
        await log_except(e, True)


# 发第1个筛子
async def send_dice_once(context):
    try:
        await lib_send_dice_once(context)
    except telegram.error.NetworkError as e:
        await log_except(e, True)
        printlog(f'send_dice_once()遇到NetworkError异常, 重试. ')
        await lib_send_dice_once(context)
    except Exception as e:
        await log_except(e, True)


# 发第2个筛子
async def send_dice_twice(context):
    try:
        await lib_send_dice_twice(context)
    except telegram.error.NetworkError as e:
        await log_except(e, True)
        printlog(f'send_dice_twice()遇到NetworkError异常, 重试. ')
        await lib_send_dice_twice(context)
    except Exception as e:
        await log_except(e, True)


# 发第3个筛子
async def send_dice_thirce(context):
    try:
        await lib_send_dice_thirce(context)
    except telegram.error.NetworkError as e:
        await log_except(e, True)
        printlog(f'_send_dice_thirce()遇到NetworkError异常, 重试. ')
        await lib_send_dice_thirce(context)
    except Exception as e:
        await log_except(e, True)


# 发送开奖结果, 历史开奖结果列表, 中奖人列表
async def send_open_bet(context) -> None:
    printlog(f'发送开奖结果-开始')
    chat_id = context.job.chat_id
    open_text = None

    with get_session() as session:
        try:
            current_timestamp = int(datetime.datetime.now(china_timezone).timestamp())
            load_only_tuple = load_only('id', 'is_lock', 'status', 'open_at', 'open_type', 'dice_total', 'issue_num', 'num_1', 'num_2', 'num_3')
            wait_statement = select(FaIssue).options(load_only_tuple).where(FaIssue.status == 1, FaIssue.is_lock == 1).order_by(col(FaIssue.id).desc()).limit(1)
            faIssue_result = session.exec(wait_statement).one()
            printlog(f'待开奖的当期记录: {faIssue_result}')
            faIssue_result.status = 2
            faIssue_result.is_lock = 2
            faIssue_result.open_at = current_timestamp

            cmd_list = faIssue_result.open_type.strip().split(' ')
            open_text = await get_open_result_str(faIssue_result.issue_num, faIssue_result.num_1, faIssue_result.num_2, faIssue_result.num_3, ', '.join(cmd_list), faIssue_result.dice_total, cmd_list, session)
            send_open_bet_msg = await context.bot.send_message(chat_id=chat_id, text=open_text, parse_mode="HTML")
            printlog(f"发消开奖消息的结果是: {type(send_open_bet_msg)}")
            session.commit()
        except telegram.error.NetworkError as e:
            printlog(f'异常start----send_open_bet()遇到NetworkError异常, 重试发送开奖结果! \n发送开奖结果-结束, 等待新的一期开始', 3)
            await log_except(e, True)
            send_open_bet_msg = await context.bot.send_message(chat_id=chat_id, text=open_text, parse_mode="HTML")
            printlog(f"异常end----发消开奖消息的结果是: {type(send_open_bet_msg)}")
        except Exception as e:
            printlog(f"Exception异常-------")
            await log_except(e, True)

    printlog(f'发送开奖结果-结束, 等待新的一期开始', 3)
