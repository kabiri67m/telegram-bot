import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from config import BOT_TOKEN, TELEGRAM_PROXY, OWNER_ID
from logger import logger
from database import init_database
from filters import add_filter, remove_filter, get_filters
from roles import set_role, get_role, remove_role
from flood import check_flood


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات مدیریت گروه فعال شد ✔")


async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not user:
        await update.message.reply_text("باید روی پیام فرد ریپلای کنید.")
        return

    # فرض بر اینه که add_warning در database یا فایل جدا تعریف شده
    count = add_warning(update.effective_chat.id, user.id)
    await update.message.reply_text(f"هشدار برای {user.first_name} — تعداد هشدارها: {count}")


async def addfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("مثال: /addfilter کلمه")
        return

    word = context.args[0]
    add_filter(update.effective_chat.id, word)
    await update.message.reply_text(f"کلمه '{word}' فیلتر شد.")


async def removefilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("مثال: /removefilter کلمه")
        return

    word = context.args[0]
    remove_filter(update.effective_chat.id, word)
    await update.message.reply_text(f"کلمه '{word}' حذف شد.")


async def setrole(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("مثال: /setrole user_id role")
        return

    user_id = int(context.args[0])
    role = context.args[1]
    set_role(update.effective_chat.id, user_id, role)
    await update.message.reply_text(f"نقش '{role}' برای کاربر {user_id} ثبت شد.")


async def removerole(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("مثال: /removerole user_id")
        return

    user_id = int(context.args[0])
    remove_role(update.effective_chat.id, user_id)
    await update.message.reply_text(f"نقش کاربر {user_id} حذف شد.")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return

    text = update.message.text.strip().lower()
    print(f"📩 پیام دریافت شد: {text}")

    for w in get_filters(update.effective_chat.id):
        if w in text:
            await update.message.delete()
            return

    if check_flood(update.effective_chat.id, update.message.from_user.id):
        await update.message.delete()
        return

    if "سلام" in text or "salam" in text:
        await update.message.reply_text("سلام محمد! 👋 خوش اومدی.")
        return

    if "خوبی" in text or "khobi" in text:
        await update.message.reply_text("من خوبم، تو چطوری؟ 😄")
        return

    await update.message.reply_text("دستور یا پیام‌ت رو متوجه نشدم، لطفاً دقیق‌تر بفرست.")


def main():
    init_database()

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .proxy(TELEGRAM_PROXY)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("addfilter", addfilter))
    app.add_handler(CommandHandler("removefilter", removefilter))
    app.add_handler(CommandHandler("setrole", setrole))
    app.add_handler(CommandHandler("removerole", removerole))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("ربات در حال اجراست...")
    app.run_polling()


if __name__ == "__main__":
    main()
