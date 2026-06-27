"""Typed application settings, loaded from YAML with env overrides.

Keeping config declarative (YAML) and typed (pydantic) means the same config
drives the API, CLI, Docker, and RunPod runs without code changes.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ServerSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class BenchmarkSettings(BaseModel):
    enabled: bool = True
    output_dir: Path = Path("benchmarks/runs")


class ProviderSettings(BaseModel):
    # Per-provider free-form options (weights path, dtype, attention impl, …).
    options: dict[str, dict[str, object]] = Field(default_factory=dict)


class Settings(BaseModel):
    default_provider: str = "skyreels"
    output_dir: Path = Path("outputs")
    server: ServerSettings = Field(default_factory=ServerSettings)
    benchmark: BenchmarkSettings = Field(default_factory=BenchmarkSettings)
    providers: ProviderSettings = Field(default_factory=ProviderSettings)


def load_settings(path: str | Path = "config/default.yaml") -> Settings:
    """Load settings from a YAML file; falls back to defaults if absent."""
    p = Path(path)
    if not p.exists():
        return Settings()
    data = yaml.safe_load(p.read_text()) or {}
    return Settings.model_validate(data)
