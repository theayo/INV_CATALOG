from contextlib import contextmanager
from typing import Literal

import psycopg
from psycopg.rows import dict_row

from app.config import Settings

Role = Literal["user", "admin"]


class Database:
    def __init__(self, settings: Settings):
        self.url = settings.database_url.get_secret_value()

    @contextmanager
    def connect(self):
        with psycopg.connect(self.url, row_factory=dict_row, connect_timeout=5) as connection:
            yield connection

    def ensure_user(self, telegram_id: int) -> Role:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO users (telegram_id) VALUES (%s) ON CONFLICT DO NOTHING",
                (telegram_id,),
            )
            return connection.execute(
                "SELECT role FROM users WHERE telegram_id = %s", (telegram_id,)
            ).fetchone()["role"]

    def set_role(self, telegram_id: int, role: Role) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO users (telegram_id, role) VALUES (%s, %s)
                ON CONFLICT (telegram_id) DO UPDATE SET role = EXCLUDED.role""",
                (telegram_id, role),
            )
