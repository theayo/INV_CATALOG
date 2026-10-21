from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.products import router as products_router
from app.api.telegram import router as telegram_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["system"])
api_router.include_router(products_router, prefix="/api/products", tags=["products"])
api_router.include_router(telegram_router, prefix="/api/telegram", tags=["telegram"])
