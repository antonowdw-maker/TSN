"""Обработка текстовых сообщений пользователя и нажатий inline-кнопок."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.commands import (
    WELCOME_TEXT,
    build_back_to_main_keyboard,
    build_faq_answer_keyboard,
    build_faq_categories_keyboard,
    build_faq_items_keyboard,
    build_main_menu,
    build_text_answer_keyboard,
)
from bot.services.ai_assistant import AIAssistantService
from bot.services.faq import FAQRepository
from bot.services.organization import OrganizationService
from bot.services.search import FAQSearchService

# Сообщение, когда ответ не найден ни в FAQ, ни через AI
NO_MATCH_TEXT = (
    "К сожалению, я не нашёл готового ответа на ваш вопрос.\n\n"
    "Попробуйте:\n"
    "• переформулировать вопрос;\n"
    "• воспользоваться разделом /faq;\n"
    "• обратиться в диспетчерскую (/dispatcher) или офис (/contacts)."
)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает произвольный текст: сначала ищет в FAQ, затем обращается к AI."""
    search_service: FAQSearchService = context.bot_data["search_service"]
    ai_service: AIAssistantService | None = context.bot_data.get("ai_service")

    user_text = update.message.text.strip()

    # Показываем индикатор «печатает», пока формируем ответ
    await update.message.chat.send_action("typing")

    # Пытаемся найти наиболее подходящий ответ в базе FAQ
    match = search_service.best_match(user_text)
    if match:
        await update.message.reply_text(
            match.item.answer,
            reply_markup=build_text_answer_keyboard(),
            parse_mode="Markdown",
        )
        return

    # Если FAQ не помог — используем AI-ассистент (если он настроен)
    if ai_service:
        answer = await ai_service.answer(user_text)
        await update.message.reply_text(
            answer,
            reply_markup=build_text_answer_keyboard(),
            parse_mode="Markdown",
        )
        return

    # Ни FAQ, ни AI не дали ответа
    await update.message.reply_text(
        NO_MATCH_TEXT,
        reply_markup=build_text_answer_keyboard(),
        parse_mode="Markdown",
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Маршрутизирует нажатия inline-кнопок: меню, категории FAQ, ответы."""
    query = update.callback_query
    await query.answer()

    faq_repo: FAQRepository = context.bot_data["faq_repo"]
    org_service: OrganizationService = context.bot_data["org_service"]
    data = query.data or ""

    # Главное меню и разделы
    if data == "menu:main":
        await query.edit_message_text(
            WELCOME_TEXT,
            reply_markup=build_main_menu(),
            parse_mode="Markdown",
        )
        return

    if data == "menu:faq":
        await query.edit_message_text(
            "Выберите категорию вопросов:",
            reply_markup=build_faq_categories_keyboard(faq_repo),
        )
        return

    if data == "menu:contacts":
        await query.edit_message_text(
            org_service.format_contacts(),
            reply_markup=build_back_to_main_keyboard(),
            parse_mode="Markdown",
        )
        return

    if data == "menu:dispatcher":
        await query.edit_message_text(
            org_service.format_dispatcher(),
            reply_markup=build_back_to_main_keyboard(),
            parse_mode="Markdown",
        )
        return

    if data == "menu:schedule":
        await query.edit_message_text(
            org_service.format_schedule(),
            reply_markup=build_back_to_main_keyboard(),
            parse_mode="Markdown",
        )
        return

    # Выбор категории FAQ — показываем список вопросов
    if data.startswith("faq_cat:"):
        category_id = data.removeprefix("faq_cat:")
        await query.edit_message_text(
            "Выберите вопрос:",
            reply_markup=build_faq_items_keyboard(faq_repo, category_id),
        )
        return

    # Выбор конкретного вопроса — показываем ответ с навигацией
    if data.startswith("faq_item:"):
        item_id = data.removeprefix("faq_item:")
        item = faq_repo.get_by_id(item_id)
        if item:
            await query.edit_message_text(
                f"*{item.question}*\n\n{item.answer}",
                reply_markup=build_faq_answer_keyboard(item.category_id),
                parse_mode="Markdown",
            )
