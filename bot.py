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

# ============================
#  تنظیمات پایه
# ============================
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

MAIN_ADMIN_ID = 1190530645  # محمد
ADMINS = set()

DB_PATH = "bot.db"

app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Commercial bot running!"

# ============================
#  دیتابیس
# ============================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            registered_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            user_id INTEGER PRIMARY KEY,
            night_mode INTEGER DEFAULT 0,
            notifications INTEGER DEFAULT 1
        )
    """)

    c.execute("INSERT OR IGNORE INTO admins (id) VALUES (?)", (MAIN_ADMIN_ID,))
    conn.commit()

    c.execute("SELECT id FROM admins")
    rows = c.fetchall()
    for row in rows:
        ADMINS.add(row[0])

    conn.close()

def db_add_user(user_id: int, name: str, ts: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO users (id, name, registered_at) VALUES (?, ?, ?)",
        (user_id, name, ts)
    )
    conn.commit()
    conn.close()

def db_get_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, registered_at FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

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
    return [r[0] for r in rows]

def db_toggle_setting(user_id: int, field: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO settings (user_id) VALUES (?)", (user_id,))
    c.execute(f"SELECT {field} FROM settings WHERE user_id = ?", (user_id,))
    val = c.fetchone()[0]
    new_val = 0 if val == 1 else 1
    c.execute(f"UPDATE settings SET {field} = ? WHERE user_id = ?", (new_val, user_id))
    conn.commit()
    conn.close()
    return new_val

# ============================
#  منوها
# ============================
def main_menu():
    return ReplyKeyboardMarkup(
        [
            ["📌 اطلاعات", "🛠 ابزارها"],
            ["📝 ثبت‌نام", "📨 پشتیبانی"],
            ["⚙️ تنظیمات", "🔘 دکمه‌های Inline"],
            ["👑 پنل مدیریت"]
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
            ["📋 لیست کاربران"],
            ["⬅️ بازگشت تنظیمات"]
        ],
        resize_keyboard=True
    )

def admin_panel():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 لیست ادمین‌ها", callback_data="list_admins"),
            InlineKeyboardButton("📋 لیست کاربران", callback_data="list_users")
        ],
        [
            InlineKeyboardButton("➕ افزودن خودم به ادمین‌ها", callback_data="self_add_admin"),
            InlineKeyboardButton("➖ حذف خودم از ادمین‌ها", callback_data="self_remove_admin")
        ],
        [
            InlineKeyboardButton("❌ بستن پنل", callback_data="close_admin")
        ]
    ])

def inline_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔗 لینک نمونه", url="https://google.com"),
            InlineKeyboardButton("📤 تست Callback", callback_data="send_msg")
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
        "سلام محمد عزیز 🌟\nاین نسخهٔ حرفه‌ای تجاری رباته.",
        reply_markup=main_menu()
    )

# ============================
#  هندلر پیام‌ها
# ============================
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    # فرم ثبت‌نام – مرحلهٔ نام
    if context.user_data.get("state") == "register_name":
        name = text.strip()
        if not name:
            await update.message.reply_text("لطفاً یک نام معتبر وارد کن.")
            return
        from datetime import datetime
        ts = datetime.utcnow().isoformat()
        db_add_user(user_id, name, ts)
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
        await update.message.reply_text("پنل مدیریت:", reply_markup=admin_panel())
        return

    # ثبت‌نام
    if text == "📝 ثبت‌نام":
        context.user_data["state"] = "register_name"
        await update.message.reply_text("لطفاً نام خودت را بفرست:")
        return

    # منوی اصلی
    if text == "📌 اطلاعات":
        await update.message.reply_text("زیرمنوی اطلاعات:", reply_markup=info_menu())
        return

    if text == "🛠 ابزارها":
        await update.message.reply_text("زیرمنوی ابزارها:", reply_markup=tools_menu())
        return

    if text == "⚙️ تنظیمات":
        await update.message.reply_text("زیرمنوی تنظیمات:", reply_markup=settings_menu())
        return

    if text == "📨 پشتیبانی":
        await update.message.reply_text("برای پشتیبانی پیام بده: @YourSupport")
        return

    if text == "❓ راهنما":
        await update.message.reply_text("اینجا می‌تونه راهنمای تجاری رباتت باشه 📘")
        return

    if text == "🔘 دکمه‌های Inline":
        await update.message.reply_text("نمونه دکمه‌های Inline:", reply_markup=inline_menu())
        return

    # زیرمنوی اطلاعات
    if text == "ℹ️ نسخه ربات":
        await update.message.reply_text("نسخه فعلی ربات: 1.0.0 (Commercial Demo)")
        return

    if text == "👤 درباره ما":
        await update.message.reply_text("این ربات برای نمایش نمونهٔ کار تجاری محمد ساخته شده است 🌟")
        return

    if text == "📊 وضعیت سرور":
        await update.message.reply_text("سرور فعال است و بدون مشکل کار می‌کند ⚡")
        return

    # زیرمنوی ابزارها (نمونه)
    if text == "🧮 ماشین حساب":
        await update.message.reply_text("ماشین حساب تجاری بعداً اضافه می‌شود 🔧")
        return

    if text == "📅 زمان":
        await update.message.reply_text("نمایش زمان سرور بعداً اضافه می‌شود ⏳")
        return

    if text == "📝 تبدیل متن":
        await update.message.reply_text("ماژول تبدیل متن در نسخهٔ بعدی فعال می‌شود 📝")
        return

    if text == "📷 پردازش تصویر":
        await update.message.reply_text("پردازش تصویر برای نسخهٔ پیشرفته‌تر در نظر گرفته شده 📷")
        return

    # تنظیمات
    if text == "🔔 اعلان‌ها":
        val = db_toggle_setting(user_id, "notifications")
        status = "فعال ✅" if val == 1 else "غیرفعال ❌"
        await update.message.reply_text(f"وضعیت اعلان‌ها: {status}")
        return

    if text == "🌗 حالت شب":
        val = db_toggle_setting(user_id, "night_mode")
        status = "فعال ✅" if val == 1 else "غیرفعال ❌"
        await update.message.reply_text(f"حالت شب: {status}")
        return

    if text == "👥 مدیریت کاربران":
        await update.message.reply_text("زیرمنوی مدیریت کاربران:", reply_markup=user_manage_menu())
        return

    # مدیریت کاربران
    if text == "📋 لیست کاربران":
        users = db_get_users()
        if not users:
            await update.message.reply_text("هنوز هیچ کاربری ثبت‌نام نکرده.")
        else:
            msg = "📋 لیست کاربران ثبت‌نام‌شده:\n"
            for uid, name, ts in users:
                msg += f"- {name} (ID: {uid}) | {ts}\n"
            await update.message.reply_text(msg)
        return

    # بازگشت
    if text == "⬅️ بازگشت":
        await update.message.reply_text("بازگشت به منوی اصلی:", reply_markup=main_menu())
        return

    if text == "⬅️ بازگشت تنظیمات":
        await update.message.reply_text("بازگشت به تنظیمات:", reply_markup=settings_menu())
        return

    # سایر پیام‌ها
    await update.message.reply_text("پیامت رسید 👌")

# ============================
#  هندلر دکمه‌های Inline
# ============================
async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "send_msg":
        await query.edit_message_text("Callback تست شد 📤")
        return

    if query.data == "close":
        await query.edit_message_text("پنجره بسته شد ❌")
        return

    if query.data == "list_admins":
        admins = db_get_admins()
        msg = "📋 لیست ادمین‌ها:\n"
        for a in admins:
            mark = " (محمد)" if a == MAIN_ADMIN_ID else ""
            msg += f"- ID: {a}{mark}\n"
        await query.edit_message_text(msg)
        return

    if query.data == "list_users":
        users = db_get_users()
        if not users:
            await query.edit_message_text("هیچ کاربری ثبت‌نام نکرده هنوز.")
        else:
            msg = "📋 لیست کاربران ثبت‌نام‌شده:\n"
            for uid, name, ts in users:
                msg += f"- {name} (ID: {uid}) | {ts}\n"
            await query.edit_message_text(msg)
        return

    if query.data == "self_add_admin":
        db_add_admin(user_id)
        await query.edit_message_text("✔ شما به لیست ادمین‌ها اضافه شدید.")
        return

    if query.data == "self_remove_admin":
        if user_id == MAIN_ADMIN_ID:
            await query.edit_message_text("❌ ادمین اصلی قابل حذف نیست.")
        else:
            db_remove_admin(user_id)
            await query.edit_message_text("❌ شما از لیست ادمین‌ها حذف شدید.")
        return

    if query.data == "close_admin":
        await query.edit_message_text("پنل مدیریت بسته شد ❌")
        return

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
