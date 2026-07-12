"""Загрузка настроек приложения и вспомогательных функций для работы с JSON."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env (если он существует)
load_dotenv()

# Корневая директория проекта и каталог с данными FAQ/организации
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


@dataclass(frozen=True)
class Settings:
    """Неизменяемый набор настроек бота, собранных из переменных окружения."""

    telegram_bot_token: str
    telegram_proxy: str | None
    telegram_connect_timeout: float
    telegram_read_timeout: float
    openai_api_key: str | None
    openai_model: str
    faq_match_threshold: int
    organization_path: Path
    faq_path: Path


def get_settings() -> Settings:
    """Читает настройки из окружения и возвращает объект Settings."""
    # Токен Telegram обязателен — без него бот не запустится
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise ValueError(
            "Не задан TELEGRAM_BOT_TOKEN. Скопируйте .env.example в .env и укажите токен."
        )

    return Settings(
        telegram_bot_token=token,
        telegram_proxy=os.getenv("TELEGRAM_PROXY", "").strip() or None,
        telegram_connect_timeout=float(os.getenv("TELEGRAM_CONNECT_TIMEOUT", "30")),
        telegram_read_timeout=float(os.getenv("TELEGRAM_READ_TIMEOUT", "30")),
        # Ключ OpenAI необязателен: без него работает только поиск по FAQ
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip() or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        faq_match_threshold=int(os.getenv("FAQ_MATCH_THRESHOLD", "65")),
        organization_path=DATA_DIR / "organization.json",
        faq_path=DATA_DIR / "faq.json",
    )


def load_json(path: Path) -> dict:
    """Загружает JSON-файл по указанному пути и возвращает словарь."""
    with path.open(encoding="utf-8") as file:
        return json.load(file)
