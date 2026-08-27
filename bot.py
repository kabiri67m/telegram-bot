import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# تنظیم لاگ برای دیباگ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# دستور start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["سلام", "کمک"], ["راهنما", "خروج"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("سلام محمد! 👋 ربات آماده‌ست.", reply_markup=reply_markup)

# دستور help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("دستورات موجود:\n/start - شروع ربات\n/help - راهنما\nو پیام‌های متنی مثل سلام، کمک، خروج.")

# پاسخ به پیام‌های متنی
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "سلام" in text:
        await update.message.reply_text("سلام! حالت چطوره؟ 😊")
    elif "کمک" in text or "راهنما" in text:
        await update.message.reply_text("این ربات می‌تونه پیام‌ها رو جواب بده و کیبورد نشون بده.")
    elif "خروج" in text:
        await update.message.reply_text("خدانگهدار 👋")
    else:
        await update.message.reply_text(f"پیام دریافت شد: {update.message.text}")

# مدیریت خطاها
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(msg="Exception while handling update:", exc_info=context.error)
    if update and hasattr(update, "message") and update.message:
        await update.message.reply_text("یک خطا رخ داد 🚨")

# اجرای ربات
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    app.add_error_handler(error_handler)

    print("ربات در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()
