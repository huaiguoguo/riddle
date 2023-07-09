import datetime

import telegram
from sqlalchemy.orm import load_only
from sqlmodel import select
from telegram import Update
from telegram.ext import ContextTypes

from logger import log_except
from orm import FaUser, get_session
from orm.models import FaBetting
from sqlmodel import func

from utils import china_timezone, get_value_by_key, generate_symbol


async def handler_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # 获取用户点击的按钮
    try:
        query = update.callback_query
        # msg = update.message
        button_pressed = query.data
        member_id = update.effective_user.id

        message = '没任何点击'

        if button_pressed == 'balance':
            message = await get_balance(member_id, context)
        elif button_pressed == 'history_bet':
            message = await get_history_bet(member_id, context)
        elif button_pressed == 'daily_win_lose':
            message = await get_daily_win_lose(member_id, context)

        # 弹窗显示信息
        await query.answer(text=f'{message}', show_alert=True)
    except telegram.error.BadRequest as e:
        await log_except(e, True)
    except Exception as e:
        await log_except(e, True)
    # await context.bot.send_dice(chat_id=msg.chat_id, emoji=telegram.constants.DiceEmoji.DICE)
    # await update.message.chat.send_dice(emoji=telegram.constants.DiceEmoji.DICE)

    # await query.edit_message_text(text="This is a popup message.")
    # await query.answer()
    # await query.edit_message_text(text=f'Received callback data: {query.data}')

    # 创建一个带有“确定”按钮的内联键盘
    # keyboard = [[InlineKeyboardButton("确定", callback_data='close')]]
    # reply_markup = InlineKeyboardMarkup(keyboard)
    # 向用户发送带有键盘的消息
    # await context.bot.send_message(text='test', reply_markup=reply_markup)

    # await context.bot.answer_callback_query(callback_query_id=query.id, text="Here is your message！！！.")
    # await context.bot.send_message(chat_id=query.message.chat_id, text="Here is your message.")


async def get_balance(tg_uid, context: ContextTypes.DEFAULT_TYPE) -> str:
    with get_session() as session:
        try:
            # 查询用户余额是够本次投注
            faUser_wait_statement = select(FaUser).options(load_only('id', 'username', 'money')).where(FaUser.tg_uid == tg_uid, FaUser.tg_chat_id == context.bot_data['tg_chat_id'])
            user_result = session.exec(faUser_wait_statement).one()
            total_bet_money = session.query(func.sum(FaBetting.bet_money)).where(FaBetting.tg_uid == tg_uid).scalar()
            message = f'id:{tg_uid}\n昵称:{user_result.username}\n余额:{user_result.money}\n总下注流水:{total_bet_money}'
            return message
        except Exception as e:
            await log_except(e, True)


async def get_history_bet(member_id, context: ContextTypes.DEFAULT_TYPE) -> str:
    message_list = []
    message_table_column_title = f"{generate_symbol(' ', 6)}期号{generate_symbol(' ', 14)}下注{generate_symbol(' ', 10)}金额\n"
    with get_session() as session:
        try:
            user_wait_statement = select(FaUser).options(load_only('id', 'tg_uid', 'tg_chat_id')).where(FaUser.tg_uid == member_id, FaUser.tg_chat_id == context.bot_data['tg_chat_id']).limit(1)
            user_result = session.exec(user_wait_statement).one()

            history_bet_limit_max = get_value_by_key('history_bet_limit_max', 'config.yaml')
            fabetting_wait_statement = select(FaBetting).options(load_only('id', 'uid', 'bet_issue', 'bet_cmd', 'bet_money', 'tg_uid', 'tg_chat_id')).where(FaBetting.uid == user_result.id, FaBetting.tg_uid == member_id, FaBetting.tg_chat_id == context.bot_data['tg_chat_id'])
            fabetting_result = session.exec(fabetting_wait_statement.limit(history_bet_limit_max)).all()
            # print(f"fabetting_result==========: {len(fabetting_result)}")
            if fabetting_result:
                for betting in fabetting_result:
                    message_list.append(f"{betting.bet_issue}{generate_symbol(' ', 8)}{betting.bet_cmd}{generate_symbol(' ', 11)}{betting.bet_money}\n")
            else:
                message_list.append(f"{generate_symbol(' ', 10)}无{generate_symbol(' ', 10)}")

            message = ''.join([message_table_column_title, *message_list])
            # print(f"message : {message}")
            return message
        except Exception as e:
            await log_except(e, True)


async def get_daily_win_lose(tg_uid, context: ContextTypes.DEFAULT_TYPE) -> str:
    with get_session() as session:
        try:
            faUser_wait_statement = select(FaUser).options(load_only('id', 'money')).where(FaUser.tg_uid == tg_uid, FaUser.tg_chat_id == context.bot_data['tg_chat_id'])
            user_result = session.exec(faUser_wait_statement).one()

            today = datetime.datetime.now(china_timezone).date()

            start_of_day = datetime.datetime.combine(today, datetime.time.min)  # 设置时间为0时0分0秒
            end_of_day = datetime.datetime.combine(today, datetime.time.max)  # 设置时间为23时59分59秒

            start_timestamp = str(start_of_day.timestamp())  # 转换为时间戳
            end_timestamp = str(end_of_day.timestamp())  # 转换为时间戳

            # print(f"today:{today}")
            # print(f"today:{func.DATE(datetime.datetime.fromtimestamp(float('1685612974')))}")
            fabetting_wait_statement_win = select(func.count()).where(FaBetting.is_lottery == 1, FaBetting.uid == user_result.id, FaBetting.tg_uid == tg_uid).where(FaBetting.created_at >= start_timestamp).where(FaBetting.created_at <= end_timestamp)
            fabetting_result_win = session.exec(fabetting_wait_statement_win).one()

            fabetting_wait_statement_lose = select(func.count()).where(FaBetting.is_lottery == 2, FaBetting.uid == user_result.id, FaBetting.tg_uid == tg_uid).where(FaBetting.created_at >= start_timestamp).where(FaBetting.created_at <= end_timestamp)
            # print(f"fabetting_wait_statement: {fabetting_wait_statement_lose}")
            fabetting_result_lose = session.exec(fabetting_wait_statement_lose).one()
            message = f'输{fabetting_result_lose}-赢{fabetting_result_win}\n余额:{user_result.money}'
        except Exception as e:
            await log_except(e, True)

    return message
