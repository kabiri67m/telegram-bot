import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from flask import Flask

# بارگذاری متغیرهای محیطی
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# وب‌سرور برای Render
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is running on Render!"

# ============================
#  منوی دکمه‌دار حرفه‌ای
# ============================

def get_main_menu():
    return ReplyKeyboardMarkup(
        [
            ["📌 اطلاعات", "🛠 ابزارها"],
            ["📨 تماس با پشتیبانی", "❓ راهنما"]
        ],
        resize_keyboard=True
    )

# ============================
#  هندلر شروع (فقط همین!)
# ============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام محمد عزیز 🌟\nبه ربات خوش آمدی!",
        reply_markup=get_main_menu()
    )

# ============================
#  هندلر پیام‌های معمولی
# ============================

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📌 اطلاعات":
        await update.message.reply_text("اینجا بخش اطلاعات است 👇\nنسخه ربات: 1.0.0")

    elif text == "🛠 ابزارها":
        await update.message.reply_text("اینجا ابزارهای ربات قرار می‌گیرند 🔧")

    elif text == "📨 تماس با پشتیبانی":
        await update.message.reply_text("برای تماس با پشتیبانی پیام بده: @YourSupport")

    elif text == "❓ راهنما":
        await update.message.reply_text("اینجا راهنمای استفاده از ربات قرار می‌گیرد 📘")

    else:
        await update.message.reply_text("پیامت رسید 👌")

# ============================
#  اجرای ربات تلگرام
# ============================

async def run_bot():
    application = ApplicationBuilder().token(TOKEN).build()

    # فقط همین دو هندلر وجود دارند
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    while True:
        await asyncio.sleep(1)

# ============================
#  نقطهٔ شروع برنامه
# ============================

if __name__ == "__main__":
    from threading import Thread

    # اجرای Flask در Thread جدا برای Render
    Thread(
        target=lambda: app_web.run(
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 5000))
        )
    ).start()

    # اجرای ربات در حلقهٔ اصلی asyncio
    asyncio.run(run_bot())
