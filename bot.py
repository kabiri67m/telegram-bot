import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask

# بارگذاری متغیرهای محیطی
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# وب‌سرور برای Render
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is running on Render!"

# هندلرهای ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام محمد! ربات روی Render اجرا شد ✅")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("پیامت رسید 👌")

async def run_bot():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

if __name__ == "__main__":
    # اجرای ربات در حلقهٔ asyncio اصلی (بدون Thread)
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())

    # اجرای Flask برای Render
    port = int(os.environ.get("PORT", 5000))
    app_web.run(host="0.0.0.0", port=port)
