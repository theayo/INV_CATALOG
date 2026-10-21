import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient

from app.catalog import get_catalog
from app.config import get_settings
from app.main import create_app
from tests.fakes import FakeCatalog


def signed_init_data(token: str, user_id=42, auth_date=None):
    fields = {
        "auth_date": str(int(time.time()) if auth_date is None else auth_date),
        "user": json.dumps({"id": user_id, "first_name": "Test"}),
        "query_id": "test-query",
    }
    check = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


@pytest.fixture
def api(settings):
    app = create_app()
    catalog = FakeCatalog(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_catalog] = lambda: catalog
    with TestClient(app) as client:
        yield client, catalog


def test_public_list_and_private_creation(api, settings, photo):
    client, catalog = api
    assert client.get("/api/products").json() == []
    form = {"title": "Зелёный товар"}
    files = {"photo": ("photo.png", photo, "image/png")}
    assert client.post("/api/products", data=form, files=files).status_code == 401
    headers = {"X-Telegram-Init-Data": signed_init_data(settings.bot_token.get_secret_value())}
    assert client.post("/api/products", headers=headers, data=form, files=files).status_code == 403
    catalog.database.set_role(42, "admin")
    result = client.post("/api/products", headers=headers, data=form, files=files)
    assert result.status_code == 201
    assert "image_key" not in result.json()
    products = client.get("/api/products").json()
    assert len(products) == 1
    assert products[0]["title"] == form["title"]
    image = client.get(products[0]["image_url"])
    assert image.status_code == 200
    assert image.content == photo
    assert image.headers["content-type"] == "image/png"
    catalog.database.set_role(42, "user")
    assert client.post("/api/products", headers=headers, data=form, files=files).status_code == 403


@pytest.mark.parametrize("kind", ["forged", "expired", "future"])
def test_invalid_telegram_identity(api, settings, photo, kind):
    client, catalog = api
    catalog.database.set_role(42, "admin")
    token = settings.bot_token.get_secret_value()
    timestamp = int(time.time()) + {"forged": 0, "expired": -7200, "future": 600}[kind]
    data = signed_init_data("another-token" if kind == "forged" else token, auth_date=timestamp)
    response = client.post(
        "/api/products",
        headers={"X-Telegram-Init-Data": data},
        data={"title": "Test"},
        files={"photo": ("photo.png", photo, "image/png")},
    )
    assert response.status_code == 401
    assert catalog.list_products() == []


def test_webhook_rejects_missing_or_invalid_secret(api):
    client, _ = api
    for headers in ({}, {"X-Telegram-Bot-Api-Secret-Token": "wrong"}):
        response = client.post("/api/telegram/webhook", json={"update_id": 1}, headers=headers)
        assert response.status_code == 403


def test_health_and_missing_images(api):
    client, _ = api
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/api/products/00000000-0000-0000-0000-000000000001/image").status_code == 404
