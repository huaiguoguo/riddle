import html

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes, CallbackContext

from helper.keyboard import keyboard
from lib import CustomContext
from logger import log_except
from utils import resquest_chatgpt, write_text, get_value_by_key


async def handler_start(update: Update, context: CustomContext) -> None:
    """Display a message with instructions on how to use this bot."""
    # url = context.bot_data["url"]
    url = 'https://xxx.com'
    payload_url = html.escape(f"{url}/submitpayload?user_id=<your user id>&payload=<payload>")
    text = (
        # f"To check if the bot is still running, call <code>{url}/healthcheck</code>.\n\n"
        # f"To post a custom update, call <code>{payload_url}</code>."
        f"检测机器人是否正在运行, 请运行<code>{url}/healthcheck</code>.\n\n"
        f"发布自定义更新, 请运行 <code>{payload_url}</code>."
    )
    await update.message.reply_html(text=text)


async def handler_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # 创建一个 InlineKeyboardMarkup 对象，并设置三个 InlineKeyboardButton
    # 将 InlineKeyboardMarkup 对象添加到消息中
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('请选择一个按钮：', reply_markup=reply_markup)


async def handler_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message_text = update.message.text
    query = update.callback_query

    if message_text.startswith("/ct"):
        s_plit = message_text.split()
        question_text = " ".join(s_plit[1:]).strip()
        if not question_text:
            await update.message.reply_html(
                # rf"你好 {user.mention_html()}!",
                f"请输入您要提问的问题! 提问格式为: /ct 问题",
                # reply_markup=ForceReply(selective=False),
            )
        else:
            chat_res = await resquest_chatgpt(user.full_name, question_text)
            await write_text(f'Answer: {chat_res}')
            await update.message.reply_html(
                # rf"你好 {user.mention_html()}!",
                f"\n\n\n\n你好,{user.mention_html()}. \n\n{chat_res}",
                # reply_markup=ForceReply(selective=False),
            )


async def send_msg(context: CallbackContext) -> None:
    message = context.job.data
    try:
        await message.chat.send_message(f'摇得的点数为: {message.dice.value}')
    except Exception as e:
        await log_except(e, True)


async def handler_dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        message = await update.effective_chat.send_dice()
        context.job_queue.run_once(send_msg, 3.5, data=message)
    except Exception as e:
        await log_except(e, True)
