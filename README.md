# Telegram Reminder Bot

Бот для напоминаний с поддержкой базы данных SQLite и Docker.

## Команды

- /start — приветствие
- /remind через X минут текст — установить напоминание
- /remind в HH:MM текст — установить напоминание на время
- /news — научные новости и погода

## Запуск локально

`bash
git clone https://github.com/DecodeEynSof/telegram-reminder-bot.git
cd telegram-reminder-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py

## Запуск через Docker

`bash
docker build -t reminder-bot .
docker run -d --name reminder-bot reminder-bot

## Автотесты

`bash
pytest test_bot.py -v

## Стек

- Python 3.13
- python-telegram-bot
- SQLite
- pytest
- Docker
