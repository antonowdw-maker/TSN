FROM python:3.12-slim

WORKDIR /app

# Зависимости проекта
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код бота и данные FAQ
COPY bot/ bot/
COPY data/ data/

# Бот работает в режиме polling (постоянное подключение к Telegram API)
CMD ["python", "-m", "bot.main"]
