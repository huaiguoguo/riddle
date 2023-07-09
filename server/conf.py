log_config = {
    "version": 1,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "custom_format"
        },
        # "access": {
        #     "formatter": "access",
        #     "class": "logging.StreamHandler",
        # },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["console"],
            "level": "WARNING"
        },
        # "uvicorn.error": {"level": "INFO"},
        # "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "format": "%(levelprefix)s %(message)s",
            "use_colors": True,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "format": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',  # noqa: E501
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": True,
        },
        "custom_format": {
            # "()": "uvicorn.logging.AccessFormatter",
            "format": "+++++++++++++++>>>>【服务器日志】<<<<开始+++++++++++++++\n时间:%(asctime)s \n进程号:[%(process)d] \n日志类型:[%(name)s] \n日志级别:[%(levelname)s] \n日志内容:%(message)s \n文件名:%(filename)s \n函数名:%(funcName)s \n行号:%(lineno)s \n +++++++++++++++>>>>【服务器日志】<<<<结束+++++++++++++++\n\n",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": True,
        }
    }
}
