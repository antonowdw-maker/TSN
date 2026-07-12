"""Тесты загрузки и структуры базы FAQ."""

from __future__ import annotations

from pathlib import Path

import pytest

from bot.services.faq import FAQRepository

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class TestFAQRepository:
    @pytest.fixture
    def repo(self) -> FAQRepository:
        """Загружает FAQ из data/faq.json."""
        return FAQRepository(DATA_DIR / "faq.json")

    def test_loads_all_categories(self, repo: FAQRepository) -> None:
        """Проверяет наличие всех основных категорий FAQ."""
        categories = repo.list_categories()
        assert len(categories) >= 8
        category_ids = {cat_id for cat_id, _ in categories}
        assert "general" in category_ids
        assert "payments" in category_ids
        assert "contacts" in category_ids

    def test_items_have_required_fields(self, repo: FAQRepository) -> None:
        """Каждый элемент FAQ содержит обязательные поля и ключевые слова."""
        for item in repo.items:
            assert item.id
            assert item.question
            assert item.answer
            assert item.category_id
            assert len(item.keywords) > 0

    def test_get_by_id(self, repo: FAQRepository) -> None:
        """Поиск по id возвращает корректный элемент."""
        item = repo.get_by_id("dispatcher")
        assert item is not None
        assert "диспетчер" in item.question.lower() or "диспетчер" in item.answer.lower()

    def test_get_by_id_unknown_returns_none(self, repo: FAQRepository) -> None:
        """Неизвестный id возвращает None."""
        assert repo.get_by_id("nonexistent_id") is None

    def test_items_by_category(self, repo: FAQRepository) -> None:
        """Фильтрация по категории возвращает только элементы этой категории."""
        payment_items = repo.items_by_category("payments")
        assert len(payment_items) >= 3
        assert all(item.category_id == "payments" for item in payment_items)

    def test_total_faq_count(self, repo: FAQRepository) -> None:
        """В базе не менее 18 вопросов."""
        assert len(repo.items) >= 18
