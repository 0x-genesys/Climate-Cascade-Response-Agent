"""SQLite engine and Alembic migration entry point."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, event
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url


def create_sqlite_engine(database_url: str) -> Engine:
    ensure_sqlite_parent(database_url)
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

    ensure_sqlite_parent(database_url)
    config = Config(str(repository_root / "migrations.ini"))
    config.set_main_option("script_location", str(repository_root / "backend" / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


def sqlite_url(path: Path) -> str:
    return str(URL.create("sqlite+pysqlite", database=str(path)))


def ensure_sqlite_parent(database_url: str) -> None:
    """Create the parent directory for file-backed SQLite URLs."""

    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or not url.database or url.database == ":memory:":
        return
    Path(url.database).expanduser().parent.mkdir(parents=True, exist_ok=True)
