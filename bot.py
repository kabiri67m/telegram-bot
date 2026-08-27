import os
import asyncio
import sqlite3
from datetime import datetime, UTC
from dotenv import load_dotenv
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from flask import Flask

# ============================
#  تنظیمات پایه
# ============================
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")  # فقط از Environment خونده می‌شود

MAIN_ADMIN_ID = 1190530645
ADMINS = set()

DB_PATH = "bot.db"

app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Commercial test bot running!"

# ============================
#  دیتابیس
# ============================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            registered_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            user_id INTEGER PRIMARY KEY,
            night_mode INTEGER DEFAULT 0,
            notifications INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    c.execute("INSERT OR IGNORE INTO admins (id) VALUES (?)", (MAIN_ADMIN_ID,))
    conn.commit()

    c.execute("SELECT id FROM admins")
    rows = c.fetchall()
    for row in rows:
        ADMINS.add(row[0])

    conn.close()

def db_add_user(user_id: int, name: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    ts = datetime.now(UTC).isoformat()
    c.execute(
        "INSERT OR REPLACE INTO users (id, name, registered_at) VALUES (?, ?, ?)",
        (user_id, name, ts)
    )
    conn.commit()
    conn.close()

def db_get_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, registered_at FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

# ============================
#  منوها
# ============================
def main_menu(user_id: int):
    buttons = [
        ["📌 اطلاعات", "🛠 ابزارها"],
        ["📝 ثبت‌نام", "🛒 ثبت سفارش"],
        ["💳 پرداخت تستی", "📨 پشتیبانی"],
        ["🔘 دکمه‌های Inline"]
    ]
    if user_id in ADMINS:
        buttons.append(["⚙️ تنظیمات"])
        buttons.append(["👑 پنل مدیریت"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# ============================
#  هندلر شروع
# ============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    name = user.first_name
    await update.message.reply_text(
        f"سلام {name} عزیز 🌟\nبه ربات خوش آمدی!",
        reply_markup=main_menu(user.id)
    )

# ============================
#  هندلر پیام‌ها
# ============================
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    # بازگشت
    if text == "⬅️ بازگشت":
        await update.message.reply_text("بازگشت به منوی اصلی:", reply_markup=main_menu(user_id))
        return

    # سایر پیام‌ها
    await update.message.reply_text("پیامت رسید 👌")

# ============================
#  اجرای ربات
# ============================
async def run_bot():
    init_db()
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

if __name__ == "__main__":
    asyncio.run(run_bot())
