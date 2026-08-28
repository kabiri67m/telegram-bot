import logging
import os
import threading
import time
from collections import defaultdict
from flask import Flask
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ChatMemberHandler,
    ContextTypes, filters
)
from telegram.constants import ChatMemberStatus

# -------------------- تنظیمات --------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# کلمات ممنوعه (می‌تونی بیشترش کنی)
FORBIDDEN_WORDS = ["کص", "کیر", "کسکش", "جنده", "کون", "دیوث", "مادرجنده", "کثافت"]

# تنظیمات ضد سیل
FLOOD_LIMIT = 6
FLOOD_TIME = 7
user_messages = defaultdict(list)

# قفلهای گروه (فعلاً در حافظه)
group_locks = defaultdict(lambda: {
    "photo": False,
    "video": False,
    "sticker": False,
    "animation": False,
    "document": False,
    "link": True,  # لینک به صورت پیش‌فرض قفل باشه
})

# سیستم اخطار
warnings = defaultdict(int)

app = Flask(__name__)

@app.route("/")
def home():
    return "Group Management Bot is running!"

# -------------------- توابع کمکی --------------------
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id,
            update.effective_user.id
        )
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False

async def delete_msg(update: Update):
    try:
        await update.message.delete()
    except Exception:
        pass

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
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text
            )

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
                chat_id,
                user_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=int(now) + 300
            )
            await update.message.reply_text(
                f"⚠️ {update.effective_user.first_name} جان، داری خیلی سریع پیام می‌فرستی.\n"
                f"به خاطر اسپم ۵ دقیقه میوت شدی."
            )
            user_messages[key].clear()
        except Exception as e:
            logger.error(f"Flood restrict error: {e}")

# -------------------- فیلتر پیام‌ها --------------------
async def filter_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return
    if await is_admin(update, context):
        return

    message = update.message
    if not message:
        return

    text = (message.text or message.caption or "").lower()
    chat_id = update.effective_chat.id
    user = message.from_user

    # حذف لینک
    if group_locks[chat_id]["link"] and message.entities:
        for entity in message.entities:
            if entity.type in ["url", "text_link"]:
                await delete_msg(update)
                await context.bot.send_message(
                    chat_id,
                    f"🔗 {user.first_name} عزیز، ارسال لینک در این گروه مجاز نیست."
                )
                return

    # کلمات ممنوعه
    for word in FORBIDDEN_WORDS:
        if word in text:
            await delete_msg(update)
            warnings[(chat_id, user.id)] += 1
            count = warnings[(chat_id, user.id)]
            
            await context.bot.send_message(
                chat_id,
                f"🚫 {user.first_name} جان، از کلمات نامناسب استفاده نکن.\n"
                f"اخطار {count} از ۳"
            )
            
            if count >= 3:
                try:
                    await context.bot.ban_chat_member(chat_id, user.id)
                    await context.bot.send_message(chat_id, f"کاربر به دلیل ۳ اخطار از گروه حذف شد.")
                except Exception:
                    pass
            return

    # قفل محتوا
    locks = group_locks[chat_id]
    if (locks["photo"] and message.photo) or \
       (locks["video"] and message.video) or \
       (locks["sticker"] and message.sticker) or \
       (locks["animation"] and message.animation) or \
       (locks["document"] and message.document):
        await delete_msg(update)

# -------------------- دستورات مدیریتی --------------------
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
        await update.message.reply_text(f"خطا در بن کردن: {e}")

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
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
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
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
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
    
    await update.message.reply_text(
        f"⚠️ اخطار به {user.first_name}\n"
        f"تعداد اخطار: {count} از ۳"
    )
    
    if count >= 3:
        try:
            await context.bot.ban_chat_member(chat_id, user.id)
            await update.message.reply_text("کاربر به دلیل ۳ اخطار بن شد.")
        except Exception:
            pass

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
📜 قوانین گروه

۱. با احترام با همه صحبت کنید.
۲. اسپم و پیام پشت‌سرهم ممنوع است.
۳. ارسال لینک بدون اجازه مجاز نیست.
۴. استفاده از کلمات رکیک ممنوع است.
۵. در صورت ۳ اخطار، از گروه حذف خواهید شد.

با رعایت قوانین، گروه قشنگ‌تری خواهیم داشت 🌿
"""
    await update.message.reply_text(text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من ربات مدیریت گروه هستم.\n"
        "مرا به گروه اضافه کنید و ادمین کنید تا بتونم کمکتون کنم."
    )

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

    application.add_handler(ChatMemberHandler(welcome, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, filter_message), group=1)
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_flood), group=2)

    logger.info("ربات مدیریت گروه شروع به کار کرد...")
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query", "chat_member"]
    )
