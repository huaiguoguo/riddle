import os
from starlette.routing import Route

from app.controller.index import forward, home

webhook_endpoint = os.getenv('TELEGRAM_WEBHOOK_BOT_ENDPOINT')

route_list = [
    Route("/", home, methods=["GET"]),
    Route(f"/{webhook_endpoint}", forward, methods=["POST"]),
    # Route("/chat_with_gpt", chatbot, methods=["GET"]),
    # Route("/healthcheck", health, methods=["GET"]),
    # Route("/submitpayload", custom_updates, methods=["POST", "GET"]),
]
