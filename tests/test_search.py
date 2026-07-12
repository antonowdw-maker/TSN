"""Тесты нечёткого поиска по базе FAQ."""

from __future__ import annotations

import pytest
from rapidfuzz import fuzz

from bot.services.search import FAQSearchService


class TestFAQSearchService:
    @pytest.mark.parametrize(
        ("query", "expected_id"),
        [
            ("Как оплатить взносы?", "payment_methods"),
            ("где офис тсн", "address"),
            ("номер диспетчерской", "dispatcher"),
            ("соседи шумят ночью", "noise"),
            ("показания счетчиков", "meter_readings"),
            ("общее собрание собственников", "general_meeting"),
            ("перепланировка квартиры", "apartment_repair"),
            ("как связаться с председателем", "contact_management"),
        ],
    )
    def test_best_match_popular_questions(
        self,
        search_service: FAQSearchService,
        query: str,
        expected_id: str,
    ) -> None:
        """Популярные вопросы находят ожидаемый FAQ-элемент с достаточным score."""
        result = search_service.best_match(query)
        assert result is not None, f"Не найден ответ для: {query}"
        assert result.item.id == expected_id, (
            f"Для '{query}' ожидался {expected_id}, получен {result.item.id}"
        )
        assert result.score >= 65

    def test_search_returns_multiple_results(self, search_service: FAQSearchService) -> None:
        """Поиск может вернуть несколько релевантных результатов."""
        results = search_service.search("оплата взносов")
        assert len(results) >= 1

    def test_empty_query_returns_empty(self, search_service: FAQSearchService) -> None:
        """Пустой запрос не возвращает результатов."""
        assert search_service.search("") == []
        assert search_service.search("   ") == []

    def test_unrelated_query_low_score(self, search_service: FAQSearchService) -> None:
        """Нерелевантный запрос не находит совпадений."""
        result = search_service.best_match("как приготовить борщ")
        assert result is None

    def test_legal_keywords_in_answers(self, search_service: FAQSearchService) -> None:
        """Ответы на юридические вопросы содержат ссылки на законы."""
        result = search_service.best_match("задолженность по взносам")
        assert result is not None
        assert "ЖК РФ" in result.item.answer or "ст." in result.item.answer

    def test_scores_use_single_zero_to_hundred_scale(
        self, search_service: FAQSearchService
    ) -> None:
        """Оценки ключей и нечёткого поиска сопоставимы на шкале 0–100."""
        normalized_query = search_service._normalize("как связаться с председателем")

        contact = next(
            item for item in search_service._repository.items if item.id == "contact_management"
        )
        apartment = next(
            item for item in search_service._repository.items if item.id == "apartment_repair"
        )

        question_score = float(fuzz.token_set_ratio(normalized_query, contact.question))
        short_keyword_score = search_service._keyword_score(normalized_query, "офис")

        assert 0 <= question_score <= 100
        assert 0 <= short_keyword_score <= 100
        assert short_keyword_score < 100
        assert question_score > short_keyword_score
        assert search_service._score_item(normalized_query, apartment) < question_score
        assert search_service.best_match("как связаться с председателем").item.id == "contact_management"
