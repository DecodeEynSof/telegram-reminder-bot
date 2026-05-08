#!/usr/bin/env python3
import sqlite3
import asyncio
import threading
import requests
import hashlib
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

translation_cache = {}

BOT_TOKEN = "8603632445:AAGhMcdv9wIM1R88-ZkR7Z5X7gksa4-D3Uk"

conn = sqlite3.connect('reminders.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, text TEXT, remind_time TEXT)')
conn.commit()

def add_reminder(chat_id, text, remind_time):
    cursor.execute('INSERT INTO reminders (chat_id, text, remind_time) VALUES (?, ?, ?)', (chat_id, text, remind_time))
    conn.commit()

def get_due_reminders():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('SELECT id, chat_id, text, remind_time FROM reminders WHERE remind_time <= ?', (now,))
    return cursor.fetchall()

def delete_reminder(reminder_id):
    cursor.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
    conn.commit()

async def check_reminders(app):
    while True:
        reminders = get_due_reminders()
        for rid, chat_id, text, remind_time in reminders:
            try:
                await app.bot.send_message(chat_id=chat_id, text=f"🔔 Напоминание: {text}")
                delete_reminder(rid)
            except Exception as e:
                print(f"Ошибка: {e}")
        await asyncio.sleep(10)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я бот-напоминатель.\n\n/remind через 10 минут чай\n/remind в 15:30 встреча")

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Пример: /remind через 10 минут чай")
        return
    text = ' '.join(context.args)
    chat_id = update.effective_chat.id
    remind_time = None
    now = datetime.now()
    if text.startswith("через"):
        parts = text.split()
        if len(parts) >= 3:
            try:
                value = int(parts[1])
                if "минут" in parts[2]:
                    remind_time = now + timedelta(minutes=value)
                elif "час" in parts[2]:
                    remind_time = now + timedelta(hours=value)
                text = ' '.join(parts[3:])
            except:
                pass
    elif text.startswith("в"):
        parts = text.split()
        if len(parts) >= 2:
            try:
                hour, minute = map(int, parts[1].split(':'))
                remind_time = now.replace(hour=hour, minute=minute, second=0)
                if remind_time <= now:
                    remind_time += timedelta(days=1)
                text = ' '.join(parts[2:])
            except:
                pass
    if not remind_time:
        await update.message.reply_text("❌ Не понял время")
        return
    add_reminder(chat_id, text, remind_time.strftime("%Y-%m-%d %H:%M:%S"))
    await update.message.reply_text(f"✅ Напоминание на {remind_time.strftime('%H:%M')}: {text}")
def get_neuroscience_news():
    try:
        url = "https://www.news-medical.net/neuroscience/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_list = []
        articles = soup.select('h2 a')[:5]
        for article in articles:
            title = article.text.strip()
            link = article.get('href')
            if link and not link.startswith('http'):
                link = 'https://www.news-medical.net' + link
            news_list.append(f"• [{title}]({link})")
        if news_list:
            return "🧠 Нейробиология: последние исследования\n" + "\n".join(news_list) + "\n\n"
        else:
            return "🧠 Новостей нейробиологии не найдено\n\n"
    except Exception as e:
        return f"🧠 Ошибка парсинга нейробиологии: {e}\n\n"
def get_robotics_news():
    try:
        url = "https://habr.com/ru/rss/topics/robotics/"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.content, 'lxml')
        news = []
        for item in soup.find_all('item')[:5]:
            title = item.title.text if item.title else ""
            link = item.link.text if item.link else ""
            if title:
                news.append(f"• [{title}]({link})")
        if news:
            return "🤖 Новости робототехники\n" + "\n".join(news) + "\n\n"
        return "🤖 Новостей робототехники не найдено\n\n"
    except:
        return "🤖 Не удалось загрузить новости робототехники\n\n"
def get_weather():
    try:
        city = "Zelenograd"
        api_key = ""  # Пока оставим пустым, сделаем бесплатный ключ позже
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            description = data['weather'][0]['description']
            return f"🌤 Погода в Зеленограде\nТемпература: {temp}°C (ощущается как {feels_like}°C)\n{description}\n"
        else:
            return "🌤 Не удалось получить погоду\n"
    except Exception as e:
        return f"🌤 Ошибка погоды: {e}\n"


async def translate_to_russian(text, max_length=1500):
    if len(text) > max_length:
        text = text[:max_length] + "..."

    text_hash = hashlib.md5(text.encode()).hexdigest()
    if text_hash in translation_cache:
        return translation_cache[text_hash]

    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": "en|ru"}
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            translated = data.get("responseData", {}).get("translatedText", text)
            result = translated
        else:
            result = f"[Не удалось перевести]\n{text}"

        if len(translation_cache) > 100:
            translation_cache.clear()
        translation_cache[text_hash] = result
        return result
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return f"[Оригинал, перевод не удался]\n{text}"

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Собираю погоду и новости... Подождите 10-15 секунд.")

    result = ""

    # ========== ПОГОДА (Open-Meteo) ==========
    try:
        lat = 55.999
        lon = 37.190
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=Europe/Moscow"
        response = requests.get(weather_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            current = data.get('current_weather', {})
            temp = current.get('temperature', 'Нет данных')
            wind = current.get('windspeed', 'Нет данных')
            result += f"🌤 Погода в Зеленограде\nТемпература: {temp}°C\nВетер: {wind} м/с\n\n"
        else:
            result += "🌤 Не удалось получить погоду\n\n"
    except Exception as e:
        result += "🌤 Ошибка погоды\n\n"

    # ========== НОВОСТИ (NewsAPI) ==========
    NEWSAPI_KEY = "0498d86f0ff84d01b969e93e16b4549d"
    topics = [
        "robotics", "quantum physics", "neuroscience", "biomedical engineering",
        "astrophysics", "virology", "molecular biology", "microelectronics",
        "programming", "artificial intelligence", "genetics", "immunology",
        "oceanology", "ornithology"
    ]

    result += "🔬 Научные новости\n\n"

    for topic in topics:
        try:
            url = f"https://newsapi.org/v2/everything?q={topic}&language=en&pageSize=1&apiKey={NEWSAPI_KEY}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                if articles:
                    title = articles[0].get('title', 'Без названия')
                    link = articles[0].get('url', '#')
                    result += f"{topic.upper()}\n• [{title}]({link})\n\n"
                else:
                    result += f"{topic.upper()}\nНовостей нет\n\n"
            else:
                result += f"{topic.upper()}\nОшибка API (код {response.status_code})\n\n"
        except Exception as e:
            result += f"{topic.upper()}\nОшибка: {str(e)[:30]}\n\n"
    await update.message.reply_text(result, parse_mode="Markdown", disable_web_page_preview=True)

async def summarize_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    news_id = query.data.replace("summarize_", "")
    news_data = context.bot_data.get('news_cache', {}).get(news_id)

    if not news_data:
        await query.edit_message_text("❌ Новость не найдена. Попробуйте /news заново.")
        return

    title = news_data['title']
    description = news_data['description']
    link = news_data['link']

    await query.edit_message_text(f"🔄 Перевожу: {title}...", parse_mode="Markdown")

    translated_title = await translate_to_russian(title)
    translated_desc = await translate_to_russian(description)

    await query.edit_message_text(
        f"{translated_title}\n\n{translated_desc}\n\n🔗 [Читать оригинал]({link})",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("remind", remind))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CallbackQueryHandler(summarize_callback, pattern="^summarize_"))

    loop = asyncio.new_event_loop()
    def run_checker():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(check_reminders(app))
    threading.Thread(target=run_checker, daemon=True).start()

    print("🤖 Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
