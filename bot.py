import os
import asyncio
from dotenv import load_dotenv
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from flask import Flask

# بارگذاری متغیرهای محیطی
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# ادمین دائمی (تو)
MAIN_ADMIN = None  # بعد از اولین /start مقدارش ذخیره می‌شود
ADMINS = set()

# وب‌سرور برای Render
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is running on Render!"

# ============================
#  منوی اصلی
# ============================

def main_menu():
    return ReplyKeyboardMarkup(
        [
            ["📌 اطلاعات", "🛠 ابزارها"],
            ["📨 پشتیبانی", "❓ راهنما"],
            ["⚙️ تنظیمات", "🔘 دکمه‌های Inline"],
            ["👑 پنل مدیریت"]
        ],
        resize_keyboard=True
    )

# ============================
#  زیرمنوها
# ============================

def info_menu():
    return ReplyKeyboardMarkup(
        [
            ["ℹ️ نسخه ربات", "👤 درباره ما"],
            ["📊 وضعیت سرور"],
            ["⬅️ بازگشت"]
        ],
        resize_keyboard=True
    )

def tools_menu():
    return ReplyKeyboardMarkup(
        [
            ["🧮 ماشین حساب", "📅 زمان"],
            ["📝 تبدیل متن", "📷 پردازش تصویر"],
            ["⬅️ بازگشت"]
        ],
        resize_keyboard=True
    )

def settings_menu():
    return ReplyKeyboardMarkup(
        [
            ["🔔 اعلان‌ها", "🌗 حالت شب"],
            ["👥 مدیریت کاربران"],
            ["⬅️ بازگشت"]
        ],
        resize_keyboard=True
    )

def user_manage_menu():
    return ReplyKeyboardMarkup(
        [
            ["➕ افزودن کاربر", "➖ حذف کاربر"],
            ["📋 لیست کاربران"],
            ["⬅️ بازگشت تنظیمات"]
        ],
        resize_keyboard=True
    )

# ============================
#  پنل مدیریت (Inline)
# ============================

def admin_panel():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ افزودن ادمین", callback_data="add_admin"),
            InlineKeyboardButton("➖ حذف ادمین", callback_data="remove_admin")
        ],
        [
            InlineKeyboardButton("📋 لیست ادمین‌ها", callback_data="list_admins")
        ],
        [
            InlineKeyboardButton("❌ بستن", callback_data="close_admin")
        ]
    ])

# ============================
#  دکمه‌های Inline نمونه
# ============================

def inline_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔗 لینک سایت", url="https://google.com"),
            InlineKeyboardButton("📤 ارسال پیام", callback_data="send_msg")
        ],
        [
            InlineKeyboardButton("❌ بستن", callback_data="close")
        ]
    ])

# ============================
#  هندلر شروع
# ============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MAIN_ADMIN

    user_id = update.message.from_user.id

    # اولین کسی که /start می‌زند → ادمین دائمی
    if MAIN_ADMIN is None:
        MAIN_ADMIN = user_id

    # همیشه تو را ادمین نگه می‌داریم
    ADMINS.add(MAIN_ADMIN)

    await update.message.reply_text(
        "سلام محمد عزیز 🌟\nبه ربات خوش آمدی!",
        reply_markup=main_menu()
    )

# ============================
#  هندلر پیام‌ها
# ============================

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    # ---------------------------
    #  پنل مدیریت
    # ---------------------------
    if text == "👑 پنل مدیریت":
        if user_id not in ADMINS:
            await update.message.reply_text("❌ شما ادمین نیستید!")
            return

        await update.message.reply_text(
            "پنل مدیریت:",
            reply_markup=admin_panel()
        )
        return

    # ---------------------------
    #  منوی اصلی
    # ---------------------------
    if text == "📌 اطلاعات":
        await update.message.reply_text("زیرمنوی اطلاعات:", reply_markup=info_menu())

    elif text == "🛠 ابزارها":
        await update.message.reply_text("زیرمنوی ابزارها:", reply_markup=tools_menu())

    elif text == "⚙️ تنظیمات":
        await update.message.reply_text("زیرمنوی تنظیمات:", reply_markup=settings_menu())

    elif text == "📨 پشتیبانی":
        await update.message.reply_text("برای پشتیبانی پیام بده: @YourSupport")

    elif text == "❓ راهنما":
        await update.message.reply_text("اینجا راهنمای استفاده از ربات قرار می‌گیرد 📘")

    elif text == "🔘 دکمه‌های Inline":
        await update.message.reply_text(
            "این هم نمونه دکمه‌های Inline:",
            reply_markup=inline_menu()
        )

    # ---------------------------
    #  زیرمنوی اطلاعات
    # ---------------------------
    elif text == "ℹ️ نسخه ربات":
        await update.message.reply_text("نسخه فعلی ربات: 3.0.0")

    elif text == "👤 درباره ما":
        await update.message.reply_text("این ربات توسط محمد ساخته شده است 🌟")

    elif text == "📊 وضعیت سرور":
        await update.message.reply_text("سرور فعال است ⚡")

    # ---------------------------
    #  زیرمنوی ابزارها
    # ---------------------------
    elif text == "🧮 ماشین حساب":
        await update.message.reply_text("ماشین حساب فعلاً فعال نیست 🔧")

    elif text == "📅 زمان":
        await update.message.reply_text("زمان فعلی: به‌زودی اضافه می‌شود ⏳")

    elif text == "📝 تبدیل متن":
        await update.message.reply_text("بخش تبدیل متن به‌زودی فعال می‌شود 📝")

    elif text == "📷 پردازش تصویر":
        await update.message.reply_text("پردازش تصویر در نسخهٔ بعدی فعال می‌شود 📷")

    # ---------------------------
    #  زیرمنوی تنظیمات
    # ---------------------------
    elif text == "🔔 اعلان‌ها":
        await update.message.reply_text("بخش اعلان‌ها فعال شد 🔔")

    elif text == "🌗 حالت شب":
        await update.message.reply_text("حالت شب فعال شد 🌙")

    elif text == "👥 مدیریت کاربران":
        await update.message.reply_text("زیرمنوی مدیریت کاربران:", reply_markup=user_manage_menu())

    # ---------------------------
    #  زیرمنوی مدیریت کاربران
    # ---------------------------
    elif text == "➕ افزودن کاربر":
        await update.message.reply_text("افزودن کاربر: به‌زودی فعال می‌شود")

    elif text == "➖ حذف کاربر":
        await update.message.reply_text("حذف کاربر: به‌زودی فعال می‌شود")

    elif text == "📋 لیست کاربران":
        await update.message.reply_text("لیست کاربران: به‌زودی فعال می‌شود")

    # ---------------------------
    #  دکمه‌های بازگشت
    # ---------------------------
    elif text == "⬅️ بازگشت":
        await update.message.reply_text("بازگشت به منوی اصلی:", reply_markup=main_menu())

    elif text == "⬅️ بازگشت تنظیمات":
        await update.message.reply_text("بازگشت به تنظیمات:", reply_markup=settings_menu())

    else:
        await update.message.reply_text("پیامت رسید 👌")

# ============================
#  هندلر دکمه‌های Inline
# ============================

async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # ---------------------------
    #  دکمه‌های نمونه
    # ---------------------------
    if query.data == "send_msg":
        await query.edit_message_text("پیام ارسال شد 📤")

    elif query.data == "close":
        await query.edit_message_text("پنجره بسته شد ❌")

    # ---------------------------
    #  پنل مدیریت
    # ---------------------------
    elif query.data == "add_admin":
        ADMINS.add(user_id)
        await query.edit_message_text("✔ شما به لیست ادمین‌ها اضافه شدید")

    elif query.data == "remove_admin":
        ADMINS.discard(user_id)
        await query.edit_message_text("❌ شما از لیست ادمین‌ها حذف شدید")

    elif query.data == "list_admins":
        admin_list = "\n".join(str(a) for a in ADMINS)
        await query.edit_message_text(f"📋 لیست ادمین‌ها:\n{admin_list}")

    elif query.data == "close_admin":
        await query.edit_message_text("پنل مدیریت بسته شد ❌")

# ============================
#  اجرای ربات تلگرام
# ============================

async def run_bot():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(CallbackQueryHandler(inline_handler))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    while True:
        await asyncio.sleep(1)

# ============================
#  نقطهٔ شروع برنامه
# ============================

if __name__ == "__main__":
    from threading import Thread

    Thread(
        target=lambda: app_web.run(
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 5000))
        )
    ).start()

    asyncio.run(run_bot())
