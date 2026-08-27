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
#  منوی اصلی
# ============================

def main_menu():
    return ReplyKeyboardMarkup(
        [
            ["📌 اطلاعات", "🛠 ابزارها"],
            ["📨 پشتیبانی", "❓ راهنما"]
        ],
        resize_keyboard=True
    )

# ============================
#  زیرمنوی اطلاعات
# ============================

def info_menu():
    return ReplyKeyboardMarkup(
        [
            ["ℹ️ نسخه ربات", "👤 درباره ما"],
            ["⬅️ بازگشت"]
        ],
        resize_keyboard=True
    )

# ============================
#  زیرمنوی ابزارها
# ============================

def tools_menu():
    return ReplyKeyboardMarkup(
        [
            ["🧮 ماشین حساب", "📅 زمان"],
            ["⬅️ بازگشت"]
        ],
        resize_keyboard=True
    )

# ============================
#  هندلر شروع
# ============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام محمد عزیز 🌟\nبه ربات خوش آمدی!",
        reply_markup=main_menu()
    )

# ============================
#  هندلر پیام‌ها
# ============================

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # ---------------------------
    #  منوی اصلی
    # ---------------------------
    if text == "📌 اطلاعات":
        await update.message.reply_text(
            "زیرمنوی اطلاعات:",
            reply_markup=info_menu()
        )

    elif text == "🛠 ابزارها":
        await update.message.reply_text(
            "زیرمنوی ابزارها:",
            reply_markup=tools_menu()
        )

    elif text == "📨 پشتیبانی":
        await update.message.reply_text("برای پشتیبانی پیام بده: @YourSupport")

    elif text == "❓ راهنما":
        await update.message.reply_text("اینجا راهنمای استفاده از ربات قرار می‌گیرد 📘")

    # ---------------------------
    #  زیرمنوی اطلاعات
    # ---------------------------
    elif text == "ℹ️ نسخه ربات":
        await update.message.reply_text("نسخه فعلی ربات: 1.0.0")

    elif text == "👤 درباره ما":
        await update.message.reply_text("این ربات توسط محمد ساخته شده است 🌟")

    # ---------------------------
    #  زیرمنوی ابزارها
    # ---------------------------
    elif text == "🧮 ماشین حساب":
        await update.message.reply_text("ماشین حساب فعلاً فعال نیست 🔧")

    elif text == "📅 زمان":
        await update.message.reply_text("زمان فعلی: به‌زودی اضافه می‌شود ⏳")

    # ---------------------------
    #  بازگشت
    # ---------------------------
    elif text == "⬅️ بازگشت":
        await update.message.reply_text(
            "بازگشت به منوی اصلی:",
            reply_markup=main_menu()
        )

    # ---------------------------
    #  پیام‌های دیگر
    # ---------------------------
    else:
        await update.message.reply_text("پیامت رسید 👌")

# ============================
#  اجرای ربات تلگرام
# ============================

async def run_bot():
    application = ApplicationBuilder().token(TOKEN).build()

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

    Thread(
        target=lambda: app_web.run(
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 5000))
        )
    ).start()

    asyncio.run(run_bot())
