import logging
import os
import threading
import time
from collections import defaultdict
from flask import Flask
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
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

# کلمات ممنوعه (می‌تونی بعداً بیشترش کنی)
FORBIDDEN_WORDS = ["کص", "کیر", "کسکش", "جنده", "کون", "دیوث", "مادرجنده"]

# ضد سیل
FLOOD_LIMIT = 5          # حداکثر پیام
FLOOD_TIME = 8           # در چند ثانیه
user_messages = defaultdict(list)

# قفلهای گروه (فعلاً در حافظه - بعداً می‌تونیم دیتابیس کنیم)
group_locks = defaultdict(lambda: {
    "photo": False,
    "video": False,
    "sticker": False,
    "animation": False,   # گیف
    "document": False,
    "link": True,         # به صورت پیش‌فرض لینک قفل باشه
})

# تعداد اخطارها
warnings = defaultdict(int)

app = Flask(__name__)

@app.route("/")
def home():
    return "Group Management Bot is running!"

# -------------------- توابع کمکی --------------------
def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """چک می‌کنه آیا کاربر ادمین هست یا نه"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    try:
        member = context.bot.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False

async def delete_message(update: Update):
    try:
        await update.message.delete()
    except Exception:
        pass

# -------------------- خوش‌آمدگویی --------------------
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    if result.new_chat_member.status == ChatMemberStatus.MEMBER:
        if result.old_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
            user = result.new_chat_member.user
            name = user.mention_html()
            text = f"سلام {name} 🌟\nبه گروه خوش اومدی!\nلطفاً قوانین گروه رو با دستور /rules مطالعه کن."
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                parse_mode="HTML"
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

    user_messages[(chat_id, user_id)] = [
        t for t in user_messages[(chat_id, user_id)] if now - t < FLOOD_TIME
    ]
    user_messages[(chat_id, user_id)].append(now)

    if len(user_messages[(chat_id, user_id)]) > FLOOD_LIMIT:
        try:
            await context.bot.restrict_chat_member(
                chat_id,
                user_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=int(now) + 300  # ۵ دقیقه میوت
            )
            await update.message.reply_text(
                f"⚠️ کاربر [{update.effective_user.first_name}](tg://user?id={user_id}) به خاطر اسپم ۵ دقیقه میوت شد.",
                parse_mode="Markdown"
            )
            user_messages[(chat_id, user_id)].clear()
        except Exception as e:
            logger.error(f"Flood error: {e}")

# -------------------- فیلتر لینک و کلمات ممنوعه --------------------
async def filter_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return
    if await is_admin(update, context):
        return

    message = update.message
    text = (message.text or message.caption or "").lower()
    chat_id = update.effective_chat.id

    # حذف لینک
    if group_locks[chat_id]["link"]:
        if message.entities:
            for entity in message.entities:
                if entity.type in ["url", "text_link"]:
                    await delete_message(update)
                    return

    # کلمات ممنوعه
    for word in FORBIDDEN_WORDS:
        if word in text:
            await delete_message(update)
            warnings[(chat_id, message.from_user.id)] += 1
            count = warnings[(chat_id, message.from_user.id)]
            await message.reply_text(
                f"🚫 پیام شما به خاطر استفاده از کلمات نامناسب حذف شد.\n"
                f"اخطار: {count}/3"
            )
            if count >= 3:
                try:
                    await context.bot.ban_chat_member(chat_id, message.from_user.id)
                    await context.bot.send_message(chat_id, f"کاربر به خاطر ۳ اخطار بن شد.")
                except:
                    pass
            return

    # قفل محتوا
    locks = group_locks[chat_id]
    if locks["photo"] and message.photo:
        await delete_message(update)
    elif locks["video"] and message.video:
        await delete_message(update)
    elif locks["sticker"] and message.sticker:
        await delete_message(update)
    elif locks["animation"] and message.animation:
        await delete_message(update)
    elif locks["document"] and message.document:
        await delete_message(update)

# -------------------- دستورات مدیریتی --------------------
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("فقط ادمین‌ها می‌تونن از این دستور استفاده کنن.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("روی پیام کاربر ریپلای کنید.")
    
    user = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"✅ کاربر {user.first_name} بن شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not context.args:
        return await update.message.reply_text("آیدی عددی کاربر را بعد از دستور بنویسید.")
    try:
        user_id = int(context.args[0])
        await context.bot.unban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text("✅ کاربر آنبن شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("فقط ادمین.")
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

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        return await update.message.reply_text("روی پیام کاربر ریپلای کنید.")
    
    user = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    warnings[(chat_id, user.id)] += 1
    count = warnings[(chat_id, user.id)]
    await update.message.reply_text(f"⚠️ اخطار به {user.first_name}\nتعداد اخطار: {count}/3")
    
    if count >= 3:
        try:
            await context.bot.ban_chat_member(chat_id, user.id)
            await update.message.reply_text("کاربر به دلیل ۳ اخطار بن شد.")
        except:
            pass

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
📜 **قوانین گروه**

۱. احترام به همه اعضا الزامی است.
۲. اسپم و تبلیغ ممنوع.
۳. ارسال لینک بدون اجازه ممنوع.
۴. استفاده از کلمات رکیک ممنوع.
۵. در صورت ۳ اخطار، بن خواهید شد.

با تشکر از رعایت قوانین 🌟
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من ربات مدیریت گروه هستم.\n"
        "مرا به گروه اضافه کنید و ادمین کنید."
    )

# -------------------- اجرای ربات --------------------
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

    # هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("unban", unban))
    application.add_handler(CommandHandler("mute", mute))
    application.add_handler(CommandHandler("unmute", unmute))
    application.add_handler(CommandHandler("warn", warn))
    application.add_handler(CommandHandler("rules", rules))
    
    application.add_handler(ChatMemberHandler(welcome, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, filter_message), group=1)
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_flood), group=2)

    logger.info("ربات مدیریت گروه شروع شد...")
    application.run_polling(drop_pending_updates=True)
