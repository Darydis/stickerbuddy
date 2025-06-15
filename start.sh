#!/usr/bin/env bash
set -e

# 1. Устанавливаем зависимости
pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install --no-cache-dir -r requirements.txt
fi

# 2. Проверяем переменные окружения
: "${TELEGRAM_TOKEN:?не задано TELEGRAM_TOKEN}"
: "${OPENAI_API_KEY:?не задан OPENAI_API_KEY}"

# 3. Запускаем бота
exec python bot.py
