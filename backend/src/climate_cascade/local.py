"""Local development entry point for one-command SQLite/API/worker startup."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import socket
import threading
import time

import uvicorn

from climate_cascade.api import build_services, create_app
from climate_cascade.environment import load_project_environment
from climate_cascade.persistence import migrate_database
from climate_cascade.workflow.worker import build_worker_engine


DEFAULT_DATABASE_URL = "sqlite:///var/climate-cascade.db"
DEFAULT_ARTIFACT_ROOT = Path("var/artifacts")
DEFAULT_CASE_ROOT = Path("data/fixtures/cases")
DEFAULT_DASHBOARD_ROOT = Path("dashboard")


def main(argv: list[str] | None = None) -> int:
    load_project_environment()
    parser = argparse.ArgumentParser(description="Prepare or run the local Climate Cascade control plane.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create local runtime directories and apply SQLite migrations.")
    _add_runtime_arguments(init_parser)

    serve_parser = subparsers.add_parser("serve", help="Start the FastAPI server and optional local worker.")
    _add_runtime_arguments(serve_parser)
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)
    serve_parser.add_argument("--dashboard-root", type=Path, default=DEFAULT_DASHBOARD_ROOT)
    serve_parser.add_argument("--no-worker", action="store_true", help="Start only the API server.")
    serve_parser.add_argument("--worker-once", action="store_true", help="Let the worker claim at most one run, for smoke tests.")
    serve_parser.add_argument("--poll-seconds", type=float, default=0.5)

    args = parser.parse_args(argv)
    if args.command == "init":
        initialize_local_runtime(
            database_url=args.database_url,
            artifact_root=args.artifact_root,
            repository_root=args.repository_root,
        )
        print(
            f"initialized database={args.database_url} artifacts={args.artifact_root}",
            flush=True,
        )
        return 0
    if args.command == "serve":
        serve_local(
            database_url=args.database_url,
            artifact_root=args.artifact_root,
            case_root=args.case_root,
            repository_root=args.repository_root,
            dashboard_root=args.dashboard_root,
            host=args.host,
            port=args.port,
            worker_enabled=not args.no_worker,
            worker_once=args.worker_once,
            poll_seconds=args.poll_seconds,
        )
        return 0
    raise AssertionError(f"Unhandled command {args.command}")


def _add_runtime_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--database-url",
        default=os.environ.get("CLIMATE_CASCADE_DATABASE_URL", DEFAULT_DATABASE_URL),
        help="SQLite URL used by the API and worker.",
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=Path(os.environ.get("CLIMATE_CASCADE_ARTIFACT_ROOT", str(DEFAULT_ARTIFACT_ROOT))),
        help="Directory for immutable content-addressed artifacts.",
    )
    parser.add_argument("--case-root", type=Path, default=DEFAULT_CASE_ROOT)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())


def initialize_local_runtime(*, database_url: str, artifact_root: Path, repository_root: Path) -> None:
    artifact_root.mkdir(parents=True, exist_ok=True)
    migrate_database(database_url, repository_root=repository_root)


def serve_local(
    *,
    database_url: str,
    artifact_root: Path,
    case_root: Path,
    repository_root: Path,
    dashboard_root: Path,
    host: str,
    port: int,
    worker_enabled: bool,
    worker_once: bool,
    poll_seconds: float,
) -> None:
    initialize_local_runtime(database_url=database_url, artifact_root=artifact_root, repository_root=repository_root)
    services = build_services(
        database_url=database_url,
        artifact_root=artifact_root,
        case_root=case_root,
        dashboard_root=dashboard_root,
        repository_root=repository_root,
        run_migrations=False,
    )
    stop_worker = threading.Event()
    worker_thread: threading.Thread | None = None
    if worker_enabled:
        engine = build_worker_engine(
            database_url=database_url,
            artifact_root=artifact_root,
            case_root=case_root,
            repository_root=repository_root,
            run_migrations=False,
        )
        worker_id = f"local-{socket.gethostname()}-{os.getpid()}"
        worker_thread = threading.Thread(
            target=_worker_loop,
            kwargs={
                "engine": engine,
                "worker_id": worker_id,
                "stop_event": stop_worker,
                "once": worker_once,
                "poll_seconds": poll_seconds,
            },
            daemon=True,
        )
        worker_thread.start()

    try:
        uvicorn.run(create_app(services=services), host=host, port=port)
    except KeyboardInterrupt:
        # Ctrl-C is the normal interactive shutdown path for the local control plane.
        pass
    finally:
        stop_worker.set()
        if worker_thread is not None:
            try:
                worker_thread.join(timeout=2)
            except KeyboardInterrupt:
                # A second Ctrl-C should not turn an otherwise clean shutdown into a traceback.
                pass


def _worker_loop(*, engine, worker_id: str, stop_event: threading.Event, once: bool, poll_seconds: float) -> None:
    while not stop_event.is_set():
        result = engine.process_next(worker_id=worker_id)
        if once:
            return
        if result is None:
            time.sleep(poll_seconds)
