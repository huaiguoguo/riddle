# from distutils.file_util import write_file
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response, HTMLResponse

from utils import write_text

HTML_404_PAGE = 'hi, 别偷看了,页面被你看丢了,请喝口茶...'
HTML_500_PAGE = 'hi, 别偷看了,服务器都被你看挂了,请先喝口茶'


async def handle_404(request: Request, exc: HTTPException) -> Response:
    await write_text(f'404页面 {str(request.url)}')
    return HTMLResponse("hi, 别偷看了,页面被你看丢了,请喝口茶...", status_code=404)


async def not_found(request: Request, exc: HTTPException) -> Response:
    await write_text(f'404错误...------ {str(request.url)}')
    return PlainTextResponse(content=HTML_404_PAGE, status_code=exc.status_code)


async def server_error(request: Request, exc: Exception) -> Response:
    await write_text(f'500错误------ {str(request.url)}')
    return PlainTextResponse(content=HTML_500_PAGE, status_code=500)