"""Settings: secrets and machine-specific values from .env, pipeline settings from config/*.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"


class Env(BaseSettings):
    """Values read from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    anthropic_api_key: str = ""
    voyage_api_key: str = ""
    sec_user_agent: str = ""
    qdrant_url: str = ""
    qdrant_path: str = "./qdrant_storage"
    max_run_cost_usd: float = 5.0


class Company(BaseModel):
    ticker: str
    name: str
    fiscal_year_end: str
    cik: int | None = None  # override when the ticker map points to a different registrant


class CorpusConfig(BaseModel):
    filings_per_company: int
    form: str
    companies: list[Company]


def load_yaml(name: str) -> dict[str, Any]:
    with (CONFIG_DIR / name).open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache
def get_env() -> Env:
    return Env()


@lru_cache
def get_settings() -> dict[str, Any]:
    return load_yaml("settings.yaml")


@lru_cache
def get_corpus() -> CorpusConfig:
    return CorpusConfig.model_validate(load_yaml("companies.yaml"))


def project_path(relative: str) -> Path:
    """Resolve a path from settings.yaml relative to the project root."""
    return PROJECT_ROOT / relative
