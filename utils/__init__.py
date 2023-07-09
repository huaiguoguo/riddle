import json
import os
import re
from datetime import datetime
from typing import List, Optional, Any
from zoneinfo import ZoneInfo

import openai
import unicodedata
import wcwidth

from config.config import get_config

china_timezone = ZoneInfo("Asia/Shanghai")


# bet_office_cmd = ['大', '小', '单', '双', '小单', '大单', '小双', '大双', '豹子']
# bet_office_cmd_odds = {'大': 1, '小': 1, '单': 1, '双': 1, '小单': 2, '大单': 2, '小双': 2, '大双': 2, '豹子': 6}

# bet_office_cmd = get_config().get('bet_office_cmd')
# bet_office_cmd_odds = get_config().get('bet_office_cmd_odds')


async def write_text(text, log_file_name='web_access.log', model='a'):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path_file_name = f"static/log/{log_file_name}"
    with open(path_file_name, model, encoding='utf-8') as f:
        if os.path.exists(path_file_name) and os.path.getsize(path_file_name) > 0:
            f.write('\n')
        f.write(f'[{now}]\n{text}')


def get_open_type(bet_cmd) -> List[str]:
    if all(item in bet_cmd for item in ['豹子']):
        return ['豹子']
    else:
        return bet_cmd


def get_display_width(string):
    return sum(wcwidth.wcswidth(char) for char in string)


def make_equal_width(wait_just_str: str, be_sum_str: str) -> str:
    display_width = get_display_width(be_sum_str)
    # print(f"be_sum_str: {be_sum_str}, display_width: {display_width}")
    # padding = ' ' * (width - display_width)
    # just_num = width - display_width
    return wait_just_str.ljust(display_width, ' ')


def make_equal_width_new(wait_just_str: str, be_sum_str: str) -> str:
    wait_display_width = get_display_width(wait_just_str)
    display_width = get_display_width(be_sum_str)
    print(f"be_sum_str: {be_sum_str}, display_width: {display_width} \n")
    padding = '  ' * (display_width - wait_display_width)
    return wait_just_str + padding


def str_replace(data) -> str:
    """ 把写错的中文符号都替换成英文 """
    chinaTab = ['：', '；', '，', '。', '！', '？', '【', '】', '“', '（', '）', '%', '#', '@', '&', "‘", ' ', '\n', '”']
    englishTab = [':', ';', ',', '.', '!', '?', '[', ']', '"', '(', ')', '%', '#', '@', '&', "'", ' ', '', '"']
    for index in range(len(chinaTab)):
        if chinaTab[index] in data:
            data = data.replace(chinaTab[index], englishTab[index])
    return data


def generate_symbol(symbol: str = '+', times: int = 30) -> str:
    return symbol * times


def is_emoji(char):
    # 检查字符是否为 emoji
    return 'emoji' in unicodedata.name(char, '').lower()


async def filter_emoji(message_text) -> bool:
    # 匹配 emoji 的正则表达式
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               "]+", flags=re.UNICODE)

    # 检查消息中的每个字符是否为 emoji
    result = False
    if emoji_pattern.search(message_text) or any(is_emoji(char) for char in message_text):
        result = True

    return result


async def resquest_chatgpt(user: str, prompt: str) -> str:
    CHATGPT_API_URL = os.environ.get("CHATGPT_API_URL")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_API_ORG = os.environ.get("OPENAI_API_ORG")

    # headers = {"Authorization": f"Bearer {CHATGPT_API_URL}"}
    data = {"inputs": prompt}

    # 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
    openai.organization = OPENAI_API_ORG
    openai.api_key = OPENAI_API_KEY
    # model_list = openai.Model.list()
    # print(model_list)

    # await write_text(f'ModelList: {str(model_list)}', 'model_list.json', 'w')

    await write_text(f'Question: {user} -> {prompt}')

    response = openai.Completion.create(
        # model="text-davinci-001",
        prompt=prompt,
        # temperature=0.9,
        # max_tokens=1024,
        # top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.9,
        stop=[" Human:", " AI:"],
        # suffix="",
        model="text-davinci-003",
        # model="babbage",
        max_tokens=2048,
        temperature=0.5
    )

    answer = response.choices[0].text.strip()
    # await write_text(f'Answer: {answer}')
    return answer


def get_value_by_key(key: str, filename: str = 'env.yaml'):
    env_config = get_config(filename)
    return env_config.get(key)


def get_config_value_by_key(key: str):
    return get_value_by_key(key, 'config.yaml')


def get_env_value_by_key(key: str):
    return get_value_by_key(key, 'env.yaml')


def get_proxy() -> str:
    proxy_protocol = get_value_by_key('BOT_PROXY_PROTOCOL')
    proxy_host = get_value_by_key('BOT_PROXY_HOST')
    proxy_port = get_value_by_key('BOT_PROXY_PORT')

    proxy_url = f"{proxy_protocol}://{proxy_host}:{proxy_port}"
    # print(f'================++++=====proxy_url: {proxy_url}')

    return proxy_url
