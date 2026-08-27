from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

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
#  هندلر شروع
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
