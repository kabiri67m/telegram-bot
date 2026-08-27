import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# فعال‌سازی لاگ برای دیباگ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

def main() -> None:
    # توکن رباتت رو اینجا بذار
    application = Application.builder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # هندلر خطا
    application.add_error_handler(error_handler)

    # اجرای ربات
    application.run_polling()

if __name__ == "__main__":
    main()
