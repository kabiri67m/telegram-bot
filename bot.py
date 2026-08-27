import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask

# بارگذاری متغیرهای محیطی
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# وب‌سرور ساده برای Render
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is running on Render!"

# تابع اصلی ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات روی Render اجرا شد ✅")

def run_bot():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == "__main__":
    # ساخت حلقهٔ asyncio به‌صورت دستی برای محیط ابری
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(asyncio.to_thread(run_bot))

    # اجرای وب‌سرور برای Render
    port = int(os.environ.get("PORT", 5000))
    app_web.run(host="0.0.0.0", port=port)
