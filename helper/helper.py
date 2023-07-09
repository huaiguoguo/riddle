from datetime import datetime
from utils import china_timezone, get_config_value_by_key


def printlog(text: str, space_num: int = 1) -> None:
    is_open_log = get_config_value_by_key('is_open_log')
    if is_open_log:
        space_str = '\n' * space_num
        log_str = f'{text}, 当前时间是: {datetime.now(china_timezone)}{space_str}'
        print(log_str)
        # setup_logger().warn(log_str)
