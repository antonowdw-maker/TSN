"""Тесты обработчиков команд, inline-меню и текстовых сообщений."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.commands import (
    HELP_TEXT,
    WELCOME_TEXT,
    build_back_to_main_keyboard,
    build_faq_answer_keyboard,
    build_faq_categories_keyboard,
    build_main_menu,
    build_text_answer_keyboard,
)
from bot.handlers.messages import handle_text_message
from bot.services.ai_assistant import AIAssistantService
from bot.services.faq import FAQRepository
from bot.services.organization import OrganizationService
from bot.services.search import FAQSearchService


@pytest.fixture
def mock_context(faq_repo: FAQRepository, org_service: OrganizationService) -> MagicMock:
    """Создаёт мок context с сервисами, как в реальном приложении."""
    context = MagicMock()
    context.bot_data = {
        "faq_repo": faq_repo,
        "org_service": org_service,
        "search_service": FAQSearchService(faq_repo, threshold=65),
        "ai_service": None,
    }
    return context


class TestUIComponents:
    def test_main_menu_has_four_buttons(self) -> None:
        """Главное меню состоит из двух рядов по две кнопки."""
        keyboard = build_main_menu()
        assert len(keyboard.inline_keyboard) == 2

    def test_faq_categories_keyboard(self, faq_repo: FAQRepository) -> None:
        """Клавиатура категорий содержит все категории плюс кнопку «Главное меню»."""
        keyboard = build_faq_categories_keyboard(faq_repo)
        assert len(keyboard.inline_keyboard) >= 9
        assert keyboard.inline_keyboard[-1][0].text == "◀️ Главное меню"
        assert keyboard.inline_keyboard[-1][0].callback_data == "menu:main"

    def test_welcome_text_mentions_tsn(self) -> None:
        """Приветствие содержит название демо-ТСН."""
        assert "Пример" in WELCOME_TEXT

    def test_help_text_lists_commands(self) -> None:
        """Справка перечисляет ключевые команды бота."""
        assert "/dispatcher" in HELP_TEXT
        assert "/schedule" in HELP_TEXT

    def test_back_to_main_keyboard(self) -> None:
        """Кнопка «Главное меню» доступна для навигации назад."""
        keyboard = build_back_to_main_keyboard()
        assert keyboard.inline_keyboard[0][0].callback_data == "menu:main"

    def test_faq_answer_keyboard_has_navigation(self) -> None:
        """После ответа FAQ есть возврат к категории и в главное меню."""
        keyboard = build_faq_answer_keyboard("payments")
        assert len(keyboard.inline_keyboard) == 2
        assert keyboard.inline_keyboard[0][0].callback_data == "faq_cat:payments"
        assert keyboard.inline_keyboard[1][0].callback_data == "menu:main"

    def test_text_answer_keyboard_has_navigation(self) -> None:
        """После текстового ответа есть FAQ и главное меню."""
        keyboard = build_text_answer_keyboard()
        assert keyboard.inline_keyboard[0][0].callback_data == "menu:faq"
        assert keyboard.inline_keyboard[1][0].callback_data == "menu:main"


class TestMessageHandler:
    @pytest.mark.asyncio
    async def test_faq_match_reply(self, mock_context: MagicMock) -> None:
        """При совпадении с FAQ бот отвечает текстом об оплате/взносах."""
        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "Как оплатить взносы?"
        update.message.reply_text = AsyncMock()
        update.message.chat.send_action = AsyncMock()

        await handle_text_message(update, mock_context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        reply_text = call_args[0][0]
        assert "оплат" in reply_text.lower() or "взнос" in reply_text.lower()
        assert call_args.kwargs.get("reply_markup") is not None

    @pytest.mark.asyncio
    async def test_no_match_without_ai(self, mock_context: MagicMock) -> None:
        """Без AI бот сообщает, что ответ не найден."""
        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "как приготовить борщ"
        update.message.reply_text = AsyncMock()
        update.message.chat.send_action = AsyncMock()

        await handle_text_message(update, mock_context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "не нашёл" in call_args[0][0].lower() or "не нашел" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_ai_fallback_when_no_faq_match(
        self,
        faq_repo: FAQRepository,
        org_service: OrganizationService,
    ) -> None:
        """При отсутствии FAQ-совпадения вызывается AI-ассистент."""
        ai_service = MagicMock(spec=AIAssistantService)
        ai_service.answer = AsyncMock(
            return_value="Для уточнения обратитесь в правление (ст. 45 ЖК РФ)."
        )

        context = MagicMock()
        context.bot_data = {
            "faq_repo": faq_repo,
            "org_service": org_service,
            "search_service": FAQSearchService(faq_repo, threshold=65),
            "ai_service": ai_service,
        }

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "какой порядок смены управляющей организации"
        update.message.reply_text = AsyncMock()
        update.message.chat.send_action = AsyncMock()

        await handle_text_message(update, context)

        ai_service.answer.assert_called_once()
        update.message.reply_text.assert_called_once()
        assert "ЖК РФ" in update.message.reply_text.call_args[0][0]


class TestApplicationCreation:
    def test_create_application_without_openai_key(self) -> None:
        """Приложение создаётся без OpenAI, если ключ не задан."""
        with patch.dict(
            "os.environ",
            {"TELEGRAM_BOT_TOKEN": "test-token-12345", "OPENAI_API_KEY": ""},
            clear=False,
        ):
            from bot.main import create_application

            with patch("bot.main.Application") as mock_app_class:
                mock_builder = MagicMock()
                mock_app_class.builder.return_value = mock_builder
                mock_builder.token.return_value = mock_builder
                mock_builder.build.return_value = MagicMock()

                app = create_application()

                assert app is not None
                mock_builder.token.assert_called_with("test-token-12345")

    def test_get_settings_raises_without_token(self) -> None:
        """Без TELEGRAM_BOT_TOKEN get_settings выбрасывает ValueError."""
        with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": ""}, clear=False):
            from bot.config import get_settings

            with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
                get_settings()
