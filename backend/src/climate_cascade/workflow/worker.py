"""Separate local worker process for leased workflow execution."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import socket
import time

from climate_cascade.baseline import OpenAIChatCompletionsGateway
from climate_cascade.persistence import LocalArtifactStore, RunRepository, create_sqlite_engine, migrate_database

from .engine import WorkflowEngine


def build_worker_engine(
    *, database_url: str, artifact_root: Path, case_root: Path, repository_root: Path, run_migrations: bool = True
) -> WorkflowEngine:
    if run_migrations:
        migrate_database(database_url, repository_root=repository_root)
    repository = RunRepository(create_sqlite_engine(database_url))

    def gateway_factory(config: dict[str, object]):
        api_key = os.environ.get(str(config.get("api_key_env", "OPENAI_API_KEY")))
        model = config.get("model")
        if not api_key or not isinstance(model, str) or not model:
            return None
        return OpenAIChatCompletionsGateway(api_key=api_key, model=model)

    return WorkflowEngine(
        repository=repository,
        artifact_store=LocalArtifactStore(artifact_root),
        case_root=case_root,
        gateway_factory=gateway_factory,
        response_supervisor_config_path=repository_root / "config" / "agents" / "response_supervisor.json",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run leased Climate Cascade workflow jobs.")
    parser.add_argument("--database-url", default=os.environ.get("CLIMATE_CASCADE_DATABASE_URL", "sqlite:///var/climate-cascade.db"))
    parser.add_argument("--artifact-root", type=Path, default=Path(os.environ.get("CLIMATE_CASCADE_ARTIFACT_ROOT", "var/artifacts")))
    parser.add_argument("--case-root", type=Path, default=Path("data/fixtures/cases"))
    parser.add_argument("--once", action="store_true", help="Claim and process at most one eligible run.")
    parser.add_argument("--poll-seconds", type=float, default=0.5)
    args = parser.parse_args(argv)
    repository_root = Path.cwd()
    engine = build_worker_engine(
        database_url=args.database_url,
        artifact_root=args.artifact_root,
        case_root=args.case_root,
        repository_root=repository_root,
    )
    worker_id = f"{socket.gethostname()}-{os.getpid()}"
    while True:
        result = engine.process_next(worker_id=worker_id)
        if args.once:
            return 0 if result is not None else 1
        if result is None:
            time.sleep(args.poll_seconds)
