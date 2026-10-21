import os
from contextlib import contextmanager
from uuid import uuid4

import psycopg
import pytest
from psycopg.conninfo import make_conninfo
from psycopg.sql import SQL, Identifier
from pydantic import SecretStr

from app.catalog import AdminRequired, Catalog, CatalogError
from app.db.database import Database
from app.db.migrate import migrate
from tests.fakes import MemoryStorage


@pytest.fixture
def db_catalog(settings, monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL integration checks")
    schema = "invix_test_" + uuid4().hex
    with psycopg.connect(url, autocommit=True) as admin:
        admin.execute(SQL("CREATE SCHEMA {}").format(Identifier(schema)))
    settings = settings.model_copy(update={"database_url": SecretStr(make_conninfo(url))})

    class SchemaDatabase(Database):
        @contextmanager
        def connect(self):
            with super().connect() as connection:
                connection.execute(SQL("SET LOCAL search_path TO {}").format(Identifier(schema)))
                yield connection

    monkeypatch.setattr("app.db.migrate.get_settings", lambda: settings)
    monkeypatch.setattr("app.db.migrate.Database", SchemaDatabase)
    try:
        migrate()
        migrate()
        yield Catalog(SchemaDatabase(settings), MemoryStorage(), settings)
    finally:
        with psycopg.connect(url, autocommit=True) as admin:
            admin.execute(SQL("DROP SCHEMA {} CASCADE").format(Identifier(schema)))


def test_roles_persist_and_start_does_not_reset_them(db_catalog):
    database = db_catalog.database
    assert database.ensure_user(42) == "user"
    database.set_role(42, "admin")
    assert type(database)(db_catalog.settings).ensure_user(42) == "admin"
    database.set_role(42, "user")
    assert type(database)(db_catalog.settings).ensure_user(42) == "user"


def test_products_and_retries_across_instances(db_catalog, photo):
    db_catalog.database.set_role(42, "admin")
    product = db_catalog.create_product(42, "  Товар  ", photo, "telegram:42:100")
    second = Catalog(
        type(db_catalog.database)(db_catalog.settings), db_catalog.storage, db_catalog.settings
    )
    duplicate = second.create_product(42, "Товар", photo, "telegram:42:100")
    assert duplicate.id == product.id
    assert product.title == "Товар"
    assert len(second.list_products()) == 1
    assert db_catalog.storage.uploads == 1
    assert second.get_product(product.id) == product
    second.database.set_role(42, "user")
    with pytest.raises(AdminRequired):
        db_catalog.create_product(42, "Запрещённый", photo)


def test_sql_failure_removes_uploaded_photo(db_catalog, photo):
    db_catalog.database.set_role(42, "admin")
    with db_catalog.database.connect() as connection:
        connection.execute("ALTER TABLE products ADD CHECK (title <> 'Reject me')")
    with pytest.raises(psycopg.errors.CheckViolation):
        db_catalog.create_product(42, "Reject me", photo)
    assert db_catalog.list_products() == []
    assert db_catalog.storage.objects == {}


def test_invalid_input_does_not_create_a_record_or_upload(db_catalog, photo):
    db_catalog.database.set_role(42, "admin")
    for title, image in [(" ", photo), ("x" * 201, photo), ("Broken", b"not an image")]:
        with pytest.raises(CatalogError):
            db_catalog.create_product(42, title, image)
    assert db_catalog.list_products() == []
    assert db_catalog.storage.uploads == 0
