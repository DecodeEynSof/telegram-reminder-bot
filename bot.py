#!/usr/bin/env python3
import sqlite3
import asyncio
import threading
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

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

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("remind", remind))

    loop = asyncio.new_event_loop()
    def run_checker():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(check_reminders(app))
    threading.Thread(target=run_checker, daemon=True).start()

    print("🤖 Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
