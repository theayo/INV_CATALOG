from collections.abc import Iterator
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.auth import telegram_user_id
from app.catalog import Catalog, CatalogError, Product, get_catalog

router = APIRouter()


class ProductResponse(BaseModel):
    id: UUID
    title: str
    image_url: str
    created_at: datetime

    @classmethod
    def from_product(cls, product: Product):
        return cls(
            id=product.id,
            title=product.title,
            image_url=f"/api/products/{product.id}/image",
            created_at=product.created_at,
        )


@router.get("", response_model=list[ProductResponse])
def list_products(catalog: Catalog = Depends(get_catalog)):
    return [ProductResponse.from_product(product) for product in catalog.list_products()]


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(
    title: Annotated[str, Form(min_length=1, max_length=200)],
    photo: Annotated[UploadFile, File()],
    telegram_id: int = Depends(telegram_user_id),
    catalog: Catalog = Depends(get_catalog),
):
    contents = photo.file.read(catalog.settings.max_photo_bytes + 1)
    if len(contents) > catalog.settings.max_photo_bytes:
        raise CatalogError("Фото должно быть не больше 10 МБ.")
    return ProductResponse.from_product(catalog.create_product(telegram_id, title, contents))


@router.get("/{product_id}/image")
def product_image(product_id: UUID, catalog: Catalog = Depends(get_catalog)):
    product = catalog.get_product(product_id)
    response = catalog.storage.open(product.image_key)

    def chunks() -> Iterator[bytes]:
        try:
            yield from response.stream(64 * 1024)
        finally:
            response.close()
            response.release_conn()

    return StreamingResponse(
        chunks(),
        media_type=response.headers.get("Content-Type", "image/jpeg"),
        headers={"Cache-Control": "public, max-age=3600", "X-Content-Type-Options": "nosniff"},
    )
