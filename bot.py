import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
from flask import Flask

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# وب‌سرور Render
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Test version running!"

# پیام تستی
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("این نسخه جدید است — تست موفق")

# اجرای ربات
async def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(1)

# شروع
if __name__ == "__main__":
    from threading import Thread

    Thread(
        target=lambda: app_web.run(
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 5000))
        )
    ).start()

    asyncio.run(run_bot())
