from io import BytesIO

import pytest
from PIL import Image

from app.config import Settings


@pytest.fixture
def settings():
    return Settings(
        _env_file=None,
        bot_token="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ_test_token",
        demo_admin_code="test-demo-code",
        telegram_webhook_secret="test-webhook-secret",
        web_app_url="https://catalog.example.com",
    )


@pytest.fixture
def photo():
    buffer = BytesIO()
    Image.new("RGB", (8, 8), "green").save(buffer, format="PNG")
    return buffer.getvalue()
