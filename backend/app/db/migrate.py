from pathlib import Path

from app.config import get_settings
from app.db.database import Database


def migrate() -> None:
    migrations = Path(__file__).resolve().parents[2] / "migrations"
    with Database(get_settings()).connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(481925)")
        connection.execute(
            """CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )"""
        )
        for path in sorted(migrations.glob("*.sql")):
            exists = connection.execute(
                "SELECT 1 FROM schema_migrations WHERE version = %s", (path.name,)
            ).fetchone()
            if exists:
                continue
            connection.execute(path.read_text(encoding="utf-8"))
            connection.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.name,))
            print(f"Applied {path.name}")


if __name__ == "__main__":
    migrate()
