"""Точка входа: сборка приложения Telegram и запуск бота в режиме polling."""

from __future__ import annotations

import logging

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from bot.config import get_settings
from bot.handlers.commands import (
    contacts_command,
    dispatcher_command,
    faq_command,
    help_command,
    schedule_command,
    start_command,
)
from bot.handlers.messages import handle_callback, handle_text_message
from bot.services.ai_assistant import AIAssistantService
from bot.services.faq import FAQRepository
from bot.services.organization import OrganizationService
from bot.services.search import FAQSearchService

# Базовая настройка логирования для отладки и мониторинга работы бота
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def create_application() -> Application:
    """Создаёт и настраивает экземпляр Telegram Application со всеми сервисами и обработчиками."""
    settings = get_settings()

    # Инициализация сервисов: FAQ, данные организации, нечёткий поиск
    faq_repo = FAQRepository(settings.faq_path)
    org_service = OrganizationService(settings.organization_path)
    search_service = FAQSearchService(faq_repo, threshold=settings.faq_match_threshold)

    # AI-ассистент подключается только при наличии ключа OpenAI
    ai_service = None
    if settings.openai_api_key:
        ai_service = AIAssistantService(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            organization=org_service,
            faq_repository=faq_repo,
        )
        logger.info("AI-ассистент включён (модель: %s)", settings.openai_model)
    else:
        logger.warning("OPENAI_API_KEY не задан — работа только по базе FAQ")

    # Сборка приложения Telegram с токеном бота и сетевыми настройками
    builder = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .connect_timeout(settings.telegram_connect_timeout)
        .read_timeout(settings.telegram_read_timeout)
        .get_updates_connect_timeout(settings.telegram_connect_timeout)
        .get_updates_read_timeout(settings.telegram_read_timeout)
    )

    if settings.telegram_proxy:
        builder = builder.proxy(settings.telegram_proxy).get_updates_proxy(
            settings.telegram_proxy
        )
        logger.info("Прокси для Telegram API: %s", settings.telegram_proxy)
    else:
        logger.warning(
            "TELEGRAM_PROXY не задан. Если бот падает с TimedOut, "
            "укажите локальный прокси VPN в .env (например http://127.0.0.1:7890)."
        )

    application = builder.build()

    # Сохраняем сервисы в bot_data — они доступны во всех обработчиках через context
    application.bot_data["faq_repo"] = faq_repo
    application.bot_data["org_service"] = org_service
    application.bot_data["search_service"] = search_service
    application.bot_data["ai_service"] = ai_service

    # Регистрация обработчиков команд, inline-кнопок и текстовых сообщений
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("faq", faq_command))
    application.add_handler(CommandHandler("contacts", contacts_command))
    application.add_handler(CommandHandler("dispatcher", dispatcher_command))
    application.add_handler(CommandHandler("schedule", schedule_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    return application


def main() -> None:
    """Запускает бота и начинает опрос обновлений от Telegram."""
    from telegram.error import NetworkError, TimedOut

    application = create_application()
    logger.info("Бот ТСН запущен (демо-режим)")
    try:
        application.run_polling(allowed_updates=["message", "callback_query"])
    except (TimedOut, NetworkError) as error:
        logger.error("Не удалось подключиться к Telegram Bot API: %s", error)
        logger.error(
            "Telegram Desktop и Bot API — разные протоколы. "
            "Если api.telegram.org недоступен, включите VPN и укажите TELEGRAM_PROXY в .env "
            "(например http://127.0.0.1:7890 или socks5://127.0.0.1:10808)."
        )
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
