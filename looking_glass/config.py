"""
Configuration management for the Looking Glass Engine.

Reads environment variables from .env file and provides typed access to all settings.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import dotenv_values


def _load_env() -> dict:
    """Load .env file from project root or user home."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        return dotenv_values(env_path)
    # Fallback to home directory
    home_env = Path.home() / ".looking-glass" / ".env"
    if home_env.exists():
        return dotenv_values(home_env)
    return {}


_ENV = _load_env()


def get(key: str, default: str = "") -> str:
    """Get a config value from environment, .env file, or default."""
    val = os.environ.get(key)
    if val is not None:
        return val
    val = _ENV.get(key)
    if val is not None:
        return val
    return default


def get_int(key: str, default: int) -> int:
    """Get a config value as integer."""
    val = get(key, str(default))
    try:
        return int(val)
    except ValueError:
        return default


def get_float(key: str, default: float) -> float:
    """Get a config value as float."""
    val = get(key, str(default))
    try:
        return float(val)
    except ValueError:
        return default


class Config:
    """Typed configuration for the Looking Glass Engine."""

    # OpenRouter settings
    openrouter_api_key: str = get("OPENROUTER_API_KEY")
    openrouter_model: str = get("OPENROUTER_MODEL", "inclusionai/ling-3.0-flash:free")
    openrouter_base_url: str = get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    # Ollama settings
    ollama_host: str = get("OLLAMA_HOST", "localhost")
    ollama_port: int = get_int("OLLAMA_PORT", 11434)
    ollama_model: str = get("OLLAMA_MODEL", "ornith:9b")
    ollama_base_url: str = get(
        "OLLAMA_BASE_URL", f"http://{ollama_host}:{ollama_port}/v1"
    )

    # Backend selection
    backend: str = get("BACKEND", "openrouter")  # "openrouter" or "ollama"

    # Field model ranges
    field_x_range: float = get_float("FIELD_X_RANGE", 10.0)
    field_y_range: float = get_float("FIELD_Y_RANGE", 10.0)
    field_z_range: float = get_float("FIELD_Z_RANGE", 10.0)

    # Database
    db_path: str = get("DB_PATH", "~/.looking-glass/sessions.db")

    # Logging
    log_level: str = get("LOG_LEVEL", "INFO")

    @property
    def ollama_full_url(self) -> str:
        """Return the full Ollama API URL."""
        return self.ollama_base_url

    @property
    def db_path_expanded(self) -> str:
        """Return the database path with home directory expanded."""
        return os.path.expanduser(self.db_path)


config = Config()