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
        "Men <b>Universal Media Downloader</b> botiman. 📥\n\n"
        "Menga quyidagi ijtimoiy tarmoqlardan havola (link) yuboring:\n"
        "• 🔴 <b>YouTube</b> (Video, Shorts, MP3 qo'shiq)\n"
        "• 📷 <b>Instagram</b> (Reels, Post, Karusel, Stories)\n"
        "• 🎵 <b>TikTok</b> (Suv belgisiz video, Musiqa)\n"
        "• 🐦 <b>Twitter / X</b> (Videolar)\n"
        "• 📌 <b>Pinterest</b> (Rasm va videolar)\n\n"
        "<i>Shunchaki havolani yuboring va sifatini tanlang!</i>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "📖 <b>Botdan foydalanish qo'llanmasi:</b>\n\n"
        "1️⃣ Ijtimoiy tarmoqdan (masalan, Instagram yoki YouTube) kerakli kontent havolasini nusxalang.\n"
        "2️⃣ Botga havolani xabar sifatida yuboring.\n"
        "3️⃣ Kerakli formatni tanlang (masalan, <b>720p HD</b> yoki <b>🎵 MP3</b>).\n"
        "4️⃣ Bot videoni yoki musiqani tez fursatda sizga yuboradi!\n\n"
        "⚠️ <b>Cheklovlar:</b>\n"
        "• Telegram orqali yuboriladigan fayllarning maksimal hajmi <b>50 MB</b>.\n"
        "• Yopiq (private) profillardagi kontentlarni yuklab bo'lmaydi.\n\n"
        "Savol yoki takliflar bo'lsa, adminga murojaat qiling."
    )
    await message.answer(text, parse_mode="HTML")
