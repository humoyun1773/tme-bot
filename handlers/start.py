from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from database import add_user

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    user = message.from_user
    if user:
        await add_user(user.id, user.username, user.full_name)

    text = (
        f"👋 <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
        "Men <b>Universal Media Downloader & Music Bot</b>man. 📥🎵\n\n"
        "<b>Menga quyidagilarni yuborishingiz mumkin:</b>\n"
        "1️⃣ <b>Ijtimoiy tarmoq havolasi:</b>\n"
        "  • 🔴 YouTube (Video, Shorts, MP3)\n"
        "  • 📷 Instagram (Reels, Post, Karusel, Stories)\n"
        "  • 🎵 TikTok (Suv belgisiz video, Audio)\n"
        "  • 🐦 Twitter / X, Pinterest va h.k.\n\n"
        "2️⃣ <b>Qo'shiq nomi yoki ijrochisi (matn):</b>\n"
        "  • Shunchaki qo'shiq nomini yozing (masalan: <code>Ummon guruhi - Sensiz</code>)\n"
        "  • Bot eng mos 5 ta qo'shiqni topib, MP3 formatda yuboradi!\n\n"
        "<i>Sinab ko'rish uchun hoziroq havola yoki qo'shiq nomini yuboring!</i>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "📖 <b>Botdan foydalanish qo'llanmasi:</b>\n\n"
        "🔹 <b>Havola orqali yuklash:</b>\n"
        "1. Instagram, YouTube, TikTok yoki boshqa tarmoqdan havola nusxalang.\n"
        "2. Botga yuboring va sifatni (360p, 720p, MP3) tanlang.\n\n"
        "🔹 <b>Qo'shiq nomi bo'yicha qidirish:</b>\n"
        "1. Hech qanday havolasiz, to'g'ridan-to'g'ri qo'shiq yoki ijrochi nomini yozing (masalan: <code>Konsta - Odamlar nima deydi</code>).\n"
        "2. Chiqqan 5 ta variantdan keraklisini bosing.\n"
        "3. Bot qo'shiqni muqova surati va ma'lumotlari bilan MP3 formatda yuboradi.\n\n"
        "⚠️ <b>Cheklovlar:</b>\n"
        "• Telegram orqali yuboriladigan fayllarning maksimal hajmi <b>50 MB</b>.\n"
        "• Yopiq (private) profillardagi kontentlarni yuklab bo'lmaydi.\n\n"
        "Savol yoki takliflar bo'lsa, adminga murojaat qiling."
    )
    await message.answer(text, parse_mode="HTML")
