import logging
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import os
import threading

# فعال‌سازی لاگ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app برای باز کردن پورت
app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram bot is running!"

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [["سلام", "خداحافظ"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("سلام! من ربات شماره دو هستم 🚀", reply_markup=reply_markup)

# پاسخ به پیام‌های متنی
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text_received = update.message.text
    if text_received == "سلام":
        await update.message.reply_text("سلام به روی ماهت 🌹")
    elif text_received == "خداحافظ":
        await update.message.reply_text("به امید دیدار 👋")
    else:
        await update.message.reply_text(f"پیام دریافت شد: {text_received}")

# هندل خطاها
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling update:", exc_info=context.error)

def run_bot():
    token = os.environ.get("BOT_TOKEN")  # توکن رو در Environment Variable بذار
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_error_handler(error_handler)
    application.run_polling()

if __name__ == "__main__":
    # اجرای ربات در یک Thread جدا
    threading.Thread(target=run_bot).start()
    # اجرای Flask روی پورت Render
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
