import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# =============================================
BOT_TOKEN = "8665299234:AAE40ncVp6dkO9yX4AtFN-lNyNm2AoiIzkI"
ADMIN_ID = 6396925882  # O'z Telegram ID ingizni shu yerga yozing (raqam)
# =============================================

DB_FILE = "kinolar.json"

def db_yuklash():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def db_saqlash(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *Kino Botga Xush Kelibsiz!*\n\n"
        "Kino kodini yuboring va kinoni oling!\n\n"
        "Misol: `001` yoki `#001`",
        parse_mode="Markdown"
    )

async def xabar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    matn = update.message.text.strip()
    kinolar = db_yuklash()

    # Admin kino qo'shish rejimi
    if str(user_id) == str(ADMIN_ID) and context.user_data.get('rejim') == 'kutish':
        # Kino fayli kutilmoqda — bu matn kod bo'lishi kerak
        await update.message.reply_text("❌ Iltimos, avval kino faylini yuboring, keyin kod!")
        context.user_data['rejim'] = None
        return

    # Kod bilan kino qidirish
    kod = matn.replace('#', '').replace(' ', '').upper()
    if kod in kinolar:
        kino = kinolar[kod]
        file_id = kino.get('file_id')
        nomi = kino.get('nomi', 'Nomsiz')
        if file_id:
            await update.message.reply_text(f"🎬 *{nomi}*\nYuklanmoqda...", parse_mode="Markdown")
            await update.message.reply_document(document=file_id, caption=f"🎬 {nomi}")
        else:
            await update.message.reply_text(f"❌ Bu kino fayli topilmadi.")
    else:
        await update.message.reply_text(
            f"❌ *{matn}* kodi topilmadi.\n\nTo'g'ri kod kiriting!",
            parse_mode="Markdown"
        )

async def fayl_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return

    # Fayl qabul qilindi — kod so'rash
    doc = update.message.document or update.message.video
    if doc:
        context.user_data['fayl_id'] = doc.file_id
        context.user_data['rejim'] = 'kod_kutish'
        await update.message.reply_text(
            "✅ Fayl qabul qilindi!\n\n"
            "Endi bu kinoning *kodi* va *nomini* yuboring:\n"
            "Format: `001 | Kino nomi`\n"
            "Misol: `001 | Avatar 2022`",
            parse_mode="Markdown"
        )

async def admin_kod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if str(user_id) != str(ADMIN_ID):
        return
    
    if context.user_data.get('rejim') != 'kod_kutish':
        return
    
    matn = update.message.text.strip()
    if '|' not in matn:
        await update.message.reply_text("❌ Format xato! `001 | Kino nomi` ko'rinishida yuboring.", parse_mode="Markdown")
        return
    
    qismlar = matn.split('|', 1)
    kod = qismlar[0].strip().replace('#', '').upper()
    nom = qismlar[1].strip()
    
    kinolar = db_yuklash()
    kinolar[kod] = {
        'nomi': nom,
        'file_id': context.user_data.get('fayl_id')
    }
    db_saqlash(kinolar)
    
    context.user_data['rejim'] = None
    context.user_data['fayl_id'] = None
    
    await update.message.reply_text(
        f"✅ Kino qo'shildi!\n\n"
        f"📽 Nomi: *{nom}*\n"
        f"🔑 Kodi: `{kod}`\n\n"
        f"Odamlar `{kod}` yozsa, bu kinoni oladi!",
        parse_mode="Markdown"
    )

async def kinolar_royxati(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text("❌ Faqat admin uchun!")
        return
    
    kinolar = db_yuklash()
    if not kinolar:
        await update.message.reply_text("📭 Hali kino qo'shilmagan.")
        return
    
    matn = "🎬 *Kinolar ro'yxati:*\n\n"
    for kod, info in kinolar.items():
        matn += f"`{kod}` — {info.get('nomi', 'Nomsiz')}\n"
    
    await update.message.reply_text(matn, parse_mode="Markdown")

async def ochirish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if str(user_id) != str(ADMIN_ID):
        return
    
    if not context.args:
        await update.message.reply_text("Format: `/ochir 001`", parse_mode="Markdown")
        return
    
    kod = context.args[0].replace('#', '').upper()
    kinolar = db_yuklash()
    
    if kod in kinolar:
        nom = kinolar[kod].get('nomi', kod)
        del kinolar[kod]
        db_saqlash(kinolar)
        await update.message.reply_text(f"✅ *{nom}* o'chirildi!", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ `{kod}` topilmadi!", parse_mode="Markdown")

async def mening_idim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Sizning Telegram ID ingiz: `{update.message.from_user.id}`", parse_mode="Markdown")

def main():
    print("🎬 Kino bot ishga tushmoqda...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("royxat", kinolar_royxati))
    app.add_handler(CommandHandler("ochir", ochirish))
    app.add_handler(CommandHandler("idim", mening_idim))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.VIDEO, fayl_qabul))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: 
        admin_kod(u, c) if str(u.message.from_user.id) == str(ADMIN_ID) and c.user_data.get('rejim') == 'kod_kutish' 
        else xabar(u, c)))
    
    print("✅ Bot ishlamoqda! Ctrl+C bilan to'xtatish mumkin.")
    app.run_polling()

if __name__ == "__main__":
    main()
