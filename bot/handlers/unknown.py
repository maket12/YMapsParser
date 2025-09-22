from aiogram import Router, types, F
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = Router()


@router.message()
async def unknown(message: types.Message):
    try:
        await message.answer(
            text="Отправь мне ссылку. Я не умею работать с другими данными😔."
        )
    except Exception as e:
        logger.error(f"❌ Возникла ошибка в unknown: {e}.")
