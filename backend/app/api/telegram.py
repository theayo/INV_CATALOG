from secrets import compare_digest

from aiogram import Bot
from aiogram.types import Update
from fastapi import APIRouter, Depends, Header, HTTPException

from app.bot.dispatcher import create_dispatcher
from app.catalog import Catalog, get_catalog
from app.config import Settings, get_settings

router = APIRouter()


@router.post("/webhook")
async def webhook(
    update: Update,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    catalog: Catalog = Depends(get_catalog),
):
    token = settings.bot_token.get_secret_value()
    expected = settings.telegram_webhook_secret.get_secret_value()
    if not token or not expected:
        raise HTTPException(503, "Webhook бота не настроен.")
    if not x_telegram_bot_api_secret_token or not compare_digest(
        expected.encode(), x_telegram_bot_api_secret_token.encode()
    ):
        raise HTTPException(403, "Неверный секрет webhook.")
    async with Bot(token=token) as bot:
        await create_dispatcher().feed_update(bot, update, catalog=catalog, settings=settings)
    return {"ok": True}
