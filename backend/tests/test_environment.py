from __future__ import annotations

import os
from pathlib import Path

from climate_cascade.environment import load_project_environment


def test_load_project_environment_reads_optional_dotenv_without_overriding_process_environment(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / ".env").write_text(
        "OPENAI_API_KEY=dotenv-key\nCLIMATE_CASCADE_DATABASE_URL=sqlite:///dotenv.db\n", encoding="utf-8"
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("CLIMATE_CASCADE_DATABASE_URL", "sqlite:///exported.db")

    loaded_path = load_project_environment(tmp_path)

    assert loaded_path == tmp_path / ".env"
    assert os.environ["OPENAI_API_KEY"] == "dotenv-key"
    assert os.environ["CLIMATE_CASCADE_DATABASE_URL"] == "sqlite:///exported.db"


def test_load_project_environment_allows_missing_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    loaded_path = load_project_environment(tmp_path)

    assert loaded_path == tmp_path / ".env"
    assert "OPENAI_API_KEY" not in os.environ
