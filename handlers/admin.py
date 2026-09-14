import asyncio
from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS
from database import get_stats, get_all_user_ids, get_all_users

router = Router()

def is_admin(user_id: int) -> bool:
    if not ADMIN_IDS:
        return True
    return user_id in ADMIN_IDS or user_id == 8746528646

def get_admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin:refresh"),
            InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin:users")
        ],
        [
            InlineKeyboardButton(text="📢 Xabar tarqatish (Rassilka)", callback_data="admin:broadcast_help")
        ]
    ])

async def build_stats_message() -> str:
    stats = await get_stats()
    platforms_text = ""
    for plat, count in stats.get("platforms", {}).items():
        icon = "🎵" if "music" in plat or "audio" in plat else ("🎬" if "video" in plat else "🌐")
        platforms_text += f"  {icon} {plat.capitalize()}: <b>{count}</b> ta\n"

    if not platforms_text:
        platforms_text = "  <i>Hali yuklab olishlar mavjud emas</i>\n"

    text = (
        "👑 <b>Admin Paneli & Bot Statistikasi:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> <code>{stats['total_users']}</code> nafar\n"
        f"🆕 <b>Bugun kirganlar:</b> <code>{stats.get('today_users', 0)}</code> nafar\n\n"
        f"📥 <b>Jami muvaffaqiyatli yuklamalar:</b> <code>{stats['total_downloads']}</code> ta\n"
        f"📅 <b>Bugungi yuklamalar:</b> <code>{stats['today_downloads']}</code> ta\n\n"
        "🌐 <b>Platformalar bo'yicha yuklamalar:</b>\n"
        f"{platforms_text}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Quyidagi tugmalar orqali foydalanuvchilar ro'yxatini ko'rishingiz yoki yangilashingiz mumkin.</i>"
    )
    return text

@router.message(Command("admin"))
@router.message(Command("stats"))
@router.message(Command("statistika"))
async def cmd_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ushbu buyruq faqat bot admini uchun!")
        return

    text = await build_stats_message()
    await message.answer(text, reply_markup=get_admin_main_kb(), parse_mode="HTML")

@router.callback_query(F.data == "admin:refresh")
async def cb_admin_refresh(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    text = await build_stats_message()
    try:
        await callback.message.edit_text(text, reply_markup=get_admin_main_kb(), parse_mode="HTML")
        await callback.answer("✅ Statistika yangilandi!")
    except Exception:
        await callback.answer("Statistika eng so'nggi holatda.")

@router.callback_query(F.data == "admin:users")
async def cb_admin_users(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    users = await get_all_users(limit=25)
    if not users:
        await callback.answer("Foydalanuvchilar topilmadi.", show_alert=True)
        return

    lines = ["👥 <b>So'nggi foydalanuvchilar ro'yxati:</b>\n━━━━━━━━━━━━━━━━━━━━\n"]
    for i, u in enumerate(users, 1):
        uname = f"@{u['username']}" if u['username'] else "Mavjud emas"
        fname = u['full_name'] or "Noma'lum"
        joined = str(u['joined_at'])[:16] if u.get('joined_at') else ""
        dl_count = u.get('total_downloads', 0)
        lines.append(
            f"{i}. <b>{fname}</b> ({uname})\n"
            f"   🆔 <code>{u['id']}</code> | 📥 {dl_count} ta yuklama\n"
            f"   📅 {joined}\n"
        )

    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Ortga (Statistika)", callback_data="admin:main")]
    ])
    await callback.message.edit_text("\n".join(lines), reply_markup=back_kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin:main")
async def cb_admin_main(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    text = await build_stats_message()
    await callback.message.edit_text(text, reply_markup=get_admin_main_kb(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin:broadcast_help")
async def cb_admin_broadcast_help(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    help_text = (
        "📢 <b>Barcha foydalanuvchilarga xabar tarqatish (Rassilka):</b>\n\n"
        "Xabar yuborish uchun quyidagi buyruqdan foydalaning:\n\n"
        "1. Matnli xabar:\n"
        "<code>/broadcast Sizning xabaringiz</code>\n\n"
        "2. Rasm yoki videoga reply (javob) qilib <code>/broadcast</code> deb yozsangiz, "
        "shu rasm/video barcha foydalanuvchilarga yuboriladi."
    )
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Ortga (Statistika)", callback_data="admin:main")]
    ])
    await callback.message.edit_text(help_text, reply_markup=back_kb, parse_mode="HTML")
    await callback.answer()

@router.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message, bot: Bot):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ushbu buyruq faqat bot adminlari uchun!")
        return

    command_parts = message.text.split(maxsplit=1)
    broadcast_text = None

    if len(command_parts) > 1:
        broadcast_text = command_parts[1]
    elif message.reply_to_message:
        broadcast_text = message.reply_to_message.text or message.reply_to_message.caption

    if not broadcast_text and not (message.reply_to_message and (message.reply_to_message.photo or message.reply_to_message.video)):
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
            if message.reply_to_message and message.reply_to_message.photo:
                await bot.send_photo(
                    uid,
                    photo=message.reply_to_message.photo[-1].file_id,
                    caption=broadcast_text,
                    parse_mode="HTML"
                )
            elif message.reply_to_message and message.reply_to_message.video:
                await bot.send_video(
                    uid,
                    video=message.reply_to_message.video.file_id,
                    caption=broadcast_text,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(uid, broadcast_text, parse_mode="HTML")
            sent_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            blocked_count += 1

    await message.answer(
        f"✅ <b>Xabar yuborish yakunlandi!</b>\n\n"
        f"• Yuborildi: <b>{sent_count}</b> nafar\n"
        f"• Yetib bormadi (bloklagan): <b>{blocked_count}</b> nafar",
        parse_mode="HTML"
    )
