"""Application settings loaded from environment variables and `.env`."""

from pathlib import Path
from typing import Any

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigError(Exception):
    """Raised when the configuration is missing or invalid."""


class Settings(BaseSettings):
    """All runtime configuration. Field names map to env vars case-insensitively."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_base_url: str = "https://integrate.api.nvidia.com/v1"
    llm_api_key: str
    llm_model: str = "meta/llama-3.3-70b-instruct"
    llm_temperature: float = 0.8
    # None = send nothing. Set true/false for models with a thinking switch.
    llm_enable_thinking: bool | None = None
    persona_file: Path = Path("personas/relic.yaml")
    user_name: str = "choom"
    data_dir: Path = Path("./data")
    history_limit: int = 20


def load_settings(**overrides: Any) -> Settings:
    """Load settings, turning validation failures into a friendly `ConfigError`."""
    try:
        return Settings(**overrides)
    except ValidationError as exc:
        errors = exc.errors()
        if any(e["type"] == "missing" and e["loc"] == ("llm_api_key",) for e in errors):
            raise ConfigError(
                "LLM_API_KEY is not set. Copy .env.example to .env and add your key "
                "(free NVIDIA NIM keys: https://build.nvidia.com)."
            ) from exc
        problems = "; ".join(f"{str(e['loc'][0]).upper()}: {e['msg']}" for e in errors)
        raise ConfigError(f"Invalid configuration: {problems}") from exc
