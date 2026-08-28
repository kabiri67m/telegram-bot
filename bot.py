import logging
import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات فعال است!")

async def echo_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هر پیامی که توی گروه یا خصوصی بیاد جواب می‌ده (برای تست)"""
    chat_type = update.effective_chat.type
    text = update.message.text or "پیام غیرمتنی"
    
    await update.message.reply_text(
        f"دریافت شد ✅\n"
        f"نوع چت: {chat_type}\n"
        f"متن: {text}"
    )
    logger.info(f"پیام دریافت شد از {chat_type}: {text}")

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise SystemExit("BOT_TOKEN تنظیم نشده")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, echo_all))

    logger.info("ربات تستی شروع شد...")
    application.run_polling(drop_pending_updates=True, allowed_updates=["message", "callback_query", "chat_member"])
