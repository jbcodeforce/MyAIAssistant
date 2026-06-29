"""Resolve and load the shared MyAIAssistant repo-root .env file."""

from __future__ import annotations

import os
from pathlib import Path

_AGENT_SERVICE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECT_ROOT = _AGENT_SERVICE_ROOT.parent
PROJECT_ENV_FILE = DEFAULT_PROJECT_ROOT / ".env"


def resolve_project_root(*, start: Path | None = None) -> Path:
    """Locate the MyAIAssistant repo root from an optional starting path."""
    explicit = os.environ.get("MYAIASSISTANT_ROOT", "").strip()
    if explicit:
        return Path(explicit).resolve()

    if start is not None:
        for parent in start.resolve().parents:
            if (parent / "backend").is_dir() and (parent / "agent_service").is_dir():
                return parent

    return DEFAULT_PROJECT_ROOT


def project_env_file(*, start: Path | None = None) -> Path:
    return resolve_project_root(start=start) / ".env"


def load_project_env(*, override: bool = False, start: Path | None = None) -> bool:
    """Load repo-root .env into os.environ. Returns True if the file exists."""
    env_file = project_env_file(start=start)
    if not env_file.is_file():
        return False

    from dotenv import load_dotenv

    load_dotenv(env_file, override=override)
    return True
