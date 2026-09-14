import asyncio
from aiogram import Router, types, Bot
from aiogram.filters import Command
from config import ADMIN_IDS
from database import get_stats, get_all_user_ids

router = Router()

def is_admin(user_id: int) -> bool:
    if not ADMIN_IDS:
        return True  # Agar admin belgilanmagan bo'lsa, test uchun ruxsat beriladi
    return user_id in ADMIN_IDS

@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ushbu buyruq faqat bot adminlari uchun!")
        return

    stats = await get_stats()
    platforms_text = ""
    for plat, count in stats.get("platforms", {}).items():
        platforms_text += f"  • {plat.capitalize()}: <b>{count}</b> ta\n"

    if not platforms_text:
        platforms_text = "  <i>Hali yuklab olishlar yo'q</i>\n"

    text = (
        "📊 <b>Bot Statistikasi:</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b> nafar\n"
        f"📥 Jami muvaffaqiyatli yuklamalar: <b>{stats['total_downloads']}</b> ta\n"
        f"📅 Bugungi yuklamalar: <b>{stats['today_downloads']}</b> ta\n\n"
        "🌐 <b>Platformalar bo'yicha:</b>\n"
        f"{platforms_text}"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message, bot: Bot):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ushbu buyruq faqat bot adminlari uchun!")
        return

    # Xabar matnini olish
    command_parts = message.text.split(maxsplit=1)
    broadcast_text = None

    if len(command_parts) > 1:
        broadcast_text = command_parts[1]
    elif message.reply_to_message:
        broadcast_text = message.reply_to_message.text or message.reply_to_message.caption

    if not broadcast_text:
        await message.answer(
            "❗ Xabar yuborish uchun quyidagicha foydalaning:\n"
            "<code>/broadcast Sizning xabaringiz</code>\n"
            "yoki xabarga reply qilib <code>/broadcast</code> deb yozing."
        )
        return

    user_ids = await get_all_user_ids()
    await message.answer(f"📢 Xabar {len(user_ids)} ta foydalanuvchiga yuborilmoqda...")

    sent_count = 0
    blocked_count = 0

    for uid in user_ids:
        try:
            await bot.send_message(uid, broadcast_text, parse_mode="HTML")
            sent_count += 1
            await asyncio.sleep(0.05)  # Flood limitidan saqlanish
        except Exception:
            blocked_count += 1

    await message.answer(
        f"✅ <b>Xabar yuborish yakunlandi!</b>\n\n"
        f"• Yuborildi: <b>{sent_count}</b>\n"
        f"• Yetib bormadi (bloklagan): <b>{blocked_count}</b>",
        parse_mode="HTML"
    )
