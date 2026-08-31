"""CLI for the FastAPI control plane."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import uvicorn

from climate_cascade.environment import load_project_environment

from .app import build_services, create_app


def main(argv: list[str] | None = None) -> int:
    load_project_environment()
    parser = argparse.ArgumentParser(description="Serve the Climate Cascade control API.")
    parser.add_argument("--database-url", default=os.environ.get("CLIMATE_CASCADE_DATABASE_URL", "sqlite:///var/climate-cascade.db"))
    parser.add_argument("--artifact-root", type=Path, default=Path(os.environ.get("CLIMATE_CASCADE_ARTIFACT_ROOT", "var/artifacts")))
    parser.add_argument("--case-root", type=Path, default=Path("data/fixtures/cases"))
    parser.add_argument("--dashboard-root", type=Path, default=Path("dashboard"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    services = build_services(
        database_url=args.database_url,
        artifact_root=args.artifact_root,
        case_root=args.case_root,
        dashboard_root=args.dashboard_root,
        repository_root=Path.cwd(),
    )
    uvicorn.run(create_app(services=services), host=args.host, port=args.port)
    return 0
