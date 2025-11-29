"""Centralized application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DOTENV_PATH = _PROJECT_ROOT / ".env"

# Load environment variables once so both the ETL and Streamlit layers share settings.
if _DOTENV_PATH.exists():
    load_dotenv(dotenv_path=_DOTENV_PATH, override=False)
else:
    load_dotenv(override=False)


@dataclass(frozen=True)
class DatabaseSettings:
    """Connection details for the relational backend."""

    host: str
    port: int
    user: str
    password: str
    name: str


@dataclass(frozen=True)
class VisualizationSettings:
    """Defaults applied across Matplotlib and Plotly charts."""

    color_palette: str = "viridis"
    plotly_template: str = "plotly_white"


@dataclass(frozen=True)
class AppSettings:
    """Aggregate configuration consumed throughout the dashboard."""

    database: DatabaseSettings
    available_services: List[str] = field(
        default_factory=lambda: [
            "Netflix",
            "Amazon Prime Video",
            "Hulu",
            "Disney+",
        ]
    )
    available_content_types: List[str] = field(
        default_factory=lambda: ["MOVIE", "TV_SHOW"]
    )
    visualization: VisualizationSettings = field(
        default_factory=VisualizationSettings
    )
    summary: str = field(init=False)

    def __post_init__(self) -> None:
        summary = (
            f"Database host={self.database.host}:{self.database.port}, "
            f"user={self.database.user}, schema={self.database.name}"
        )
        object.__setattr__(self, "summary", summary)

    def settings_summary(self) -> str:
        return self.summary


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return cached application settings."""

    return AppSettings(
        database=DatabaseSettings(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "password"),
            name=os.getenv("DB_NAME", "streaming_media_db"),
        )
    )


def settings_summary() -> str:
    """Human-readable description useful for Streamlit debug panels."""

    return get_settings().summary
