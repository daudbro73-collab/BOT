from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Allow running as `python main.py` from project root
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import get_settings
from src.bot.handlers import router
from src.scanner.engine import ScannerEngine
from src.storage.users import UserStore


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("main")


async def main() -> None:
    settings = get_settings()
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    users = UserStore()
    scanner = ScannerEngine(bot=bot, users=users)

    dp["users"] = users
    dp.include_router(router)

    # aiogram 3 dependency injection via workflow data
    @dp.update.outer_middleware()
    async def inject_users(handler, event, data):
        data["users"] = users
        return await handler(event, data)

    await scanner.start()
    logger.info("Bot polling started")
    try:
        await dp.start_polling(bot)
    finally:
        await scanner.stop()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
