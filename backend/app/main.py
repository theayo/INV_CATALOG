import logging

import psycopg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from minio.error import S3Error
from urllib3.exceptions import HTTPError

from app import __version__
from app.api.health import router as health_router
from app.api.products import router as products_router
from app.api.telegram import router as telegram_router
from app.catalog import CatalogError
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, version=__version__)
    application.include_router(health_router)
    application.include_router(products_router)
    application.include_router(telegram_router)

    @application.exception_handler(CatalogError)
    def catalog_error(_request: Request, error: CatalogError):
        return JSONResponse({"detail": str(error)}, status_code=error.status_code)

    def storage_error(_request: Request, error: Exception):
        logging.getLogger(__name__).error("Storage request failed", exc_info=error)
        return JSONResponse(
            {"detail": "Хранилище временно недоступно. Попробуйте ещё раз."}, status_code=503
        )

    for error_type in (psycopg.Error, S3Error, HTTPError):
        application.add_exception_handler(error_type, storage_error)
    return application


app = create_app()
