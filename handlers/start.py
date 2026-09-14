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
        f"✨ <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
        "Men <b>Universal Media & Music Downloader</b> botiman 🚀\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📥 <b>Ijtimoiy tarmoqlar:</b>\n"
        "• 🔴 <b>YouTube:</b> Video (360p - 1080p), Shorts, MP3\n"
        "• 📷 <b>Instagram:</b> Reels, Post, Karusel, Stories\n"
        "• 🎵 <b>TikTok:</b> Suv belgisiz video va musiqa\n"
        "• 🐦 <b>Twitter / X, Pinterest:</b> Video va rasmlar\n\n"
        "🎧 <b>Qo'shiq qidirish:</b>\n"
        "Shunchaki qo'shiq yoki ijrochi nomini yozing (masalan: <code>Ummon - Sensiz</code>), "
        "bot kerakli musiqani MP3 formatda yetkazib beradi!\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <i>Boshlash uchun havola yoki qo'shiq nomini yuboring!</i>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "📖 <b>Botdan foydalanish qo'llanmasi</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ <b>Havola orqali yuklash:</b>\n"
        "• Ijtimoiy tarmoqdan havolani nusxalab botga yuboring.\n"
        "• Istalgan sifatni (720p HD, 1080p FHD yoki MP3) tanlang.\n\n"
        "2️⃣ <b>Qo'shiq nomi orqali qidirish:</b>\n"
        "• Istalgan qo'shiq nomini yozib yuboring (masalan: <code>Konsta - Odamlar</code>).\n"
        "• Chiqqan ro'yxatdan kerakli raqamni (1️⃣, 2️⃣, 3️⃣...) bosing.\n"
        "• Bot qo'shiqni to'liq MP3 formatda, muqovasi bilan yuboradi.\n\n"
        "⚠️ <b>Cheklov:</b> Telegram orqali maksimal fayl hajmi 50 MB.\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Savol yoki takliflar bo'lsa, adminga murojaat qiling.</i>"
    )
    await message.answer(text, parse_mode="HTML")
