import logging

import uvicorn

from logger import setup_logger
from app import starlette_app
from utils import get_value_by_key
from .conf import log_config

from uvicorn.logging import AccessFormatter

webserver_host = get_value_by_key('BOT_WEBSERVER_HOST')
webserver_port = get_value_by_key('BOT_WEBSERVER_PORT')

# setup_logger()

server = uvicorn.Server(
    config=uvicorn.Config(
        app=starlette_app,
        host=webserver_host,
        port=int(webserver_port),
        log_config=log_config,
        access_log=True,
        use_colors=True,
        # log_level='info',
        reload=True,
        # root_path=''
        # reload_dirs='GameBt'
    )
)
