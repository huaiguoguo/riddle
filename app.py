#!/usr/bin/env python
# This program is dedicated to the public domain under the CC0 license.
# pylint: disable=import-error,wrong-import-position

import asyncio
from bot import initialization
from server import server


async def main() -> None:
    botapp = await initialization()

    # webhook_info = await bot.bot.get_webhook_info()
    # print(f"======webhook_info=========={webhook_info}")
    # print(f"2------appid: {bot}")

    # bet_office_cmd = config.get('bet_office_cmd')
    # print(bet_office_cmd)

    async with botapp:
        await botapp.start()
        await server.serve()
        await botapp.stop()


if __name__ == "__main__":
    asyncio.run(main())
