import json

import httpx
from starlette import requests
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse, JSONResponse
from telegram import Update

from bot import bot_application
from utils import write_text
from logger import logger_instance


async def home(request: Request) -> Response:
    # return PlainTextResponse(content='你好, 老板!')
    data = {
        'code': 200,
        'message': '老板,你好,请喝茶, 想看点什么呢...',
        'status': 200
    }
    # logger_instance().info('老板来了...')

    await write_text('老板来了...')
    return JSONResponse(content=data)


async def forward(request: Request) -> Response:
    """Handle incoming Telegram updates by putting them into the `update_queue`"""
    # bot_application = BotApplication().bot_application
    # print('/////////////////////////////////')
    # print(bot_application)

    await bot_application.update_queue.put(
        Update.de_json(data=await request.json(), bot=bot_application.bot)
    )
    await write_text(await request.json(), 'forward_access.log')
    return Response()


# async def chat_with_gpt(prompt: Request):
#     OPEN_API_KEY = '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'
#     CHATGPT_API_URL = 'https://api.openai.com/v1/engines/davinci-codex/completions'
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {OPEN_API_KEY}"
#     }
#
#     data = {
#         "prompt": prompt,
#         "max_tokens": 60,
#         "temperature": 0.7
#     }
#
#     response = requests.Re(CHATGPT_API_URL, json=data, headers=headers)
#     if response.status_code == 200:
#         return response.json()['choices'][0]['text'].strip()
#     else:
#         return "Sorry, I am not able to process your request right now."


async def chat_with_gpt(prompt: str) -> str:
    # url = "https://api-inference.huggingface.co/models/uer/gpt2-chinese-cluecorpussmall"
    OPEN_API_KEY = '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'
    CHATGPT_API_URL = 'https://api.openai.com/v1/engines/davinci-codex/completions'
    headers = {"Authorization": f"Bearer {CHATGPT_API_URL}"}
    data = {"inputs": prompt}
    async with httpx.AsyncClient() as client:
        response = await client.post(CHATGPT_API_URL, headers=headers, json=data)
        response.raise_for_status()
        output = response.json()["outputs"][0]
        return output["generated_text"].strip()


async def chatbot(request):
    body = await request.json()
    prompt = body.get("prompt")
    if prompt is None:
        return JSONResponse({"error": "Prompt is missing"}, status_code=400)
    response = await chat_with_gpt(prompt)
    return JSONResponse({"response": response})
