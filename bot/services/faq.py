"""Загрузка и доступ к базе часто задаваемых вопросов (FAQ) из JSON."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bot.config import load_json


@dataclass(frozen=True)
class FAQItem:
    """Один элемент FAQ: вопрос, ответ, ключевые слова и принадлежность к категории."""

    id: str
    question: str
    answer: str
    keywords: list[str]
    category_id: str
    category_title: str


class FAQRepository:
    """Репозиторий FAQ: загружает данные из JSON и предоставляет методы выборки."""

    def __init__(self, faq_path: Path) -> None:
        self._items = self._load_items(faq_path)

    @staticmethod
    def _load_items(faq_path: Path) -> list[FAQItem]:
        """Парсит JSON и преобразует записи в список объектов FAQItem."""
        data = load_json(faq_path)
        items: list[FAQItem] = []
        for category in data.get("categories", []):
            for item in category.get("items", []):
                items.append(
                    FAQItem(
                        id=item["id"],
                        question=item["question"],
                        answer=item["answer"],
                        keywords=item.get("keywords", []),
                        category_id=category["id"],
                        category_title=category["title"],
                    )
                )
        return items

    @property
    def items(self) -> list[FAQItem]:
        """Возвращает полный список всех элементов FAQ."""
        return self._items

    def get_by_id(self, item_id: str) -> FAQItem | None:
        """Находит элемент FAQ по уникальному идентификатору."""
        for item in self._items:
            if item.id == item_id:
                return item
        return None

    def list_categories(self) -> list[tuple[str, str]]:
        """Возвращает список категорий в виде пар (id, название) без дубликатов."""
        seen: set[str] = set()
        result: list[tuple[str, str]] = []
        for item in self._items:
            if item.category_id not in seen:
                seen.add(item.category_id)
                result.append((item.category_id, item.category_title))
        return result

    def items_by_category(self, category_id: str) -> list[FAQItem]:
        """Возвращает все вопросы, принадлежащие указанной категории."""
        return [item for item in self._items if item.category_id == category_id]
