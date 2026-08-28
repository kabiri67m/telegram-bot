import logging
import os
import threading
import time
from collections import defaultdict
from flask import Flask
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ChatMemberHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ChatMemberStatus

# -------------------- تنظیمات --------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

FORBIDDEN_WORDS = [
    "کص", "کس", "کیر", "کون", "جنده", "کسکش", "دیوث", "مادرجنده",
    "کثافت", "حرومزاده", "حرومی", "لاشی", "جیش", "شاش", "گایید",
    "می‌گامت", "بگامت", "ننتو", "مادرتو", "خواهرتو", "کیری", "کونی",
    "جنده‌", "کس‌کش", "مادرجنده‌", "لاشی‌", "بی‌شرف", "بی‌غیرت",
    "کصکش", "کسخوار", "جنده‌خانه", "مادرقحبه"
]

FLOOD_LIMIT = 6
FLOOD_TIME = 7
user_messages = defaultdict(list)

group_locks = defaultdict(lambda: {
    "photo": False,
    "video": False,
    "sticker": False,
    "animation": False,
    "document": False,
    "link": True,
})

warnings = defaultdict(int)

slowmode_settings = defaultdict(lambda: {"enabled": False, "interval": 60})
last_message_time = defaultdict(float)

TIME_MAP = {
    "30s": 30,
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "6h": 21600,
    "1d": 86400,
}

app = Flask(__name__)

@app.route("/")
def home():
    return "Group Management Bot is running!"

@app.route("/health")
def health():
    return "OK", 200

# -------------------- توابع کمکی --------------------
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False

async def delete_msg(update: Update):
    try:
        await update.message.delete()
    except Exception:
        pass

def format_time(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} ثانیه"
    elif seconds < 3600:
        return f"{seconds // 60} دقیقه"
    elif seconds < 86400:
        return f"{seconds // 3600} ساعت"
    else:
        return f"{seconds // 86400} روز"

# -------------------- خوش‌آمدگویی --------------------
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    if result.new_chat_member.status == ChatMemberStatus.MEMBER:
        if result.old_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED, ChatMemberStatus.RESTRICTED]:
            user = result.new_chat_member.user
            name = user.first_name
            text = (
                f"سلام {name} عزیز 🌸\n\n"
                f"به جمع‌مون خیلی خوش اومدی!\n"
                f"اینجا مثل خونه‌ست، راحت باش ولی قوانین گروه رو هم رعایت کن.\n\n"
                f"برای دیدن قوانین می‌تونی از دستور /rules استفاده کنی.\n"
                f"خوشحالیم که هستی 🌿"
            )
            try:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
            except Exception as e:
                logger.error(f"Welcome error: {e}")

# -------------------- ضد سیل --------------------
async def check_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return
    if await is_admin(update, context):
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    now = time.time()
    key = (chat_id, user_id)
    user_messages[key] = [t for t in user_messages[key] if now - t < FLOOD_TIME]
    user_messages[key].append(now)

    if len(user_messages[key]) >= FLOOD_LIMIT:
        try:
            await context.bot.restrict_chat_member(
                chat_id, user_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=int(now) + 300
            )
            await update.message.reply_text(
                f"⚠️ {update.effective_user.first_name} جان، داری خیلی سریع پیام می‌فرستی.\n"
                f"به خاطر اسپم ۵ دقیقه میوت شدی."
            )
            user_messages[key].clear()
        except Exception as e:
            logger.error(f"Flood error: {e}")

# -------------------- فیلتر پیام‌ها --------------------
async def filter_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return
    if await is_admin(update, context):
        return

    message = update.message
    if not message:
        return

    chat_id = update.effective_chat.id
    user = message.from_user
    text = (message.text or message.caption or "").lower()
    now = time.time()

    # Slow Mode
    settings = slowmode_settings[chat_id]
    if settings["enabled"]:
        key = (chat_id, user.id)
        last_time = last_message_time[key]
        interval = settings["interval"]
        if now - last_time < interval:
            remaining = int(interval - (now - last_time))
            await delete_msg(update)
            try:
                await context.bot.send_message(
                    chat_id,
                    f"⏳ {user.first_name} عزیز، محدودیت ارسال پیام فعاله.\n"
                    f"لطفاً {format_time(remaining)} دیگه صبر کن."
                )
            except:
                pass
            return
        else:
            last_message_time[key] = now

    # لینک
    has_link = False
    if message.entities:
        for entity in message.entities:
            if entity.type in ["url", "text_link"]:
                has_link = True
                break
    link_keywords = ["http://", "https://", "www.", "t.me/", "telegram.me/"]
    if any(k in text for k in link_keywords):
        has_link = True

    if group_locks[chat_id]["link"] and has_link:
        await delete_msg(update)
        try:
            await context.bot.send_message(chat_id, f"🔗 {user.first_name} عزیز، ارسال لینک در این گروه مجاز نیست.")
        except:
            pass
        return

    # کلمات ممنوعه
    for word in FORBIDDEN_WORDS:
        if word in text:
            await delete_msg(update)
            warnings[(chat_id, user.id)] += 1
            count = warnings[(chat_id, user.id)]
            try:
                await context.bot.send_message(chat_id, f"🚫 {user.first_name} جان، از کلمات نامناسب استفاده نکن.\nاخطار {count} از ۳")
            except:
                pass
            if count >= 3:
                try:
                    await context.bot.ban_chat_member(chat_id, user.id)
                    await context.bot.send_message(chat_id, "کاربر به دلیل ۳ اخطار از گروه حذف شد.")
                except:
                    pass
            return

    # قفل محتوا
    locks = group_locks[chat_id]
    if (locks["photo"] and message.photo) or (locks["video"] and message.video) or \
       (locks["sticker"] and message.sticker) or (locks["animation"] and message.animation) or \
       (locks["document"] and message.document):
        await delete_msg(update)

# -------------------- دستورات --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    keyboard = [[InlineKeyboardButton("⚙️ منوی تنظیمات", callback_data="settings_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("منوی تنظیمات:", reply_markup=reply_markup)

async def slowmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("این دستور فقط برای ادمین‌هاست.")
    chat_id = update.effective_chat.id
    args = context.args
    if not args:
        settings = slowmode_settings[chat_id]
        if settings["enabled"]:
            await update.message.reply_text(f"⏳ محدودیت ارسال پیام **فعال** است.\nفاصله مجاز: هر {format_time(settings['interval'])} یک پیام")
        else:
            await update.message.reply_text("⏳ محدودیت ارسال پیام در حال حاضر **خاموش** است.")
        return
    command = args[0].lower()
    if command == "off":
        slowmode_settings[chat_id]["enabled"] = False
        await update.message.reply_text("✅ محدودیت ارسال پیام خاموش شد.")
        return
    if command in TIME_MAP:
        slowmode_settings[chat_id]["enabled"] = True
        slowmode_settings[chat_id]["interval"] = TIME_MAP[command]
        await update.message.reply_text(f"✅ محدودیت ارسال پیام فعال شد.\nهر کاربر هر {format_time(TIME_MAP[command])} می‌تونه یک پیام بفرسته.")
        return
    await update.message.reply_text("فرمت درست نیست.\nمثال:\n/slowmode 1m\n/slowmode 30s\n/slowmode off")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("این دستور فقط برای ادمین‌هاست.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("لطفاً روی پیام کاربر ریپلای کنید.")
    user = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"✅ کاربر {user.first_name} از گروه بن شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not context.args:
        return await update.message.reply_text("آیدی عددی کاربر را وارد کنید.\nمثال: /unban 123456789")
    try:
        user_id = int(context.args[0])
        await context.bot.unban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text("✅ کاربر آنبن شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("این دستور فقط برای ادمین‌هاست.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("روی پیام کاربر ریپلای کنید.")
    user = update.message.reply_to_message.from_user
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, user.id, permissions=ChatPermissions(can_send_messages=False))
        await update.message.reply_text(f"🔇 کاربر {user.first_name} میوت شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        return await update.message.reply_text("روی پیام کاربر ریپلای کنید.")
    user = update.message.reply_to_message.from_user
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, user.id, permissions=ChatPermissions(
            can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True
        ))
        await update.message.reply_text(f"🔊 کاربر {user.first_name} آنمیوت شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        return await update.message.reply_text("روی پیام کاربر ریپلای کنید.")
    user = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    warnings[(chat_id, user.id)] += 1
    count = warnings[(chat_id, user.id)]
    await update.message.reply_text(f"⚠️ اخطار به {user.first_name}\nتعداد اخطار: {count} از ۳")
    if count >= 3:
        try:
            await context.bot.ban_chat_member(chat_id, user.id)
            await update.message.reply_text("کاربر به دلیل ۳ اخطار بن شد.")
        except:
            pass

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """📜 قوانین گروه

۱. با احترام با همه صحبت کنید.
۲. اسپم و پیام پشت‌سرهم ممنوع است.
۳. ارسال لینک بدون اجازه مجاز نیست.
۴. استفاده از کلمات رکیک ممنوع است.
۵. در صورت ۳ اخطار، از گروه حذف خواهید شد.

با رعایت قوانین، گروه قشنگ‌تری خواهیم داشت 🌿"""
    await update.message.reply_text(text)

# -------------------- منوی Callback --------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "settings_menu":
        keyboard = [
            [InlineKeyboardButton("🔄 Slow Mode", callback_data="slowmode_menu")],
            [InlineKeyboardButton("🛑 کلمات ممنوعه", callback_data="forbidden_words")],
            [InlineKeyboardButton("📷 قفل محتوا", callback_data="lock_menu")],
            [InlineKeyboardButton("❌ ریست تنظیمات", callback_data="reset_settings")]
        ]
        await query.edit_message_text("⚙️ تنظیمات گروه:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "slowmode_menu":
        keyboard = [
            [InlineKeyboardButton("✅ خاموش", callback_data="slow_off")],
            [InlineKeyboardButton("30 ثانیه", callback_data="slow_30s")],
            [InlineKeyboardButton("۱ دقیقه", callback_data="slow_1m")],
            [InlineKeyboardButton("۵ دقیقه", callback_data="slow_5m")],
            [InlineKeyboardButton("۱ ساعت", callback_data="slow_1h")],
            [InlineKeyboardButton("۱ روز", callback_data="slow_1d")],
            [InlineKeyboardButton("بازگشت", callback_data="settings_menu")]
        ]
        await query.edit_message_text("⏳ Slow Mode:\nهر کاربر فقط یک پیام در هر X ثانیه می‌تونه بفرسته.", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "forbidden_words":
        await query.edit_message_text("🛑 کلمات ممنوعه:\n\nلیست فعلی:\nکص، کیر، کون، جنده، دیوث، مادرجنده و...\n\nبرای ویرایش لیست بعداً می‌تونیم اضافه کنیم.")

    elif data == "lock_menu":
        await query.edit_message_text("📷 قفل محتوا:\n\nعکس، ویدیو، استیکر و... در گروه قفل می‌شن.\n(در نسخه فعلی فقط لینک به صورت پیش‌فرض قفل است)")

    elif data == "reset_settings":
        for cid in list(slowmode_settings.keys()):
            slowmode_settings[cid]["enabled"] = False
            slowmode_settings[cid]["interval"] = 60
        await query.edit_message_text("✅ تنظیمات به حالت پیش‌فرض برگشت.")

    elif data.startswith("slow_"):
        # توجه: این منو فعلاً فقط نمایشی است چون chat_id گروه را از خصوصی نمی‌دانیم
        # برای کارکرد واقعی Slow Mode از دستور /slowmode داخل گروه استفاده کن
        if data == "slow_off":
            await query.edit_message_text("برای خاموش کردن Slow Mode داخل گروه دستور زیر را بزن:\n/slowmode off")
        else:
            time_key = data.replace("slow_", "")
            await query.edit_message_text(f"برای فعال کردن این حالت داخل گروه دستور زیر را بزن:\n/slowmode {time_key}")

# -------------------- اجرا --------------------
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise SystemExit("BOT_TOKEN تنظیم نشده")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("unban", unban))
    application.add_handler(CommandHandler("mute", mute))
    application.add_handler(CommandHandler("unmute", unmute))
    application.add_handler(CommandHandler("warn", warn_user))
    application.add_handler(CommandHandler("rules", rules))
    application.add_handler(CommandHandler("slowmode", slowmode))

    application.add_handler(ChatMemberHandler(welcome, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, filter_message), group=1)
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_flood), group=2)

    # منوی دکمه‌ای (درست)
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("ربات مدیریت گروه شروع به کار کرد...")
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query", "chat_member"]
    )
