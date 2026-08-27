import os
import asyncio
import sqlite3
from datetime import datetime
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
    return "Commercial test bot running!"

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

    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            product TEXT,
            quantity INTEGER,
            status TEXT,
            created_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_id INTEGER,
            method TEXT,
            status TEXT,
            created_at TEXT
        )
    """)

    c.execute("INSERT OR IGNORE INTO admins (id) VALUES (?)", (MAIN_ADMIN_ID,))
    conn.commit()

    c.execute("SELECT id FROM admins")
    rows = c.fetchall()
    for row in rows:
        ADMINS.add(row[0])

    conn.close()

def db_add_user(user_id: int, name: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    ts = datetime.utcnow().isoformat()
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

def db_create_order(user_id: int, category: str, product: str, quantity: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    ts = datetime.utcnow().isoformat()
    c.execute(
        "INSERT INTO orders (user_id, category, product, quantity, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, category, product, quantity, "pending", ts)
    )
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id

def db_get_orders():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, user_id, category, product, quantity, status, created_at FROM orders")
    rows = c.fetchall()
    conn.close()
    return rows

def db_create_payment(user_id: int, order_id: int, method: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    ts = datetime.utcnow().isoformat()
    c.execute(
        "INSERT INTO payments (user_id, order_id, method, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, order_id, method, "paid_test", ts)
    )
    payment_id = c.lastrowid
    conn.commit()
    conn.close()
    return payment_id

def db_get_payments():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, user_id, order_id, method, status, created_at FROM payments")
    rows = c.fetchall()
    conn.close()
    return rows

# ============================
#  منوها
# ============================
def main_menu(user_id: int):
    buttons = [
        ["📌 اطلاعات", "🛠 ابزارها"],
        ["📝 ثبت‌نام", "🛒 ثبت سفارش"],
        ["💳 پرداخت تستی", "📨 پشتیبانی"],
        ["⚙️ تنظیمات", "🔘 دکمه‌های Inline"]
    ]
    if user_id in ADMINS:
        buttons.append(["👑 پنل مدیریت"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

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
            InlineKeyboardButton("📋 لیست سفارش‌ها", callback_data="list_orders"),
            InlineKeyboardButton("📋 لیست پرداخت‌ها", callback_data="list_payments")
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
#  فرم سفارش حرفه‌ای (Inline)
# ============================
def order_category_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📦 دسته A", callback_data="order_cat_A"),
            InlineKeyboardButton("📦 دسته B", callback_data="order_cat_B")
        ],
        [
            InlineKeyboardButton("❌ لغو سفارش", callback_data="order_cancel")
        ]
    ])

def order_product_keyboard(category: str):
    if category == "A":
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("محصول A1", callback_data="order_prod_A1"),
                InlineKeyboardButton("محصول A2", callback_data="order_prod_A2")
            ],
            [
                InlineKeyboardButton("⬅️ بازگشت به دسته", callback_data="order_back_cat"),
                InlineKeyboardButton("❌ لغو سفارش", callback_data="order_cancel")
            ]
        ])
    else:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("محصول B1", callback_data="order_prod_B1"),
                InlineKeyboardButton("محصول B2", callback_data="order_prod_B2")
            ],
            [
                InlineKeyboardButton("⬅️ بازگشت به دسته", callback_data="order_back_cat"),
                InlineKeyboardButton("❌ لغو سفارش", callback_data="order_cancel")
            ]
        ])

def order_quantity_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1", callback_data="order_qty_1"),
            InlineKeyboardButton("2", callback_data="order_qty_2"),
            InlineKeyboardButton("3", callback_data="order_qty_3")
        ],
        [
            InlineKeyboardButton("❌ لغو سفارش", callback_data="order_cancel")
        ]
    ])

def order_confirm_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✔ تأیید سفارش", callback_data="order_confirm"),
            InlineKeyboardButton("❌ لغو سفارش", callback_data="order_cancel")
        ]
    ])

# ============================
#  سیستم پرداخت تستی (Inline)
# ============================
def payment_method_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💳 کارت", callback_data="pay_method_card"),
            InlineKeyboardButton("💵 نقدی", callback_data="pay_method_cash")
        ],
        [
            InlineKeyboardButton("❌ لغو پرداخت", callback_data="pay_cancel")
        ]
    ])

def payment_confirm_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✔ تأیید پرداخت", callback_data="pay_confirm"),
            InlineKeyboardButton("❌ لغو پرداخت", callback_data="pay_cancel")
        ]
    ])

# ============================
#  هندلر شروع
# ============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    name = user.first_name
    await update.message.reply_text(
        f"سلام {name} عزیز 🌟\nبه ربات خوش آمدی!",
        reply_markup=main_menu(user.id)
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
        db_add_user(user_id, name)
        context.user_data["state"] = None
        await update.message.reply_text(
            f"ثبت‌نام انجام شد ✅\nنام: {name}",
            reply_markup=main_menu(user_id)
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

    # شروع سفارش حرفه‌ای
    if text == "🛒 ثبت سفارش":
        context.user_data["order"] = {}
        await update.message.reply_text(
            "لطفاً دستهٔ محصول را انتخاب کن:",
            reply_markup=order_category_keyboard()
        )
        return

    # شروع پرداخت تستی حرفه‌ای
    if text == "💳 پرداخت تستی":
        last_order_id = context.user_data.get("last_order_id")
        if not last_order_id:
            await update.message.reply_text("هیچ سفارشی برای پرداخت ثبت نشده.")
            return
        context.user_data["payment"] = {"order_id": last_order_id}
        await update.message.reply_text(
            "لطفاً روش پرداخت را انتخاب کن:",
            reply_markup=payment_method_keyboard()
        )
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
        await update.message.reply_text("نسخه فعلی ربات: 1.0.0 (Commercial Test)")
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
        await update.message.reply_text("بازگشت به منوی اصلی:", reply_markup=main_menu(user_id))
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
    data = query.data
    await query.answer()

    # دکمه‌های نمونه
    if data == "send_msg":
        await query.edit_message_text("Callback تست شد 📤")
        return

    if data == "close":
        await query.edit_message_text("پنجره بسته شد ❌")
        return

    # پنل مدیریت
    if data == "list_admins":
        admins = db_get_admins()
        msg = "📋 لیست ادمین‌ها:\n"
        for a in admins:
            mark = " (محمد)" if a == MAIN_ADMIN_ID else ""
            msg += f"- ID: {a}{mark}\n"
        await query.edit_message_text(msg)
        return

    if data == "list_users":
        users = db_get_users()
        if not users:
            await query.edit_message_text("هیچ کاربری ثبت‌نام نکرده هنوز.")
        else:
            msg = "📋 لیست کاربران ثبت‌نام‌شده:\n"
            for uid, name, ts in users:
                msg += f"- {name} (ID: {uid}) | {ts}\n"
            await query.edit_message_text(msg)
        return

    if data == "list_orders":
        orders = db_get_orders()
        if not orders:
            await query.edit_message_text("هیچ سفارشی ثبت نشده.")
        else:
            msg = "📋 لیست سفارش‌ها:\n"
            for oid, uid, cat, prod, qty, status, ts in orders:
                msg += f"- #{oid} | کاربر {uid} | {cat}/{prod} x{qty} | {status} | {ts}\n"
            await query.edit_message_text(msg)
        return

    if data == "list_payments":
        payments = db_get_payments()
        if not payments:
            await query.edit_message_text("هیچ پرداختی ثبت نشده.")
        else:
            msg = "📋 لیست پرداخت‌ها:\n"
            for pid, uid, oid, method, status, ts in payments:
                msg += f"- #{pid} | کاربر {uid} | سفارش #{oid} | {method} | {status} | {ts}\n"
            await query.edit_message_text(msg)
        return

    if data == "self_add_admin":
        db_add_admin(user_id)
        await query.edit_message_text("✔ شما به لیست ادمین‌ها اضافه شدید.")
        return

    if data == "self_remove_admin":
        if user_id == MAIN_ADMIN_ID:
            await query.edit_message_text("❌ ادمین اصلی قابل حذف نیست.")
        else:
            db_remove_admin(user_id)
            await query.edit_message_text("❌ شما از لیست ادمین‌ها حذف شدید.")
        return

    if data == "close_admin":
        await query.edit_message_text("پنل مدیریت بسته شد ❌")
        return

    # فرم سفارش حرفه‌ای
    order = context.user_data.get("order", {})

    if data == "order_cat_A":
        order["category"] = "A"
        context.user_data["order"] = order
        await query.edit_message_text(
            "دسته A انتخاب شد.\nلطفاً محصول را انتخاب کن:",
            reply_markup=order_product_keyboard("A")
        )
        return

    if data == "order_cat_B":
        order["category"] = "B"
        context.user_data["order"] = order
        await query.edit_message_text(
            "دسته B انتخاب شد.\nلطفاً محصول را انتخاب کن:",
            reply_markup=order_product_keyboard("B")
        )
        return

    if data == "order_back_cat":
        await query.edit_message_text(
            "لطفاً دستهٔ محصول را انتخاب کن:",
            reply_markup=order_category_keyboard()
        )
        return

    if data.startswith("order_prod_"):
        prod_map = {
            "order_prod_A1": "محصول A1",
            "order_prod_A2": "محصول A2",
            "order_prod_B1": "محصول B1",
            "order_prod_B2": "محصول B2",
        }
        product = prod_map.get(data, "نامشخص")
        order["product"] = product
        context.user_data["order"] = order
        await query.edit_message_text(
            f"محصول انتخاب شد: {product}\nلطفاً تعداد را انتخاب کن:",
            reply_markup=order_quantity_keyboard()
        )
        return

    if data.startswith("order_qty_"):
        qty_map = {
            "order_qty_1": 1,
            "order_qty_2": 2,
            "order_qty_3": 3,
        }
        quantity = qty_map.get(data, 1)
        order["quantity"] = quantity
        context.user_data["order"] = order
        summary = f"خلاصه سفارش:\nدسته: {order.get('category')}\nمحصول: {order.get('product')}\nتعداد: {order.get('quantity')}"
        await query.edit_message_text(
            summary + "\nآیا تأیید می‌کنی؟",
            reply_markup=order_confirm_keyboard()
        )
        return

    if data == "order_confirm":
        if not order.get("category") or not order.get("product") or not order.get("quantity"):
            await query.edit_message_text("اطلاعات سفارش ناقص است.")
            return
        order_id = db_create_order(user_id, order["category"], order["product"], order["quantity"])
        context.user_data["last_order_id"] = order_id
        context.user_data["order"] = {}
        await query.edit_message_text(
            f"سفارش ثبت شد ✅\nشماره سفارش: #{order_id}\nبرای پرداخت تستی از منو «💳 پرداخت تستی» استفاده کن."
        )
        return

    if data == "order_cancel":
        context.user_data["order"] = {}
        await query.edit_message_text("سفارش لغو شد ❌")
        return

    # سیستم پرداخت تستی حرفه‌ای
    payment = context.user_data.get("payment", {})

    if data == "pay_method_card":
        payment["method"] = "کارت"
        context.user_data["payment"] = payment
        await query.edit_message_text(
            "روش پرداخت: کارت 💳\nآیا تأیید می‌کنی؟",
            reply_markup=payment_confirm_keyboard()
        )
        return

    if data == "pay_method_cash":
        payment["method"] = "نقدی"
        context.user_data["payment"] = payment
        await query.edit_message_text(
            "روش پرداخت: نقدی 💵\nآیا تأیید می‌کنی؟",
            reply_markup=payment_confirm_keyboard()
        )
        return

    if data == "pay_confirm":
        order_id = payment.get("order_id")
        method = payment.get("method")
        if not order_id or not method:
            await query.edit_message_text("اطلاعات پرداخت ناقص است.")
            return
        payment_id = db_create_payment(user_id, order_id, method)
        context.user_data["payment"] = {}
        await query.edit_message_text(
            f"پرداخت تستی ثبت شد ✅\nشماره پرداخت: #{payment_id}\nسفارش #{order_id} با روش {method} پرداخت شد (تستی)."
        )
        return

    if data == "pay_cancel":
        context.user_data["payment"] = {}
        await query.edit_message_text("پرداخت لغو شد ❌")
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
