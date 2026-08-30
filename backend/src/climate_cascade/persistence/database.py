"""SQLite engine and Alembic migration entry point."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, event
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


def create_sqlite_engine(database_url: str) -> Engine:
    engine = create_engine(database_url, future=True)

    @event.listens_for(engine, "connect")
    def configure_sqlite(connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

    return engine


def migrate_database(database_url: str, *, repository_root: Path) -> None:
    """Apply the checked-in Alembic migrations to the configured database."""

    config = Config(str(repository_root / "migrations.ini"))
    config.set_main_option("script_location", str(repository_root / "backend" / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


def sqlite_url(path: Path) -> str:
    return str(URL.create("sqlite+pysqlite", database=str(path)))
