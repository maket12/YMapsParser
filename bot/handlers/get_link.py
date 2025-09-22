from aiogram import Router, types, F
from aiogram.types import FSInputFile
import logging
from services.ymaps_parser.parser import YMapsParser
from services.excel.main import export_to_excel

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = Router()


@router.message(F.text)
async def get_link(message: types.Message):
    try:
        if message.text.startswith("https://yandex.ru/maps"):
            msg = await message.answer(
                text="Парсинг может занять время..."
            )

            data = None
            async with YMapsParser(logger) as parser:
                data = await parser.parse(url=message.text.strip())

            await msg.delete()

            if data:
                file_path = export_to_excel(data=data)
                await message.answer(
                    text="Получен результат парсинга:"
                )
                await message.answer_document(
                    document=FSInputFile(file_path)
                )
            else:
                await message.answer(
                    text="Возникла ошибка во время парсинга или ничего не удалось собрать."
                )
        else:
            await message.answer(
                text="Я не умею работать с такой ссылкой😔.\n"
                     "Ссылка должна начинаться с 'https://yandex.ru/maps'."
            )
    except Exception as e:
        logger.error(f"❌ Возникла ошибка в get_link: {e}.")
