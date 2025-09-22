from aiogram import Dispatcher
from bot.handlers.start import router as start_router
from bot.handlers.get_link import router as get_link_router
from bot.handlers.unknown import router as unknown_router


def include_all_routers(dp: Dispatcher):
    routers = [start_router, get_link_router, unknown_router]
    dp.include_routers(*routers)
