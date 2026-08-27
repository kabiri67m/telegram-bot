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

async def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("Starting bot polling...")

    # به‌جای run_polling (که خودش حلقه رو مدیریت می‌کنه)، همه‌چیز رو دستی کنترل می‌کنیم:
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

if __name__ == "__main__":
    # اجرای Flask در Thread جدا تا Render پورت رو چک کنه
    from threading import Thread
    Thread(target=lambda: app_web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()

    # اجرای ربات در حلقهٔ اصلی، بدون nested loop
    asyncio.run(main())
