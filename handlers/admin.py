import asyncio
from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS
from database import get_stats, get_all_user_ids, get_all_users, find_user, get_user_history

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
            InlineKeyboardButton(text="🔍 Userni qidirish", callback_data="admin:search_prompt"),
            InlineKeyboardButton(text="📢 Xabar tarqatish", callback_data="admin:broadcast_help")
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
        f"👥 <b>Jami botga kirganlar:</b> <code>{stats['total_users']}</code> nafar\n"
        f"🆕 <b>Bugun yangi kirganlar:</b> <code>{stats.get('today_users', 0)}</code> nafar\n\n"
        f"📥 <b>Jami muvaffaqiyatli yuklamalar:</b> <code>{stats['total_downloads']}</code> ta\n"
        f"📅 <b>Bugungi yuklamalar:</b> <code>{stats['today_downloads']}</code> ta\n\n"
        "🌐 <b>Platformalar bo'yicha yuklamalar:</b>\n"
        f"{platforms_text}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔍 <i>Foydalanuvchini tekshirish: <code>/user @username</code> yoki <code>/user ID</code></i>"
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

    lines = [
        f"👥 <b>Bot foydalanuvchilari (Jami: {len(users)} nafar):</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
    ]
    for i, u in enumerate(users, 1):
        uname = f"@{u['username']}" if u['username'] else "<i>username yo'q</i>"
        fname = u['full_name'] or "Noma'lum"
        visits = u.get('visits_count') or 1
        dl_count = u.get('total_downloads', 0)
        last_act = str(u.get('last_active') or u.get('joined_at') or '')[:16]

        lines.append(
            f"{i}. <b>{fname}</b> ({uname})\n"
            f"   🆔 <code>{u['id']}</code>\n"
            f"   🔄 <b>Kirishlar:</b> {visits} marta | 📥 <b>Yuklamalar:</b> {dl_count} ta\n"
            f"   ⏰ <b>Oxirgi kirish:</b> {last_act}\n"
        )

    lines.append("━━━━━━━━━━━━━━━━━━━━\n💡 <i>Batafsil tekshirish: <code>/user @username</code></i>")

    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin:users"),
            InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin:main")
        ]
    ])
    await callback.message.edit_text("\n".join(lines), reply_markup=back_kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin:search_prompt")
async def cb_admin_search_prompt(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    help_text = (
        "🔍 <b>Foydalanuvchini qidirish:</b>\n\n"
        "Istalgan foydalanuvchini topish va uning nechta kirishi borligini ko'rish uchun "
        "quyidagi buyruqni yuboring:\n\n"
        "• Username orqali: <code>/user @username</code>\n"
        "• Telegram ID orqali: <code>/user 123456789</code>\n\n"
        "<i>Masalan: <code>/user @Xumoyun_711</code></i>"
    )
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Ortga (Statistika)", callback_data="admin:main")]
    ])
    await callback.message.edit_text(help_text, reply_markup=back_kb, parse_mode="HTML")
    await callback.answer()

@router.message(Command("user"))
@router.message(Command("find"))
@router.message(Command("qidir"))
async def cmd_find_user(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ushbu buyruq faqat bot admini uchun!")
        return

    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "❗ Qidirish uchun username yoki ID ni yozing:\n"
            "Masalan: <code>/user @Xumoyun_711</code> yoki <code>/user 8746528646</code>",
            parse_mode="HTML"
        )
        return

    query = parts[1].strip()
    u = await find_user(query)

    if not u:
        await message.answer(
            f"❌ <b>'{query}'</b> bo'yicha hech qanday foydalanuvchi topilmadi.\n"
            "Username yoki ID to'g'riligini tekshirib qayta urinib ko'ring.",
            parse_mode="HTML"
        )
        return

    uname = f"@{u['username']}" if u['username'] else "Mavjud emas"
    fname = u['full_name'] or "Noma'lum"
    visits = u.get('visits_count') or 1
    downloads = u.get('total_downloads', 0)
    joined = str(u.get('joined_at', ''))[:19]
    last_act = str(u.get('last_active', ''))[:19]

    history = await get_user_history(u['id'], limit=5)
    history_text = ""
    if history:
        for idx, item in enumerate(history, 1):
            song = item.get("song_title") or "Fayl"
            perf = item.get("performer") or ""
            dt = str(item.get("created_at") or "")[:16]
            history_text += f"  {idx}. {song} - {perf} (<i>{dt}</i>)\n"
    else:
        history_text = "  <i>Hali musiqa yuklab olmagan</i>\n"

    report = (
        "👤 <b>Foydalanuvchi hisoboti (Haqiqiy baza ma'lumotlari):</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Ism-familiya:</b> <b>{fname}</b>\n"
        f"🔗 <b>Username:</b> {uname}\n"
        f"🆔 <b>Telegram ID:</b> <code>{u['id']}</code>\n\n"
        "📊 <b>Faollik ko'rsatkichlari:</b>\n"
        f"🔄 <b>Botga kirishlar (murojaatlar):</b> <b>{visits}</b> marta\n"
        f"📥 <b>Jami yuklab olganlari:</b> <b>{downloads}</b> ta\n"
        f"📅 <b>Birinchi kirgan vaqti:</b> {joined}\n"
        f"⏰ <b>Oxirgi kirgan vaqti:</b> {last_act}\n\n"
        "🎵 <b>Oxirgi yuklagan fayllari:</b>\n"
        f"{history_text}"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(report, parse_mode="HTML")

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
