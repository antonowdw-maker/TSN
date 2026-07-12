"""Общие фикстуры pytest: репозиторий FAQ, сервис организации и поиск."""

from __future__ import annotations

from pathlib import Path

import pytest

from bot.services.faq import FAQRepository
from bot.services.organization import OrganizationService
from bot.services.search import FAQSearchService

# Путь к каталогу data относительно корня проекта
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture
def faq_repo() -> FAQRepository:
    """Загружает FAQ из data/faq.json для использования в тестах."""
    return FAQRepository(DATA_DIR / "faq.json")


@pytest.fixture
def org_service() -> OrganizationService:
    """Загружает данные организации из data/organization.json."""
    return OrganizationService(DATA_DIR / "organization.json")


@pytest.fixture
def search_service(faq_repo: FAQRepository) -> FAQSearchService:
    """Создаёт сервис поиска с порогом совпадения 65%."""
    return FAQSearchService(faq_repo, threshold=65)
