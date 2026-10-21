from aiogram import Dispatcher

from app.bot.handlers import create_router


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(disable_fsm=True)
    dispatcher.include_router(create_router())
    return dispatcher
