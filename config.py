"""Sozlamalar .env faylidan o'qiladi (parollar kodga yozilmaydi)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_URL = f"sqlite:///{BASE_DIR / 'shop.db'}"
DEFAULT_REDIS_URL = "redis://localhost:6379/0"

load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str


def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "").strip() or DEFAULT_DATABASE_URL,
        redis_url=os.getenv("REDIS_URL", "").strip() or DEFAULT_REDIS_URL,
    )
