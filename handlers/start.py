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
        "Men <b>Musiqa & Media Yuklovchi Bot</b>man 🚀\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎧 <b>Qo'shiq qidirish:</b>\n"
        "Shunchaki qo'shiq yoki ijrochi nomini yozing (masalan: <code>Ummon - Sensiz</code>), "
        "bot eng sara 5 ta variantni topib, MP3 formatda yetkazib beradi!\n\n"
        "📥 <b>Havola orqali yuklash:</b>\n"
        "• 🔴 <b>YouTube:</b> Video va Audio (128, 192, 320 kbps)\n"
        "• 📷 <b>Instagram:</b> Reels, Post, Karusel, Stories\n"
        "• 🎵 <b>TikTok:</b> Suv belgisiz video va musiqa\n"
        "• 🐦 <b>Twitter / X, Pinterest:</b> Video va rasmlar\n\n"
        "⭐️ <b>Qo'shimcha buyruqlar:</b>\n"
        "• /history — Oxirgi yuklab olingan qo'shiqlar tarixi\n"
        "• /favorites — Sevimli qo'shiqlar ro'yxati\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <i>Boshlash uchun havola yoki qo'shiq nomini yuboring!</i>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "📖 <b>Botdan foydalanish qo'llanmasi</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ <b>Qo'shiq nomi bo'yicha qidirish:</b>\n"
        "• Istalgan qo'shiq nomini yozib yuboring (masalan: <code>Konsta - Odamlar</code>).\n"
        "• Chiqqan ro'yxatdan kerakli raqamni (1️⃣, 2️⃣, 3️⃣...) bosing.\n"
        "• Bot qo'shiqni to'liq MP3 formatda, muqovasi bilan yuboradi.\n\n"
        "2️⃣ <b>Havola orqali yuklash:</b>\n"
        "• YouTube, Instagram yoki TikTok havolasini yuboring.\n"
        "• Video sifati yoki audio bitrate (128k, 192k, 320k) ni tanlang.\n\n"
        "3️⃣ <b>Tarix va Sevimlilar:</b>\n"
        "• /history — Oxirgi 10 ta yuklagan qo'shiqlaringizni ko'rish va qayta yuklash.\n"
        "• /favorites — Sevimlilar ro'yxati. Har bir qo'shiq ostidagi ❤️ tugmasini bosib saqlab qo'yishingiz mumkin.\n\n"
        "⚠️ <b>Cheklov:</b> Telegram orqali maksimal fayl hajmi 50 MB.\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Savol yoki takliflar bo'lsa, adminga murojaat qiling.</i>"
    )
    await message.answer(text, parse_mode="HTML")
