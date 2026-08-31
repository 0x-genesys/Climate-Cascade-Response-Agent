"""Local-only environment loading for CLI entry points."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def load_project_environment(project_root: Path | None = None) -> Path:
    """Load an optional project `.env` without overriding process environment."""

    dotenv_path = (project_root or Path.cwd()) / ".env"
    if dotenv_path.is_file():
        load_dotenv(dotenv_path=dotenv_path, override=False)
    return dotenv_path
