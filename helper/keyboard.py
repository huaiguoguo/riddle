from telegram import InlineKeyboardButton

from utils import get_value_by_key

keyboard = [
    [
        InlineKeyboardButton("上分下分", url=get_value_by_key('up_down_score', 'config.yaml')),
        InlineKeyboardButton("查看余额", callback_data='balance'),
    ],
    [
        InlineKeyboardButton("历史投注", callback_data='history_bet'),
        InlineKeyboardButton("今日输赢", callback_data='daily_win_lose'),
    ],
    # [
    # InlineKeyboardButton("联系客服", callback_data='contact'),
    # InlineKeyboardButton("上分下分", callback_data='recharge', switch_inline_query='https://t.me/jichang_user'),
    # ]
]