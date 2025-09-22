from aiogram import Router, types
from aiogram.filters import CommandStart
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


router = Router()


@router.message(CommandStart())
async def start(message: types.Message):
    try:
        await message.answer(
            text="Привет! Я - парсер Яндекс карт.\n"
                 "Отправь мне ссылку и я соберу для тебя все данные:"
        )
    except Exception as e:
        logger.error(f"❌ Возникла ошибка в start: {e}.")
