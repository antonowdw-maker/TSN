# Telegram-ассистент ТСН (демо-версия)

Вежливый Telegram-бот для жителей товарищества собственников недвижимости (ТСН). Репозиторий содержит **демонстрационные данные** — перед развёртыванием замените их на актуальные сведения вашей организации.

## Возможности

- База из 20+ популярных вопросов и ответов по категориям
- Поиск ответов по смыслу (fuzzy matching)
- AI-ассистент на базе OpenAI GPT-4o-mini для вопросов вне FAQ
- Контакты руководства, диспетчерская, график работы сотрудников
- Ссылки на ГК РФ, ЖК РФ и другие нормативные акты

## Быстрый старт

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Настроить окружение
copy .env.example .env
# Укажите TELEGRAM_BOT_TOKEN (получить у @BotFather)
# Опционально: OPENAI_API_KEY для AI-ответов

# 3. Запустить бота
python -m bot.main
```

> **Если `TimedOut` на домашнем ПК:** Telegram Desktop и Bot API используют разные протоколы. С домашнего интернета `api.telegram.org` часто недоступен. **VPN не обязателен** — см. раздел [Запуск без VPN](#запуск-без-vpn) ниже.

## Запуск без VPN

Бот должен работать **на сервере**, где доступен `api.telegram.org`. С вашего компьютера можно только разрабатывать и запускать тесты (`pytest`).

### Вариант 1 — VPS (рекомендуется, ~300–500 ₽/мес)

1. Арендуйте VPS (Timeweb Cloud, Selectel, REG.RU, Hetzner и т.п.).
2. Подключитесь по SSH и установите Docker, либо Python 3.12.
3. Склонируйте репозиторий:
   ```bash
   git clone https://github.com/antonowdw-maker/TSN.git
   cd TSN
   ```
4. Создайте `.env` с токеном:
   ```bash
   cp .env.example .env
   nano .env   # TELEGRAM_BOT_TOKEN=...
   ```
5. Запуск через Docker:
   ```bash
   docker build -t tsn-bot .
   docker run -d --name tsn-bot --env-file .env --restart unless-stopped tsn-bot
   ```
   Или без Docker:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python -m bot.main
   ```
6. Проверьте бота в Telegram: `/start`.

`TELEGRAM_PROXY` на сервере обычно **не нужен**.

### Вариант 2 — бесплатный PaaS (для теста)

Подключите GitHub-репозиторий к [Render](https://render.com) или [Railway](https://railway.app):

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `python -m bot.main`
- **Environment:** `TELEGRAM_BOT_TOKEN`, опционально `OPENAI_API_KEY`

Минус бесплатных тарифов: сервис может «засыпать», бот отвечает с задержкой.

### Вариант 3 — локально только разработка

| На вашем ПК | На сервере в облаке |
|-------------|---------------------|
| `pytest -v` — тесты | `python -m bot.main` — живой бот |
| правка `data/*.json` | бот работает 24/7 |
| правка кода | после `git push` — обновление на сервере |

### Если всё же нужен прокси (опционально)

Только если сервер тоже не достучится до Telegram:

```env
TELEGRAM_PROXY=http://127.0.0.1:7890
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и главное меню |
| `/help` | Справка по командам |
| `/faq` | Популярные вопросы по категориям |
| `/contacts` | Контакты и руководство |
| `/dispatcher` | Диспетчерская и аварийный телефон |
| `/schedule` | График работы сотрудников |

## Настройка данных

- `data/faq.json` — база вопросов и ответов (можно дополнять)
- `data/organization.json` — контакты, телефоны, графики работы

> **Важно:** в репозитории используются **шаблонные** контактные данные (ФИО, адрес, телефоны, e-mail, ИНН/ОГРН). Перед публикацией для реального ТСН замените их в `data/organization.json` и `data/faq.json` на актуальные сведения. Не коммитьте файлы `.env` с реальными токенами.

## Тестирование

```bash
pytest -v
```

Тестовые кейсы описаны в `tests/TEST_CASES.md`.

## Структура проекта

```
ТСН/
├── bot/
│   ├── main.py              # Точка входа
│   ├── config.py            # Настройки
│   ├── handlers/            # Обработчики команд и сообщений
│   └── services/            # FAQ, поиск, AI, организация
├── data/
│   ├── faq.json             # База вопросов-ответов
│   └── organization.json    # Контакты и графики
├── tests/                   # Автотесты
├── requirements.txt
├── Dockerfile               # Для развёртывания на VPS
└── .env.example
```
