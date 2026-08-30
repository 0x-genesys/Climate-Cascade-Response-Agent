from __future__ import annotations

from pathlib import Path
import threading

from fastapi.testclient import TestClient
from sqlalchemy import text

from climate_cascade import local
from climate_cascade.local import main as local_main
from climate_cascade.persistence import create_sqlite_engine, sqlite_url


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CASE_ROOT = REPOSITORY_ROOT / "data" / "fixtures" / "cases"


def test_local_init_creates_sqlite_database_and_artifact_root(tmp_path: Path, capsys) -> None:
    database_path = tmp_path / "runtime" / "climate-cascade.db"
    artifact_root = tmp_path / "runtime" / "artifacts"
    database_url = sqlite_url(database_path)

    exit_code = local_main(
        [
            "init",
            "--database-url",
            database_url,
            "--artifact-root",
            str(artifact_root),
            "--repository-root",
            str(REPOSITORY_ROOT),
        ]
    )

    assert exit_code == 0
    assert database_path.is_file()
    assert artifact_root.is_dir()
    assert "initialized database=" in capsys.readouterr().out
    with create_sqlite_engine(database_url).connect() as connection:
        tables = set(connection.execute(text("SELECT name FROM sqlite_master WHERE type = 'table'")).scalars())
    assert {"runs", "run_events", "artifacts", "run_artifacts"}.issubset(tables)


def test_local_serve_starts_api_and_worker_with_shared_sqlite_runtime(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "runtime" / "climate-cascade.db"
    artifact_root = tmp_path / "runtime" / "artifacts"
    database_url = sqlite_url(database_path)
    worker_called = threading.Event()
    captured: dict[str, object] = {}

    class RecordingEngine:
        def process_next(self, *, worker_id: str):
            captured["worker_id"] = worker_id
            worker_called.set()
            return None

    def fake_build_worker_engine(
        *, database_url: str, artifact_root: Path, case_root: Path, repository_root: Path, run_migrations: bool
    ):
        captured["worker_database_url"] = database_url
        captured["worker_artifact_root"] = artifact_root
        captured["worker_case_root"] = case_root
        captured["worker_repository_root"] = repository_root
        captured["worker_run_migrations"] = run_migrations
        return RecordingEngine()

    def fake_uvicorn_run(app, *, host: str, port: int) -> None:
        captured["api_host"] = host
        captured["api_port"] = port
        assert TestClient(app).get("/v1/health").json() == {"status": "ready"}
        assert worker_called.wait(timeout=1)

    monkeypatch.setattr(local, "build_worker_engine", fake_build_worker_engine)
    monkeypatch.setattr(local.uvicorn, "run", fake_uvicorn_run)

    exit_code = local_main(
        [
            "serve",
            "--database-url",
            database_url,
            "--artifact-root",
            str(artifact_root),
            "--case-root",
            str(CASE_ROOT),
            "--repository-root",
            str(REPOSITORY_ROOT),
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
            "--worker-once",
        ]
    )

    assert exit_code == 0
    assert database_path.is_file()
    assert artifact_root.is_dir()
    assert captured["api_host"] == "127.0.0.1"
    assert captured["api_port"] == 8765
    assert captured["worker_database_url"] == database_url
    assert captured["worker_artifact_root"] == artifact_root
    assert captured["worker_case_root"] == CASE_ROOT
    assert captured["worker_repository_root"] == REPOSITORY_ROOT
    assert captured["worker_run_migrations"] is False
    assert str(captured["worker_id"]).startswith("local-")


def test_local_serve_treats_keyboard_interrupt_as_clean_shutdown(tmp_path: Path, monkeypatch) -> None:
    database_url = sqlite_url(tmp_path / "runtime" / "climate-cascade.db")

    def interrupted_uvicorn_run(app, *, host: str, port: int) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(local.uvicorn, "run", interrupted_uvicorn_run)

    exit_code = local_main(
        [
            "serve",
            "--database-url",
            database_url,
            "--artifact-root",
            str(tmp_path / "runtime" / "artifacts"),
            "--case-root",
            str(CASE_ROOT),
            "--repository-root",
            str(REPOSITORY_ROOT),
            "--no-worker",
        ]
    )

    assert exit_code == 0
