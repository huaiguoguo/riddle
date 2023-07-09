from dotenv import load_dotenv

from telegram import BotCommand
from telegram.ext import CommandHandler, Application, MessageHandler, ChatMemberHandler, CallbackQueryHandler, filters

from helper.helper import printlog
from utils import get_proxy, get_value_by_key
from bot.version_inspect import version_info_runtime_inspect

from .handler.callback_query_handler import handler_button
from .handler.chat_member_handler import greet_chat_members
from .handler.command_handler import handler_start, handler_menu, handler_chat, handler_dice
from .handler.message_handler import handler_text_message
from .job import repeat_job

version_info_runtime_inspect()
load_dotenv()

bot_application = (
    Application.builder().token(get_value_by_key('TELEGRAM_BOT_TOKEN')).connect_timeout(30).read_timeout(30).get_updates_read_timeout(42)
    .write_timeout(30)
    # .get_updates_write_timeout(30).pool_timeout(30).get_updates_pool_timeout(30).get_updates_connect_timeout(30)
    .proxy_url(get_proxy()).get_updates_proxy_url(get_proxy())
    # .updater(None)
    # .context_types(ContextTypes(context=CustomContext))
    .build()
)


async def set_bot_data() -> None:
    # 设置全局的机器人变量
    chat_id = get_value_by_key('TELEGRAM_CHAT_ID')
    webhook_host = get_value_by_key('TELEGRAM_WEBHOOK_HOST')
    webhook_bot_endpoint = get_value_by_key('TELEGRAM_WEBHOOK_BOT_ENDPOINT')

    bot_application.bot_data["tg_chat_id"] = chat_id
    bot_application.bot_data["tg_webhook_host"] = webhook_host
    bot_application.bot_data["tg_webhook_bot_endpoint"] = webhook_bot_endpoint
    bot_application.bot_data["tg_webhook_bot_url"] = f"{webhook_host}/{webhook_bot_endpoint}"


async def redister_handler() -> Application:
    # print(f"1------appid: {bot_application}")
    bot_application.handlers.clear()
    # bot_application.add_handler(CommandHandler("start", handler_start))
    bot_application.add_handler(CommandHandler("menu", handler_menu))
    # bot_application.add_handler(CommandHandler('ct', handler_chat))
    # bot_application.add_handler(CommandHandler('dc', handler_dice))
    bot_application.add_handler(MessageHandler(filters.TEXT, handler_text_message))
    # bot_instance.add_handler(MessageHandler(filters.ChatType.GROUPS, handler_group_message))
    bot_application.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))
    # bot_instance.add_handler(MessageHandler(filters.Message.animation, animation_callback))
    bot_application.add_handler(CallbackQueryHandler(handler_button))
    # bot_instance.add_handler(TypeHandler(type=WebhookUpdate, callback=handler_webhook_update))
    return bot_application


async def set_my_command() -> Application:
    # 设置bot命令
    commands = [
        # BotCommand("start", "开始"),
        # BotCommand("dc", "摇一摇"),
        # BotCommand("ct", "ai聊天"),
        BotCommand("menu", "菜单"),
    ]
    await bot_application.bot.set_my_commands(commands)
    return bot_application


async def run_job() -> None:
    await repeat_job(bot_application)


# init
async def initialization() -> Application:
    await set_bot_data()
    await redister_handler()
    await set_my_command()
    await run_job()
    # print(f"tg_webhook_bot_url: {bot_application.bot_data['tg_webhook_bot_url']}")
    set_result = await bot_application.bot.set_webhook(url=bot_application.bot_data['tg_webhook_bot_url'])
    printlog(f'=+=====webhook设置结果=============={set_result}')
    return bot_application


def runbot_without_webframework() -> None:
    # job = Queue()
    # updater = Updater(bot_instance_after_register_handler.bot, job)
    # bot_instance_after_register_handler.updater = updater
    # allowed_updates = ['message', 'edited_message', 'channel_post', 'edited_channel_post', 'inline_query', 'chosen_inline_result', 'callback_query', 'shipping_query', 'pre_checkout_query', 'poll', 'poll_answer', 'my_chat_member', 'chat_member']
    # bot_instance_after_register_handler.run_webhook(
    #     listen="127.0.0.1",
    #     port=9001,
    #     url_path=f"/gamebot",
    #     # secret_token='ASecretTokenIHaveChangedByNow',
    #     allowed_updates=allowed_updates,
    #     cert='cert/chatplay_masoner_cn.pem',
    #     # key='cert/chatplay_masoner_cn.key',
    #     webhook_url=f"{bot_instance_after_register_handler.bot_data['tg_webhook_server_url']}"
    # )
    # bot_instance_after_register_handler.bot.set_webhook(url=bot_instance_after_register_handler.bot_data['tg_webhook_bot_url'])
    pass
