from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import load_only
from sqlmodel import select
from telegram import ChatMember, ChatMemberUpdated, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from helper.helper import printlog
from utils import china_timezone
from logger import logger_instance, log_except
from orm.models import FaUser
from orm import get_session, check_user_whether


# 解包状态
async def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    try:
        status_change = chat_member_update.difference().get("status")
        old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))
        if status_change is None:
            return None

        old_status, new_status = status_change
        was_member = old_status in [
            ChatMember.MEMBER,
            ChatMember.OWNER,
            ChatMember.ADMINISTRATOR,
        ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
        is_member = new_status in [
            ChatMember.MEMBER,
            ChatMember.OWNER,
            ChatMember.ADMINISTRATOR,
        ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

        return was_member, is_member
    except Exception as e:
        await log_except(e, True)


async def leave_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # chat_invite_link = update.message.chat.invite_link
    # message = f"{member_name} is no longer with us. Thanks a lot, {cause_name} ..."
    # message = f"{member_name} 已离开群组! ..."
    # await update.effective_chat.send_message(
    #     message,
    #     parse_mode=ParseMode.HTML,
    # )
    with get_session() as session:
        try:
            tg_uid = update.effective_user.id
            tg_chat_id = update.chat_member.chat.id
            wait_statement = select(FaUser).options(load_only('id', 'tg_uid', 'tg_chat_id')).where(FaUser.tg_uid == tg_uid, FaUser.tg_chat_id == tg_chat_id).limit(1)
            user_result = session.exec(wait_statement).first()
            printlog(f"""
                到达退群处理函数!
                username: {update.effective_user.username}
                first_name: {update.effective_user.first_name}
            """)
            if user_result:
                current_timestamp = int(datetime.now(china_timezone).timestamp())
                user_result.leave_group_status = 'leave'
                user_result.leave_group_time = current_timestamp
                session.commit()
        except Exception as e:
            await log_except(e, True)


async def join_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await insert_data(update)
    # message = f"{cause_name} 邀请 {member_name} 加入. 欢迎!"
    # if member_id == cause_id:
    #     message = f"{member_name}, 欢迎加入!"
    # await update.effective_chat.send_message(
    #     message,
    #     parse_mode=ParseMode.HTML,
    # )
    pass


# 给新进的用户打招呼
async def greet_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greets new users in chats and announces when someone leaves"""
    # logger_instance().info(" 消转终于转发过来了, 我操, 也不知道昨天动着哪个地方的代码了, 让我调试了一天.... ====================================+++///")
    # print(f"/////////////////////////{update.chat_member}")

    result = await extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result

    # member_id = update.chat_member.new_chat_member.user.id
    # member_name = update.chat_member.new_chat_member.user.mention_html()
    # cause_id = update.chat_member.from_user.id
    # cause_name = update.chat_member.from_user.mention_html()

    if not was_member and is_member:
        await join_process(update, context)
    elif was_member and not is_member:
        await leave_process(update, context)


async def insert_data(update: Update) -> None:
    tg_chat_id = update.chat_member.chat.id
    tg_chat_title = update.chat_member.chat.title

    # print(f"update.chat_member===================： {update.chat_member}")
    # printlog(f"update.chat_member.new_chat_member===================： {update.chat_member.new_chat_member}")
    # printlog(f"update.chat_member.new_chat_member.user.first_name===================： {update.chat_member.new_chat_member.user.first_name}")
    # printlog(f"update.chat_member.new_chat_member.user.username===================： {update.chat_member.new_chat_member.user.username}")

    tg_uid = update.effective_user.id
    # member_name = update.effective_user.mention_html()
    tg_first_name = update.chat_member.new_chat_member.user.first_name
    tg_username = update.chat_member.new_chat_member.user.username

    # member_photo = await update.effective_user.get_profile_photos()
    # print(f'member_photo:{member_photo}')
    # member_id = update.chat_member.new_chat_member.user.id
    # member_name = update.chat_member.new_chat_member.user.mention_html()

    # print(f'chat_id:{chat_id}')

    # invite_link = update.chat_member.invite_link.invite_link
    # is_revoked = update.chat_member.invite_link.is_revoked

    cause_id = update.chat_member.from_user.id
    cause_first_name = update.chat_member.from_user.first_name
    cause_username = update.chat_member.from_user.username
    # current_timestamp = int(datetime.now(china_timezone).timestamp())

    try:
        # await check_user_whether(chat_id, member_id, member_name, member_username, cause_id, cause_first_name, cause_username)
        await check_user_whether(tg_chat_id, tg_chat_title, tg_uid, tg_first_name, tg_username, cause_id, cause_first_name, cause_username)
    except Exception as e:
        await log_except(e, True)
