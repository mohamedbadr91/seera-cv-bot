import os, logging, io
from telegram import Update
from telegram import ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import arabic_reshaper
from bidi.algorithm import get_display

LANG, NAME, TITLE, CONTACT, SUMMARY, EXP, EDU, SKILLS, TEMPLATE = range(9)

def ar(t):
    try:
        return get_display(arabic_reshaper.reshape(t))
    except:
        return t

async def start(update, context):
    context.user_data.clear()
    context.user_data["cv"] = {}
    await update.message.reply_text("اهلا بيك في SeeraCVBot\nاختر لغة السيرة:", reply_markup=ReplyKeyboardMarkup([["عربي 🇪🇬", "English 🇺🇸"]], resize_keyboard=True))
    return LANG

async def set_lang(update, context):
    context.user_data["lang"] = "ar" if "عربي" in update.message.text else "en"
    context.user_data["cv"] = {}
    await update.message.reply_text("اسمك الكامل؟", reply_markup=ReplyKeyboardMarkup([["إلغاء ❌"]], resize_keyboard=True))
    return NAME

async def set_name(update, context):
    context.user_data["cv"]["name"] = update.message.text
    await update.message.reply_text("المسمى الوظيفي؟")
    return TITLE

async def set_title(update, context):
    context.user_data["cv"]["title"] = update.message.text
    await update.message.reply_text("الهاتف والايميل؟ (اجباري)")
    return CONTACT

async def set_contact(update, context):
    context.user_data["cv"]["contact"] = update.message.text
    await update.message.reply_text("ملخص مهني او تخطي", reply_markup=ReplyKeyboardMarkup([["تخطي ⏭️"], ["إنهاء وإنشاء السيرة ✅"]], resize_keyboard=True))
    return SUMMARY

async def set_summary(update, context):
    if "إنهاء" in update.message.text:
        return await choose_template(update, context)
    if "تخطي" not in update.message.text:
        context.user_data["cv"]["summary"] = update.message.text
    await update.message.reply_text("الخبرات؟ او تخطي", reply_markup=ReplyKeyboardMarkup([["تخطي ⏭️"], ["إنهاء وإنشاء السيرة ✅"]], resize_keyboard=True))
    return EXP

async def set_exp(update, context):
    if "إنهاء" in update.message.text:
        return await choose_template(update, context)
    if "تخطي" not in update.message.text:
        context.user_data["cv"]["exp"] = update.message.text
    await update.message.reply_text("التعليم؟ او تخطي", reply_markup=ReplyKeyboardMarkup([["تخطي ⏭️"], ["إنهاء وإنشاء السيرة ✅"]], resize_keyboard=True))
    return EDU

async def set_edu(update, context):
    if "إنهاء" in update.message.text:
        return await choose_template(update, context)
    if "تخطي" not in update.message.text:
        context.user_data["cv"]["edu"] = update.message.text
    await update.message.reply_text("المهارات؟ او تخطي", reply_markup=ReplyKeyboardMarkup([["تخطي ⏭️"], ["إنهاء وإنشاء السيرة ✅"]], resize_keyboard=True))
    return SKILLS

async def set_skills(update, context):
    if "إنهاء" in update.message.text:
        return await choose_template(update, context)
    if "تخطي" not in update.message.text:
        context.user_data["cv"]["skills"] = update.message.text
    return await choose_template(update, context)

async def choose_template(update, context):
    await update.message.reply_text("اختار القالب:", reply_markup=ReplyKeyboardMarkup([["ATS - بدون صورة ✅"]], resize_keyboard=True))
    return TEMPLATE

def build_pdf(cv, lang):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    style = styles['Normal']
    style.fontSize = 11
    style.leading = 16
    def add_sec(t_ar, t_en, k):
        c = cv.get(k)
        if not c:
            return
        t = t_ar if lang=="ar" else t_en
        story.append(Paragraph(f"<b>{t}</b>", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        for line in c.split('\n'):
            story.append(Paragraph(ar(line) if lang=="ar" else line, style))
        story.append(Spacer(1, 0.2*inch))
    n = cv.get("name","")
    story.append(Paragraph(f"<b><font size=16>{ar(n) if lang=='ar' else n}</font></b>", styles['Heading1']))
    story.append(Paragraph(ar(cv.get("title","")) if lang=="ar" else cv.get("title",""), style))
    story.append(Paragraph(ar(cv.get("contact","")) if lang=="ar" else cv.get("contact",""), style))
    story.append(Spacer(1, 0.3*inch))
    add_sec("الملخص", "Summary", "summary")
    add_sec("الخبرات", "Experience", "exp")
    add_sec("التعليم", "Education", "edu")
    add_sec("المهارات", "Skills", "skills")
    doc.build(story)
    buffer.seek(0)
    return buffer

async def create_cv_final(update, context):
    cv = context.user_data.get("cv", {})
    lang = context.user_data.get("lang", "ar")
    await update.message.reply_text("⏳ جاري انشاء السيرة...")
    pdf = build_pdf(cv, lang)
    await update.message.reply_document(document=pdf, filename=f"CV_{cv.get('name','user')}.pdf", caption="✅ سيرتك جاهزة ATS")
    return ConversationHandler.END

def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_lang)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_name)],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_title)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_contact)],
            SUMMARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_summary)],
            EXP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_exp)],
            EDU: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_edu)],
            SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_skills)],
            TEMPLATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_cv_final)],
        },
        fallbacks=[CommandHandler("start", start)]
    )
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
