import sys
import logging
import traceback
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler

from helper.helper import printlog
from utils import china_timezone, write_text, generate_symbol


# Enable logging
# logging.basicConfig(
#     filemode='a',
#     # filename='static/log/runs/runing.log',
#     encoding='utf-8',
# )


def setup_logger(log_file='static/log/runs/runtime.log', name=__name__, level=logging.WARN, log_type=1, filemodel='a', encoding='utf-8', max_bytes=2 * 1024 * 1024, backup_count=5):
    # 创建日志记录器
    logging.basicConfig(
        filemode=filemodel,
        encoding=encoding,
        level=level
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 检查是否已经存在相同类型的handler
    printlog(f"len(logger.handlers): {len(logger.handlers)}")
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler) and log_type == 1:
            return logger
        if isinstance(handler, TimedRotatingFileHandler) and log_type == 2:
            return logger

    # 创建文件处理器
    # file_handler = logging.FileHandler(log_file, delay=True)
    # file_handler.setLevel(level)

    if log_type == 1:
        handler = RotatingFileHandler(log_file, mode=filemodel, encoding=encoding, maxBytes=max_bytes, backupCount=backup_count)
    else:
        handler = TimedRotatingFileHandler(log_file, when='midnight', interval=1, backupCount=7)

    # 创建格式化器
    start_str = f'{generate_symbol()}【机器人日志】--开始{generate_symbol()}'
    end_str = f'{generate_symbol()}【机器人日志】--结束{generate_symbol()}'
    formatter_str = f'{start_str} \n时间:%(asctime)s \n进程号:[%(process)d] \n日志类型:[%(name)s] \n日志级别:[%(levelname)s] \n文件名:%(filename)s \n函数名:%(funcName)s \n行号:%(lineno)s \n日志内容:%(rawsql)s {end_str}\n\n'

    formatter = logging.Formatter(formatter_str)
    handler.setFormatter(formatter)
    handler.setLevel(level)

    # 添加处理器到日志记录器
    logger.addHandler(handler)

    return logger


# 暂时弃用
def logger_instance(logger_name: str = 'GameBt'):
    loggerInstance = logging.getLogger(logger_name)
    return loggerInstance


def generate_except_log_message(e, is_print: bool = False) -> str:
    current_datetime = datetime.now(china_timezone)
    # current_timestamp = int(current_datetime.timestamp())

    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback_details = traceback.extract_tb(exc_traceback)
    filename = traceback_details[-1].filename
    line_number = traceback_details[-1].lineno

    except_start_str = f"{generate_symbol()}异常记录开始{generate_symbol()}"
    except_end_str = f"{generate_symbol()}异常记录结束{generate_symbol()}"

    except_message = f"{except_start_str}\n异常时间:{current_datetime}\n{exc_type}\n异常类型: {exc_type}\n异常内容: {e}\n发生异常的文件名: {filename}\n发生异常的行数: {line_number}\n{except_end_str}\n\n"

    if is_print is True:
        printlog(f"异常类型: {exc_type}")
        printlog(f"异常内容: {e}")
        printlog(f"发生异常的文件名: {filename}")
        printlog(f"发生异常的行数: {line_number}")

    return except_message


async def log_except(e, isprint=False) -> None:
    except_message = generate_except_log_message(e, isprint)

    # 记录到run.log
    # setup_logger('runtime.log').debug(except_message)

    # 记录到except.log
    await write_text(except_message, 'except.log')
