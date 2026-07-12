"""Сервис AI-ассистента: формирует ответы через OpenAI на основе контекста организации и FAQ."""

from __future__ import annotations

from openai import AsyncOpenAI

from bot.services.faq import FAQRepository
from bot.services.organization import OrganizationService

# Системный промпт задаёт роль и правила поведения AI (без реальных персональных данных)
SYSTEM_PROMPT = """\
Вы — вежливый и компетентный ассистент ТСН (Ж) «Пример» \
(г. Примерный, микрорайон Центральный 1).

Ваши задачи:
- отвечать на вопросы жителей о деятельности ТСН;
- при необходимости ссылаться на нормы ГК РФ, ЖК РФ и иные законы РФ;
- направлять жителей к диспетчерской, правлению или нужному специалисту;
- быть тактичным, понятным и структурированным.

Правила:
1. Отвечайте на русском языке.
2. Если информации недостаточно — честно скажите об этом и предложите \
обратиться в офис или на info@example-tsn.local.
3. Не выдумывайте телефоны, суммы взносов и решения собраний.
4. При юридических вопросах указывайте статьи законов (например, ст. 158 ЖК РФ).
5. Для аварийных ситуаций рекомендуйте звонить в диспетчерскую/аварийную службу.
6. Ответы должны быть краткими (до 500 слов), с маркированными списками где уместно.
"""


class AIAssistantService:
    """Обёртка над OpenAI API для генерации ответов на вопросы жителей."""

    def __init__(
        self,
        api_key: str,
        model: str,
        organization: OrganizationService,
        faq_repository: FAQRepository,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._organization = organization
        self._faq_repository = faq_repository

    def _build_faq_context(self) -> str:
        """Собирает краткий контекст из первых 15 записей FAQ для промпта."""
        lines = ["База популярных вопросов:"]
        for item in self._faq_repository.items[:15]:
            lines.append(f"Q: {item.question}\nA: {item.answer[:200]}...")
        return "\n\n".join(lines)

    async def answer(self, user_question: str) -> str:
        """Отправляет вопрос в OpenAI с контекстом организации и FAQ, возвращает ответ."""
        org_context = self._organization.context_for_ai()
        faq_context = self._build_faq_context()

        # Формируем пользовательское сообщение с полным контекстом
        user_content = (
            f"Контекст организации:\n{org_context}\n\n"
            f"{faq_context}\n\n"
            f"Вопрос жителя: {user_question}"
        )

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=800,
        )

        content = response.choices[0].message.content
        return content.strip() if content else "Извините, не удалось сформировать ответ."
