"""Обработчики slash-команд и построение inline-клавиатур главного меню."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.services.faq import FAQRepository
from bot.services.organization import OrganizationService

# Текст приветствия при команде /start (без реальных персональных данных)
WELCOME_TEXT = (
    "Здравствуйте! Я — ассистент *ТСН (Ж) «Пример»* "
    "(г. Примерный, микрорайон Центральный 1).\n\n"
    "Помогу ответить на общие вопросы о деятельности товарищества, "
    "контактах, взносах, собраниях и содержании дома.\n\n"
    "Выберите раздел или просто напишите свой вопрос."
)

# Справка по доступным командам бота
HELP_TEXT = (
    "📖 *Справка по командам:*\n\n"
    "/start — приветствие и меню\n"
    "/help — эта справка\n"
    "/faq — популярные вопросы\n"
    "/contacts — контакты и руководство\n"
    "/dispatcher — диспетчерская\n"
    "/schedule — график работы сотрудников\n\n"
    "Также вы можете написать вопрос обычным сообщением — "
    "я постараюсь найти ответ в базе знаний или сформулировать его с помощью ИИ.\n\n"
    "При необходимости я ссылаюсь на *ГК РФ*, *ЖК РФ* и другие нормативные акты."
)


def build_main_menu() -> InlineKeyboardMarkup:
    """Формирует главное inline-меню с четырьмя разделами."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📋 Популярные вопросы", callback_data="menu:faq"),
                InlineKeyboardButton("📞 Контакты", callback_data="menu:contacts"),
            ],
            [
                InlineKeyboardButton("🚨 Диспетчерская", callback_data="menu:dispatcher"),
                InlineKeyboardButton("📅 График работы", callback_data="menu:schedule"),
            ],
        ]
    )


def build_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с одной кнопкой возврата в главное меню."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("◀️ Главное меню", callback_data="menu:main")]]
    )


def build_faq_answer_keyboard(category_id: str) -> InlineKeyboardMarkup:
    """Клавиатура после ответа на FAQ: назад к категории и в главное меню."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("◀️ К вопросам категории", callback_data=f"faq_cat:{category_id}")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="menu:main")],
        ]
    )


def build_text_answer_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после текстового ответа (поиск, AI, «не найдено»)."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📋 Популярные вопросы", callback_data="menu:faq")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="menu:main")],
        ]
    )


def build_faq_categories_keyboard(faq_repo: FAQRepository) -> InlineKeyboardMarkup:
    """Строит клавиатуру со списком категорий FAQ и кнопкой «Главное меню»."""
    buttons = [
        [InlineKeyboardButton(title, callback_data=f"faq_cat:{cat_id}")]
        for cat_id, title in faq_repo.list_categories()
    ]
    buttons.append([InlineKeyboardButton("◀️ Главное меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(buttons)


def build_faq_items_keyboard(faq_repo: FAQRepository, category_id: str) -> InlineKeyboardMarkup:
    """Строит клавиатуру с вопросами выбранной категории FAQ."""
    items = faq_repo.items_by_category(category_id)
    buttons = [
        [InlineKeyboardButton(item.question[:60], callback_data=f"faq_item:{item.id}")]
        for item in items
    ]
    buttons.append([InlineKeyboardButton("◀️ К категориям", callback_data="menu:faq")])
    return InlineKeyboardMarkup(buttons)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветствие и главное меню по команде /start."""
    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=build_main_menu(),
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет справку по командам по команде /help."""
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает список категорий FAQ по команде /faq."""
    faq_repo: FAQRepository = context.bot_data["faq_repo"]
    await update.message.reply_text(
        "Выберите категорию вопросов:",
        reply_markup=build_faq_categories_keyboard(faq_repo),
    )


async def contacts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет контакты руководства и офиса по команде /contacts."""
    org_service: OrganizationService = context.bot_data["org_service"]
    await update.message.reply_text(
        org_service.format_contacts(),
        reply_markup=build_back_to_main_keyboard(),
        parse_mode="Markdown",
    )


async def dispatcher_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет информацию о диспетчерской по команде /dispatcher."""
    org_service: OrganizationService = context.bot_data["org_service"]
    await update.message.reply_text(
        org_service.format_dispatcher(),
        reply_markup=build_back_to_main_keyboard(),
        parse_mode="Markdown",
    )


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет график работы сотрудников по команде /schedule."""
    org_service: OrganizationService = context.bot_data["org_service"]
    await update.message.reply_text(
        org_service.format_schedule(),
        reply_markup=build_back_to_main_keyboard(),
        parse_mode="Markdown",
    )
