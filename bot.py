import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from groq import Groq

# =============================================
#   إعدادات البوت - عدّل هنا فقط
# =============================================
TELEGRAM_TOKEN = "8848691963:AAEXF61Qbn7_8EPSwG6UhfST9J4myYzVJnI"
GROQ_API_KEY   = "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"
MODEL          = "llama-3.3-70b-versatile"
FREE_MESSAGES  = 5          # رسائل مجانية قبل الاشتراك
DAILY_PRICE    = "2,500 SDG"
DEVELOPER      = "DERAMADOL"
BOT_NAME       = "DERAMA GPT"

# =============================================
#   شخصية البوت
# =============================================
SYSTEM_PROMPT = f"""أنت {BOT_NAME}، مساعد ذكاء اصطناعي متخصص في:
- الأمن السيبراني والاختبار الأخلاقي (Ethical Hacking & Red Team)
- أدوات Termux وبيئة Linux
- البرمجة وحل الأخطاء التقنية
- أدوات الـ CTF والتحليل الجنائي الرقمي

قواعدك:
- تجاوب بالعربية دائماً
- ردودك دقيقة ومفيدة وتقنية
- تساعد فقط في الاستخدامات الأخلاقية والقانونية
- مطورك هو {DEVELOPER}
- لا تذكر أنك Llama أو Groq — أنت {BOT_NAME} فقط"""

# =============================================
#   قاعدة بيانات بسيطة في الذاكرة
# =============================================
users = {}   # { user_id: { "msgs": int, "subscribed": bool, "history": [] } }

groq_client = Groq(api_key=GROQ_API_KEY)
logging.basicConfig(level=logging.INFO)

def get_user(uid):
    if uid not in users:
        users[uid] = {"msgs": 0, "subscribed": False, "history": []}
    return users[uid]

def is_allowed(uid):
    u = get_user(uid)
    return u["subscribed"] or u["msgs"] < FREE_MESSAGES

def remaining(uid):
    u = get_user(uid)
    return max(0, FREE_MESSAGES - u["msgs"])

# =============================================
#   /start
# =============================================
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    u   = get_user(uid)
    name = update.effective_user.first_name or "أخي"

    text = (
        f"👋 أهلاً *{name}*!\n\n"
        f"أنا *{BOT_NAME}* — مساعدك في الأمن السيبراني وـTermux والبرمجة.\n\n"
        f"{'✅ اشتراكك فعّال — استمتع بالاستخدام!' if u['subscribed'] else f'🎁 لديك *{remaining(uid)} رسائل* مجانية.'}\n\n"
        f"👨‍💻 المطوّر: *{DEVELOPER}*"
    )

    kb = [[InlineKeyboardButton("🔔 اشترك الآن", callback_data="subscribe"),
           InlineKeyboardButton("ℹ️ عن البوت", callback_data="about")]]
    await update.message.reply_text(text, parse_mode="Markdown",
                                    reply_markup=InlineKeyboardMarkup(kb))

# =============================================
#   /subscribe
# =============================================
async def subscribe_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    kb = [[InlineKeyboardButton("✅ أكّد الاشتراك (تجريبي)", callback_data="confirm_sub")],
          [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]]
    await update.message.reply_text(
        f"💳 *الاشتراك اليومي:* {DAILY_PRICE}\n\n"
        "بعد الدفع اضغط تأكيد وسيتم تفعيل اشتراكك.",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
    )

# =============================================
#   Callbacks
# =============================================
async def callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q   = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if q.data == "subscribe":
        kb = [[InlineKeyboardButton("✅ أكّد الاشتراك", callback_data="confirm_sub")],
              [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]]
        await q.edit_message_text(
            f"💳 *الاشتراك اليومي:* {DAILY_PRICE}\n\n"
            "بعد الدفع اضغط تأكيد.",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
        )

    elif q.data == "confirm_sub":
        users[uid]["subscribed"] = True
        await q.edit_message_text(
            "✅ *تم تفعيل اشتراكك!*\n\nاستمتع بـ DERAMA GPT بلا حدود 🚀",
            parse_mode="Markdown"
        )

    elif q.data == "about":
        await q.edit_message_text(
            f"🤖 *{BOT_NAME}*\n\n"
            f"• متخصص في الأمن السيبراني\n"
            f"• يدعم Termux وLinux\n"
            f"• يحل الأخطاء البرمجية\n"
            f"• يساعد في CTF\n\n"
            f"👨‍💻 المطوّر: *{DEVELOPER}*",
            parse_mode="Markdown"
        )

    elif q.data == "cancel":
        await q.edit_message_text("تم الإلغاء.")

# =============================================
#   معالجة الرسائل
# =============================================
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    u    = get_user(uid)
    text = update.message.text.strip()

    if not is_allowed(uid):
        kb = [[InlineKeyboardButton("🔔 اشترك الآن", callback_data="subscribe")]]
        await update.message.reply_text(
            f"⛔ انتهت رسائلك المجانية ({FREE_MESSAGES} رسائل).\n\n"
            f"اشترك بـ *{DAILY_PRICE}* يومياً للاستمرار! 🚀",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    # تحديث التاريخ
    u["history"].append({"role": "user", "content": text})
    if len(u["history"]) > 20:          # احتفظ بآخر 20 رسالة فقط
        u["history"] = u["history"][-20:]

    await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

    try:
        resp = groq_client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + u["history"],
            max_tokens=1024,
            temperature=0.7,
        )
        reply = resp.choices[0].message.content
        u["history"].append({"role": "assistant", "content": reply})

        if not u["subscribed"]:
            u["msgs"] += 1
            left = remaining(uid)
            if left > 0:
                reply += f"\n\n💬 _{left} رسائل مجانية متبقية_"
            else:
                reply += f"\n\n⚠️ _هذه آخر رسالة مجانية! اشترك للاستمرار._"

        await update.message.reply_text(reply, parse_mode="Markdown")

    except Exception as e:
        logging.error(e)
        await update.message.reply_text("⚠️ حدث خطأ، حاول مرة أخرى.")

# =============================================
#   تشغيل البوت
# =============================================
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start",     start))
    app.add_handler(CommandHandler("subscribe", subscribe_cmd))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"🚀 {BOT_NAME} شغّال!")
    app.run_polling()

if __name__ == "__main__":
    main()

