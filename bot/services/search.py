"""Нечёткий поиск (fuzzy matching) по базе FAQ с помощью библиотеки rapidfuzz."""

from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz

from bot.services.faq import FAQItem, FAQRepository


@dataclass(frozen=True)
class SearchResult:
    """Результат поиска: найденный элемент FAQ и оценка совпадения (0–100)."""

    item: FAQItem
    score: float


class FAQSearchService:
    """Ищет наиболее подходящие ответы FAQ по тексту вопроса пользователя."""

    # Минимальная длина ключевого слова для поиска по вхождению в запрос
    _MIN_KEYWORD_LENGTH = 4
    # Порог близости отдельного слова запроса к ключевому слову (учёт словоформ)
    _TOKEN_MATCH_THRESHOLD = 85

    def __init__(self, repository: FAQRepository, threshold: int = 65) -> None:
        self._repository = repository
        self._threshold = threshold

    @staticmethod
    def _normalize(text: str) -> str:
        """Приводит текст к нижнему регистру и убирает лишние пробелы."""
        return " ".join(text.lower().strip().split())

    def _keyword_score(self, normalized_query: str, normalized_keyword: str) -> float:
        """Оценивает совпадение ключевого слова с запросом на шкале 0–100.

        Все оценки сопоставимы с нечётким поиском по вопросам (0–100).
        Короткие общие ключи не получают искусственного приоритета над
        семантически близким совпадением по тексту вопроса.
        """
        if len(normalized_keyword) < self._MIN_KEYWORD_LENGTH:
            return 0.0

        alignment = float(fuzz.partial_ratio(normalized_query, normalized_keyword))
        matched_token_length = len(normalized_keyword)

        if normalized_keyword not in normalized_query:
            token_scores: list[tuple[float, int]] = []
            for token in normalized_query.split():
                if len(token) < self._MIN_KEYWORD_LENGTH:
                    continue
                token_ratio = float(fuzz.ratio(token, normalized_keyword))
                if token_ratio >= self._TOKEN_MATCH_THRESHOLD:
                    token_scores.append((token_ratio, len(token)))

            if not token_scores:
                return 0.0

            best_token_ratio, matched_token_length = max(
                token_scores, key=lambda pair: pair[0]
            )
            alignment = max(alignment, best_token_ratio)

        specificity = min(1.0, len(normalized_keyword) / matched_token_length)
        return alignment * (0.6 + 0.4 * specificity)

    def _score_item(self, normalized_query: str, item: FAQItem) -> float:
        """Считает итоговую оценку FAQ-элемента как максимум по ключам и вопросу."""
        # token_set_ratio устойчивее к ложным совпадениям, чем WRatio
        best_score = float(fuzz.token_set_ratio(normalized_query, item.question))

        for keyword in item.keywords:
            best_score = max(
                best_score,
                self._keyword_score(normalized_query, self._normalize(keyword)),
            )

        return best_score

    def search(self, query: str, limit: int = 3) -> list[SearchResult]:
        """Ищет до `limit` наиболее подходящих ответов, фильтруя по порогу совпадения."""
        normalized_query = self._normalize(query)
        if not normalized_query:
            return []

        # Все кандидаты оцениваются на единой шкале 0–100
        results: list[SearchResult] = []
        for item in self._repository.items:
            score = self._score_item(normalized_query, item)
            if score >= self._threshold:
                results.append(SearchResult(item=item, score=score))

        return sorted(
            results,
            key=lambda result: (
                result.score,
                float(fuzz.token_set_ratio(normalized_query, result.item.question)),
            ),
            reverse=True,
        )[:limit]

    def best_match(self, query: str) -> SearchResult | None:
        """Возвращает один лучший результат или None, если совпадение ниже порога."""
        results = self.search(query, limit=1)
        return results[0] if results else None
