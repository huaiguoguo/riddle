from telegram.constants import ParseMode

from lib import WebhookUpdate, CustomContext
from logger import logger_instance


async def handler_webhook_update(update: WebhookUpdate, context: CustomContext) -> None:
    """Callback that handles the custom updates."""
    # logger_instance().info("这是   handler_webhook_update ++++++++++++++++++++++==+++///")
    chat_member = await context.bot.get_chat_member(chat_id=update.user_id, user_id=update.user_id)
    payloads = context.user_data.setdefault("payloads", [])
    payloads.append(update.payload)
    combined_payloads = "</code>\n• <code>".join(payloads)
    text = (
        f"The user {chat_member.user.mention_html()} has sent a new payload. "
        f"So far they have sent the following payloads: \n\n• <code>{combined_payloads}</code>"
    )
    await context.bot.send_message(
        chat_id=context.bot_data["admin_chat_id"], text=text, parse_mode=ParseMode.HTML
    )
