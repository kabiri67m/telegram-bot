import logging
import os
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram bot is running!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [["سلام", "خداحافظ"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("سلام! من ربات حسابدار هستم 🚀", reply_markup=reply_markup)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if text == "سلام":
        await update.message.reply_text("سلام به روی ماهت 🌹")
    elif text == "خداحافظ":
        await update.message.reply_text("به امید دیدار 👋")
    else:
        await update.message.reply_text(f"پیام دریافت شد: {text}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling update:", exc_info=context.error)

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # اول Flask رو توی thread فرعی اجرا می‌کنیم
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # ربات رو توی main thread اجرا می‌کنیم (مهم)
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN پیدا نشد!")
        raise SystemExit("BOT_TOKEN تنظیم نشده")

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_error_handler(error_handler)

    logger.info("ربات در حال شروع polling...")
    application.run_polling(drop_pending_updates=True)
