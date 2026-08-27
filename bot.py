import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")  # فقط از Environment خونده می‌شود

app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is running!"

def main_menu():
    return ReplyKeyboardMarkup([["⬅️ بازگشت"]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 🌟", reply_markup=main_menu())

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "⬅️ بازگشت":
        await update.message.reply_text("بازگشت به منوی اصلی:", reply_markup=main_menu())
        return
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
    asyncio.run(run_bot())
