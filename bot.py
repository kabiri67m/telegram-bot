import os
import asyncio
import sqlite3
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

# ادمین دائمی (محمد)
MAIN_ADMIN_ID = 1190530645
ADMINS = set()

# وب‌سرور برای Render
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is running on Render!"

# ============================
#  توابع دیتابیس
# ============================

DB_PATH = "bot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # جدول ادمین‌ها
    c.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY
        )
    """)

    # جدول کاربران ثبت‌نام‌شده
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    """)

    # اطمینان از وجود ادمین اصلی
    c.execute("INSERT OR IGNORE INTO admins (id) VALUES (?)", (MAIN_ADMIN_ID,))

    conn.commit()

    # بارگذاری ادمین‌ها در حافظه
    c.execute("SELECT id FROM admins")
    rows = c.fetchall()
    for row in rows:
        ADMINS.add(row[0])

    conn.close()

def db_add_admin(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO admins (id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    ADMINS.add(user_id)

def db_remove_admin(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    ADMINS.discard(user_id)

def db_get_admins():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM admins")
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def db_add_user(user_id: int, name: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (id, name) VALUES (?, ?)", (user_id, name))
    conn.commit()
    conn.close()

def db_get_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

# ============================
#  منوها
# ============================

def main_menu():
    return ReplyKeyboardMarkup(
        [
            ["📌 اطلاعات", "🛠 ابزارها"],
            ["📨 پشتیبانی", "❓ راهنما"],
            ["⚙️ تنظیمات", "🔘 دکمه‌های Inline"],
            ["📝 ثبت‌نام", "👑 پنل مدیریت"]
        ],
        resize_keyboard=True
    )

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
            InlineKeyboardButton("📋 لیست ادمین‌ها", callback_data="list_admins"),
            InlineKeyboardButton("📋 لیست کاربران", callback_data="list_users")
        ],
        [
            InlineKeyboardButton("❌ بستن", callback_data="close_admin")
        ]
    ])

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

    # فرم ثبت‌نام - مرحله دوم
    if context.user_data.get("state") == "register_name":
        name = text.strip()
        if not name:
            await update.message.reply_text("لطفاً یک نام معتبر وارد کن.")
            return
        db_add_user(user_id, name)
        context.user_data["state"] = None
        await update.message.reply_text(
            f"ثبت‌نام انجام شد ✅\nنام: {name}",
            reply_markup=main_menu()
        )
        return

    # پنل مدیریت
    if text == "👑 پنل مدیریت":
        if user_id not in ADMINS:
            await update.message.reply_text("❌ شما ادمین نیستید!")
            return

        await update.message.reply_text(
            "پنل مدیریت:",
            reply_markup=admin_panel()
        )
        return

    # ثبت‌نام
    if text == "📝 ثبت‌نام":
        context.user_data["state"] = "register_name"
        await update.message.reply_text("لطفاً نام خودت را بفرست:")
        return

    # منوی اصلی
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

    # زیرمنوی اطلاعات
    elif text == "ℹ️ نسخه ربات":
        await update.message.reply_text("نسخه فعلی ربات: 4.0.0")

    elif text == "👤 درباره ما":
        await update.message.reply_text("این ربات توسط محمد ساخته شده است 🌟")

    elif text == "📊 وضعیت سرور":
        await update.message.reply_text("سرور فعال است ⚡")

    # زیرمنوی ابزارها
    elif text == "🧮 ماشین حساب":
        await update.message.reply_text("ماشین حساب فعلاً فعال نیست 🔧")

    elif text == "📅 زمان":
        await update.message.reply_text("زمان فعلی: به‌زودی اضافه می‌شود ⏳")

    elif text == "📝 تبدیل متن":
        await update.message.reply_text("بخش تبدیل متن به‌زودی فعال می‌شود 📝")

    elif text == "📷 پردازش تصویر":
        await update.message.reply_text("پردازش تصویر در نسخهٔ بعدی فعال می‌شود 📷")

    # زیرمنوی تنظیمات
    elif text == "🔔 اعلان‌ها":
        await update.message.reply_text("بخش اعلان‌ها فعال شد 🔔")

    elif text == "🌗 حالت شب":
        await update.message.reply_text("حالت شب فعال شد 🌙")

    elif text == "👥 مدیریت کاربران":
        await update.message.reply_text("زیرمنوی مدیریت کاربران:", reply_markup=user_manage_menu())

    # زیرمنوی مدیریت کاربران (نمونه)
    elif text == "➕ افزودن کاربر":
        await update.message.reply_text("افزودن کاربر: به‌زودی فعال می‌شود")

    elif text == "➖ حذف کاربر":
        await update.message.reply_text("حذف کاربر: به‌زودی فعال می‌شود")

    elif text == "📋 لیست کاربران":
        users = db_get_users()
        if not users:
            await update.message.reply_text("هیچ کاربری ثبت‌نام نکرده هنوز.")
        else:
            msg = "📋 لیست کاربران ثبت‌نام‌شده:\n"
            for uid, name in users:
                msg += f"- {name} (ID: {uid})\n"
            await update.message.reply_text(msg)

    # بازگشت
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

    if query.data == "send_msg":
        await query.edit_message_text("پیام ارسال شد 📤")

    elif query.data == "close":
        await query.edit_message_text("پنجره بسته شد ❌")

    elif query.data == "list_admins":
        admins = db_get_admins()
        msg = "📋 لیست ادمین‌ها:\n"
        for a in admins:
            msg += f"- ID: {a}\n"
        await query.edit_message_text(msg)

    elif query.data == "list_users":
        users = db_get_users()
        if not users:
            await query.edit_message_text("هیچ کاربری ثبت‌نام نکرده هنوز.")
        else:
            msg = "📋 لیست کاربران ثبت‌نام‌شده:\n"
            for uid, name in users:
                msg += f"- {name} (ID: {uid})\n"
            await query.edit_message_text(msg)

    elif query.data == "close_admin":
        await query.edit_message_text("پنل مدیریت بسته شد ❌")

# ============================
#  اجرای ربات
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
#  نقطه شروع
# ============================

if __name__ == "__main__":
    from threading import Thread

    init_db()

    Thread(
        target=lambda: app_web.run(
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 5000))
        )
    ).start()

    asyncio.run(run_bot())
