import datetime
import random
import string

from utils import str_replace, china_timezone


def generate_random_email() -> str:
    domains = ['foxmail.com', 'qq.com', 'vip.qq.com', '126.com', '189.com', '139.com', 'yeah.com', 'sohu.com', 'tom.com', 'sina.com', '163.com', 'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
    random_domain = random.choice(domains)

    username_length = random.randint(6, 12)
    username = ''.join(random.choices(string.ascii_letters + string.digits, k=username_length))

    email = f"{username}@{random_domain}"
    return email


def generate_lottery_person_list_str(betting, index, count, betting_person_str):
    bet_cmd_china = betting.bet_cmd
    username = str_replace(betting.ofuser.username.replace(" ", ''))
    lottery_money = betting.lottery_odds * betting.bet_money
    if len(bet_cmd_china) < 2:
        bet_cmd_china = bet_cmd_china.ljust(5)

    if index == count - 1:
        betting_person_str.append(f"{username} {bet_cmd_china}+{lottery_money:.2f}")
    else:
        betting_person_str.append(f"{username} {bet_cmd_china}+{lottery_money:.2f}\n")


def assembly_open_bet_wait_update_data(betting_result, cmd_list, betting_person_str, fa_betting_wait_update_data, fa_user_wait_recrease_data, fa_redeem_wait_insert_data):
    is_clear: bool = False
    count = len(betting_result)
    current_timestamp = int(datetime.datetime.now(china_timezone).timestamp())
    for index, betting in enumerate(betting_result):
        if betting.bet_cmd in cmd_list:
            lottery_money = betting.lottery_odds * betting.bet_money
            # 组装中奖人列表数据
            if not is_clear:
                is_clear = True
                betting_person_str.clear()
            generate_lottery_person_list_str(betting, index, count, betting_person_str)
            # 组装更新投注记录状态数据
            fa_betting_wait_update_data.append({'id': betting.id, 'uid': betting.uid, 'is_lottery': 1, 'is_redeem': 1})
            # 组装赔付记录数据
            fa_redeem_wait_insert_data.append({"uid": betting.uid, "bet_id": betting.id, "bet_issue": betting.bet_issue, "lottery_odds": betting.lottery_odds, "total_money": lottery_money, "created_at": current_timestamp})
            # 组装更新用户余额数据
            found = False
            for wait_data_item in fa_user_wait_recrease_data:
                if wait_data_item['id'] == betting.uid:
                    wait_data_item['money'] += lottery_money
                    found = True
                    break
            if not found:
                fa_user_wait_recrease_data.append({"id": betting.uid, "money": betting.ofuser.money + lottery_money})
        else:
            # 组装更新投注记录状态数据
            fa_betting_wait_update_data.append({'id': betting.id, 'uid': betting.uid, 'is_lottery': 2})
