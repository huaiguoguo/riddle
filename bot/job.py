import datetime

from telegram.ext import Application

from helper.helper import printlog
from logger import log_except
from utils import china_timezone
from bot.handler.job_queue import start_issue


def start_job(bot_application) -> None:
    chat_id = bot_application.bot_data["tg_chat_id"]
    bot_application.job_queue.run_once(start_issue, when=datetime.timedelta(seconds=0), chat_id=chat_id)
    bot_application.job_queue.run_repeating(callback=start_issue, interval=datetime.timedelta(seconds=120), first=0, name='daily_task', chat_id=chat_id)


async def repeat_job(bot_application: Application) -> None:
    try:
        current_timestamp = datetime.datetime.now(china_timezone)
        printlog(f'首次运行时间: {current_timestamp}')

        start_job(bot_application)
    except Exception as e:
        await log_except(e, True)
