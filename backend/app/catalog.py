import logging
from datetime import datetime
from io import BytesIO
from uuid import UUID, uuid4

from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.db.database import Database
from app.storage.minio import ObjectStorage

logger = logging.getLogger(__name__)


class CatalogError(Exception):
    status_code = 400


class AdminRequired(CatalogError):
    status_code = 403

    def __init__(self):
        super().__init__("Создание товаров доступно только администратору.")


class ProductNotFound(CatalogError):
    status_code = 404

    def __init__(self):
        super().__init__("Товар не найден.")


class Product(BaseModel):
    id: UUID
    title: str
    image_key: str
    created_at: datetime


def validate_photo(photo: bytes, max_bytes: int) -> str:
    if not photo:
        raise CatalogError("Пришлите фотографию товара.")
    if len(photo) > max_bytes:
        raise CatalogError(f"Фото должно быть не больше {max_bytes // (1024 * 1024)} МБ.")
    try:
        with Image.open(BytesIO(photo)) as image:
            content_type = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}.get(
                image.format
            )
            if not content_type or image.width * image.height > 20_000_000:
                raise CatalogError("Нужно фото JPEG, PNG или WebP размером до 20 мегапикселей.")
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as error:
        raise CatalogError("Не удалось прочитать фото. Пришлите JPEG, PNG или WebP.") from error
    return content_type


class Catalog:
    def __init__(self, database: Database, storage: ObjectStorage, settings: Settings):
        self.database = database
        self.storage = storage
        self.settings = settings

    def list_products(self) -> list[Product]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT id, title, image_key, created_at FROM products "
                "ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [Product.model_validate(row) for row in rows]

    def get_product(self, product_id: UUID) -> Product:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT id, title, image_key, created_at FROM products WHERE id = %s", (product_id,)
            ).fetchone()
        if row is None:
            raise ProductNotFound()
        return Product.model_validate(row)

    def create_product(
        self, telegram_id: int, title: str, photo: bytes, source_key: str | None = None
    ) -> Product:
        title = title.strip()
        if not 1 <= len(title) <= 200:
            raise CatalogError("Название должно содержать от 1 до 200 символов.")

        with self.database.connect() as connection:
            # This row lock serializes uploads, retries and /user for the same sender.
            user = connection.execute(
                "SELECT role FROM users WHERE telegram_id = %s FOR UPDATE", (telegram_id,)
            ).fetchone()
            if not user or user["role"] != "admin":
                raise AdminRequired()
            if source_key:
                existing = connection.execute(
                    "SELECT id, title, image_key, created_at FROM products WHERE source_key = %s",
                    (source_key,),
                ).fetchone()
                if existing:
                    return Product.model_validate(existing)

            content_type = validate_photo(photo, self.settings.max_photo_bytes)
            product_id = uuid4()
            image_key = f"products/{product_id}"
            self.storage.put(image_key, photo, content_type)
            try:
                row = connection.execute(
                    """INSERT INTO products (id, title, image_key, source_key)
                    VALUES (%s, %s, %s, %s) RETURNING id, title, image_key, created_at""",
                    (product_id, title, image_key, source_key),
                ).fetchone()
            except Exception:
                try:
                    self.storage.remove(image_key)
                except Exception:
                    logger.exception("Could not remove an image after a failed insert")
                raise
        # Do not delete the image on an ambiguous COMMIT failure: the row may exist.
        return Product.model_validate(row)


def get_catalog() -> Catalog:
    settings = get_settings()
    return Catalog(Database(settings), ObjectStorage(settings), settings)
