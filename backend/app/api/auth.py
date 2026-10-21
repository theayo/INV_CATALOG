import time
from typing import Annotated

from aiogram.utils.web_app import safe_parse_webapp_init_data
from fastapi import Depends, Header, HTTPException

from app.config import Settings, get_settings


def telegram_user_id(
    init_data: Annotated[str | None, Header(alias="X-Telegram-Init-Data")] = None,
    settings: Settings = Depends(get_settings),
) -> int:
    token = settings.bot_token.get_secret_value()
    if not token:
        raise HTTPException(503, "Бот не настроен.")
    if not init_data:
        raise HTTPException(401, "Нужны данные авторизации Telegram Mini App.")
    try:
        data = safe_parse_webapp_init_data(token, init_data)
        age = time.time() - data.auth_date.timestamp()
        if not data.user or age < -60 or age > settings.telegram_auth_max_age:
            raise ValueError("Expired init data")
    except (ValueError, TypeError, KeyError) as error:
        raise HTTPException(401, "Недействительные данные авторизации Telegram.") from error
    return data.user.id
