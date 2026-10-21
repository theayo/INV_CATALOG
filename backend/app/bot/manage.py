import argparse
import asyncio

from aiogram import Bot
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from app.bot.dispatcher import create_dispatcher
from app.catalog import get_catalog
from app.config import get_settings


async def run(action: str, url: str | None) -> None:
    settings = get_settings()
    token = settings.bot_token.get_secret_value()
    if not token:
        raise SystemExit("Set BOT_TOKEN in backend environment")
    async with Bot(token=token) as bot:
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Открыть каталог"),
                BotCommand(command="create", description="Создать товар (администратор)"),
                BotCommand(command="admin", description="Войти по демокоду"),
                BotCommand(command="user", description="Вернуться к роли пользователя"),
            ]
        )
        if settings.web_app_url.startswith("https://"):
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="Каталог", web_app=WebAppInfo(url=settings.web_app_url)
                )
            )
        if action == "webhook":
            secret = settings.telegram_webhook_secret.get_secret_value()
            if not url or not url.startswith("https://") or not secret:
                raise SystemExit("Provide --url https://API_HOST and TELEGRAM_WEBHOOK_SECRET")
            await bot.set_webhook(
                url=f"{url.rstrip('/')}/api/telegram/webhook",
                secret_token=secret,
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=False,
            )
            print("Webhook configured")
        else:
            await bot.delete_webhook(drop_pending_updates=False)
            await create_dispatcher().start_polling(
                bot, catalog=get_catalog(), settings=settings, handle_as_tasks=False
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the INVIX Telegram bot")
    parser.add_argument("action", choices=["webhook", "poll"])
    parser.add_argument("--url", help="Public HTTPS backend origin for webhook")
    arguments = parser.parse_args()
    asyncio.run(run(arguments.action, arguments.url))


if __name__ == "__main__":
    main()
