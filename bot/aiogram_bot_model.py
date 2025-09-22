import os
from dotenv import load_dotenv
import logging
from aiogram import Dispatcher, Bot
from bot.include_routers import include_all_routers

dp = Dispatcher()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def load_bot_token():
    load_dotenv()
    return os.getenv("BOT_TOKEN")


async def aiogram_bot_start():
    try:
        bot_token = load_bot_token()
        if bot_token is None:
            logger.error("BOT_TOKEN is missing")

        logger.debug("🛠 Admin panel is preparing to start...")
        logger.info("👨‍💻 Developer: https://kwork.ru/user/maket14 (commercial project).")

        bot = Bot(token=bot_token)

        include_all_routers(dp=dp)
        logger.debug("📡 Routers included successfully.")

        logger.debug("✅ Admin panel successfully started. Enjoy using it!")

        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"💥 Fatal error during admin panel startup: {e}")
