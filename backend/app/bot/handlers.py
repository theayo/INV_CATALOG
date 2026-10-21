import asyncio
from io import BytesIO
from secrets import compare_digest

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from app.catalog import Catalog, CatalogError
from app.config import Settings

PHOTO_PROMPT = "Пришлите одно фото с названием товара в подписи (до 200 символов)."


def menu(settings: Settings, admin: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if settings.web_app_url.startswith("https://"):
        rows.append(
            [
                InlineKeyboardButton(
                    text="Открыть каталог", web_app=WebAppInfo(url=settings.web_app_url)
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="В браузере", url=settings.web_app_url)])
    if admin:
        rows.append([InlineKeyboardButton(text="Создать товар", callback_data="create_product")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def user_role(message: Message, catalog: Catalog) -> str:
    return await asyncio.to_thread(catalog.database.ensure_user, message.from_user.id)


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(disable_fsm=True)
    dispatcher.message.filter(F.chat.type == "private", F.from_user)
    dispatcher.callback_query.filter(F.message.chat.type == "private")

    @dispatcher.message(CommandStart())
    async def start(message: Message, catalog: Catalog, settings: Settings):
        role = await user_role(message, catalog)
        await message.answer("У меня есть товар", reply_markup=menu(settings, role == "admin"))

    @dispatcher.message(Command("admin"))
    async def admin(message: Message, command: CommandObject, catalog: Catalog, settings: Settings):
        await user_role(message, catalog)
        expected = settings.demo_admin_code.get_secret_value()
        if not expected:
            await message.answer("Демовход администратора пока не настроен.")
            return
        if not command.args or not compare_digest(command.args.strip().encode(), expected.encode()):
            await message.answer("Неверный демокод. Используйте /admin <демокод>.")
            return
        await asyncio.to_thread(catalog.database.set_role, message.from_user.id, "admin")
        await message.answer(
            "Теперь вы администратор. Можно создать товар; /user вернёт обычную роль.",
            reply_markup=menu(settings, admin=True),
        )

    @dispatcher.message(Command("user"))
    async def user(message: Message, catalog: Catalog, settings: Settings):
        await asyncio.to_thread(catalog.database.set_role, message.from_user.id, "user")
        await message.answer(
            "Вы обычный пользователь. Добавление товаров недоступно.", reply_markup=menu(settings)
        )

    @dispatcher.message(Command("create"))
    @dispatcher.message(F.text == "Создать товар")
    async def create(message: Message, catalog: Catalog):
        if await user_role(message, catalog) != "admin":
            await message.answer("Создание товаров доступно только администратору.")
            return
        await message.answer(PHOTO_PROMPT)

    @dispatcher.callback_query(F.data == "create_product")
    async def create_callback(query: CallbackQuery, catalog: Catalog):
        role = await asyncio.to_thread(catalog.database.ensure_user, query.from_user.id)
        if role != "admin":
            await query.answer("Создание доступно только администратору.", show_alert=True)
            return
        await query.answer()
        await query.message.answer(PHOTO_PROMPT)

    @dispatcher.message(F.photo)
    async def photo(message: Message, bot: Bot, catalog: Catalog, settings: Settings):
        if await user_role(message, catalog) != "admin":
            await message.answer("Создание товаров доступно только администратору.")
            return
        if message.media_group_id:
            await message.answer("Пришлите одно фото с подписью, без альбома.")
            return
        title = (message.caption or "").strip()
        if not 1 <= len(title) <= 200:
            await message.answer("Добавьте к фото название от 1 до 200 символов.")
            return
        picture = message.photo[-1]
        if picture.file_size and picture.file_size > settings.max_photo_bytes:
            await message.answer("Фото должно быть не больше 10 МБ.")
            return
        destination = BytesIO()
        await bot.download(picture, destination=destination)
        try:
            product = await asyncio.to_thread(
                catalog.create_product,
                message.from_user.id,
                title,
                destination.getvalue(),
                f"telegram:{message.chat.id}:{message.message_id}",
            )
        except CatalogError as error:
            await message.answer(str(error))
            return
        await message.answer(
            f"Товар «{product.title}» сохранён.", reply_markup=menu(settings, admin=True)
        )

    @dispatcher.message()
    async def fallback(message: Message, catalog: Catalog, settings: Settings):
        role = await user_role(message, catalog)
        text = "У меня есть товар"
        if role == "admin":
            text += "\nДля создания пришлите фото с названием в подписи одним сообщением."
        await message.answer(text, reply_markup=menu(settings, role == "admin"))

    return dispatcher
