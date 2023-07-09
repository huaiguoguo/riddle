from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.exceptions import ExceptionMiddleware

from exception import handle_404, not_found, server_error
from routes import route_list

exception_handlers = {
    404: not_found,
    500: server_error,
}

starlette_app = Starlette(
    routes=route_list,
    # middleware=[
    #     Middleware(
    #         ExceptionMiddleware,
    #         debug=True,
    #         handlers=exception_handlers
    #     )
    # ],
    exception_handlers=exception_handlers
)
