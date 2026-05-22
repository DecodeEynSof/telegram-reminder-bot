import pytest
from datetime import datetime, timedelta
from bot import add_reminder, get_due_reminders, delete_reminder, conn, cursor

def test_add_and_get_reminder():
    cursor.execute("DELETE FROM reminders")
    conn.commit()
    
    chat_id = 123456789
    text = "Тестовое напоминание"
    remind_time = (datetime.now() - timedelta(seconds=5)).strftime("%Y-%m-%d %H:%M:%S")
    
    add_reminder(chat_id, text, remind_time)
    
    reminders = get_due_reminders()
    assert len(reminders) >= 1
    assert reminders[0][2] == text

def test_delete_reminder():
    cursor.execute("DELETE FROM reminders")
    conn.commit()
    
    remind_time = (datetime.now() - timedelta(seconds=5)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO reminders (chat_id, text, remind_time) VALUES (?, ?, ?)",
        (123, "to delete", remind_time)
    )
    conn.commit()
    reminder_id = cursor.lastrowid
    
    delete_reminder(reminder_id)
    
    cursor.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
    assert cursor.fetchone() is None
