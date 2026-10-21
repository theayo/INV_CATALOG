from unittest.mock import AsyncMock

from aiogram import Bot
from aiogram.methods import SendMessage
from aiogram.types import Message, Update

from app.bot.dispatcher import create_dispatcher
from tests.fakes import FakeCatalog


async def test_full_demo_flow(settings, photo):
    catalog = FakeCatalog(settings)
    session = AsyncMock()
    session.return_value = Message.model_validate(
        {"message_id": 999, "date": 1, "chat": {"id": 42, "type": "private"}}
    )
    bot = Bot(token=settings.bot_token.get_secret_value(), session=session)

    async def download(_picture, destination):
        destination.write(photo)
        return destination

    bot.download = AsyncMock(side_effect=download)

    async def send(message_id, text=None, caption=None, with_photo=False):
        payload = {
            "message_id": message_id,
            "date": 1,
            "chat": {"id": 42, "type": "private"},
            "from": {"id": 42, "is_bot": False, "first_name": "Test"},
        }
        if text is not None:
            payload["text"] = text
        if with_photo:
            payload["photo"] = [
                {"file_id": "test", "file_unique_id": "test", "width": 8, "height": 8}
            ]
            if caption is not None:
                payload["caption"] = caption
        update = Update.model_validate({"update_id": message_id, "message": payload})
        await create_dispatcher().feed_update(bot, update, catalog=catalog, settings=settings)
        return [
            call.args[1] for call in session.call_args_list if isinstance(call.args[1], SendMessage)
        ][-1]

    reply = await send(1, "/start")
    assert reply.text == "У меня есть товар"
    assert reply.reply_markup.inline_keyboard[0][0].web_app.url == settings.web_app_url
    assert catalog.database.roles[42] == "user"
    await send(2, caption="Запрещённый", with_photo=True)
    assert not catalog.products
    await send(3, "/admin wrong")
    assert catalog.database.roles[42] == "user"
    await send(4, "/admin test-demo-code")
    assert catalog.database.roles[42] == "admin"
    await send(5, "/start")
    assert catalog.database.roles[42] == "admin"
    await send(6, "/create")
    await send(7, with_photo=True)
    assert not catalog.products
    await send(8, caption="Зелёный товар", with_photo=True)
    await send(8, caption="Зелёный товар", with_photo=True)
    assert len(catalog.products) == 1
    assert catalog.storage.uploads == 1
    await send(9, "/user")
    assert catalog.database.roles[42] == "user"
    await send(10, caption="После понижения", with_photo=True)
    assert len(catalog.products) == 1
    await send(11, "/start")
    assert catalog.database.roles[42] == "user"
