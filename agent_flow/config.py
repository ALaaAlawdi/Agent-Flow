"""Runtime configuration loader for Agent-Flow.

Loads a project-level ``.env`` file (once) so entry points such as
``run_demo.py``, the CLI, and the FastAPI app all share the same
provider credentials (OpenAI, Anthropic, ...) without hard-coding them.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is optional at runtime
    load_dotenv = None  # type: ignore[assignment]


_LOADED = False
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_env(override: bool = False) -> Path | None:
    """Load ``<repo>/.env`` into ``os.environ`` exactly once.

    Returns the path that was loaded, or ``None`` when no ``.env`` was found
    or ``python-dotenv`` is unavailable. Safe to call multiple times.
    """
    global _LOADED
    if _LOADED and not override:
        return None
    if load_dotenv is None:
        _LOADED = True
        return None
    env_path = PROJECT_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=override)
        _LOADED = True
        return env_path
    _LOADED = True
    return None


def openai_api_key() -> str | None:
    """Return the currently configured OpenAI API key, if any."""
    load_env()
    return os.environ.get("OPENAI_API_KEY")


def default_model() -> str:
    """Default LLM used when a caller does not specify one."""
    load_env()
    return os.environ.get("AGENT_FLOW_DEFAULT_MODEL", "gpt-4o-mini")
