import os
from aiogram import Router, types, F
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from database import increment_download, add_user
from services import (
    extract_url,
    detect_platform,
    get_media_info,
    download_media,
    remove_file
)
from keyboards import (
    store_url_in_cache,
    get_url_from_cache,
    get_quality_keyboard,
    get_retry_keyboard
)

router = Router()

def format_duration(seconds: int | float | None) -> str:
    if not seconds:
        return "Noma'lum"
    s = int(seconds)
    mins = s // 60
    secs = s % 60
    return f"{mins}:{secs:02d}"

@router.message(F.text)
async def handle_link_message(message: types.Message):
    # Foydalanuvchini bazaga qo'shish
    user = message.from_user
    if user:
        await add_user(user.id, user.username, user.full_name)

    text = message.text.strip()
    url = extract_url(text)

    if not url:
        # Foydalanuvchi oddiy matn yuborgan bo'lsa
        await message.answer(
            "ℹ️ Iltimos, YouTube, Instagram yoki TikTok havolasini (link) yuboring.\n"
            "Yordam uchun: /help",
            parse_mode="HTML"
        )
        return

    platform, clean_url = detect_platform(url)
    if platform == "unknown":
        await message.answer(
            "❌ Kechirasiz, bu havola qo'llab-quvvatlanmaydi.\n"
            "Qo'llab-quvvatlanadigan platformalar: YouTube, Instagram, TikTok, Twitter/X, Pinterest va b.",
            parse_mode="HTML"
        )
        return

    status_msg = await message.answer("🔍 Havola tahlil qilinmoqda...")

    info = await get_media_info(clean_url)
    if not info:
        await status_msg.edit_text(
            "❌ Kontent topilmadi yoki ushbu hisob yopiq (private).\n"
            "Iltimos, havolani tekshirib qayta yuboring."
        )
        await increment_download(user.id, platform, clean_url, status="failed")
        return

    cache_key = store_url_in_cache(clean_url)
    title = info.get("title", "Media")
    uploader = info.get("uploader", "Noma'lum")
    duration = format_duration(info.get("duration"))
    available_formats = info.get("available_formats", [])

    caption = (
        f"🎬 <b>{title}</b>\n\n"
        f"👤 Muallif: <b>{uploader}</b>\n"
        f"⏱ Davomiyligi: <b>{duration}</b>\n"
        f"🌐 Manba: <b>{platform.capitalize()}</b>\n\n"
        "⬇️ <i>Kerakli sifat yoki formatni tanlang:</i>"
    )

    kb = get_quality_keyboard(cache_key, available_formats)
    await status_msg.edit_text(caption, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data.startswith("dl:"))
async def handle_download_callback(callback: types.CallbackQuery):
    await callback.answer()
    data_parts = callback.data.split(":")
    if len(data_parts) < 3:
        return

    quality = data_parts[1]
    cache_key = data_parts[2]
    url = get_url_from_cache(cache_key)

    if not url:
        await callback.message.edit_text(
            "⚠️ Havola eskirgan. Iltimos, havolani qaytadan yuboring."
        )
        return

    platform, _ = detect_platform(url)
    user_id = callback.from_user.id

    await callback.message.edit_text(
        "⏳ <b>Yuklanmoqda...</b>\n"
        "<i>Fayl hajmiga qarab bir necha soniya vaqt olishi mumkin. Iltimos kuting.</i>",
        parse_mode="HTML"
    )

    is_audio = (quality == "audio")
    res = await download_media(url, quality=quality, is_audio=is_audio)
    temp_dir = res.get("temp_dir")

    try:
        if res["status"] == "size_exceeded":
            size_mb = res.get("size_mb", 0)
            kb = get_quality_keyboard(cache_key)
            await callback.message.edit_text(
                f"⚠️ <b>Fayl hajmi juda katta ({size_mb} MB)!</b>\n"
                "Telegram bot orqali maksimal 50 MB gacha fayl yuborish mumkin.\n\n"
                "Iltimos, pastroq sifatni yoki faqat <b>🎵 Audio (MP3)</b> variantini tanlang:",
                parse_mode="HTML",
                reply_markup=kb
            )
            await increment_download(user_id, platform, url, status="size_exceeded")
            return

        if res["status"] == "error":
            err = res.get("error_message", "Noma'lum xatolik")
            kb = get_retry_keyboard(cache_key)
            await callback.message.edit_text(
                f"❌ <b>Yuklashda xatolik yuz berdi:</b>\n{err}",
                parse_mode="HTML",
                reply_markup=kb
            )
            await increment_download(user_id, platform, url, status="failed")
            return

        # Muvaffaqiyatli yuklandi -> Telegramga jo'natish
        await callback.message.edit_text("📤 <b>Telegramga yuborilmoqda...</b>", parse_mode="HTML")

        media_type = res.get("type")
        files = res.get("files", [])
        title = res.get("title", "Yuklangan media")
        bot_mention = "@audio_x_bot orqali yuklandi"

        if media_type == "audio":
            for f in files:
                audio_file = FSInputFile(str(f))
                await callback.message.answer_audio(
                    audio=audio_file,
                    caption=f"🎵 <b>{title}</b>\n\n🤖 {bot_mention}",
                    parse_mode="HTML"
                )
        elif media_type == "photo":
            for f in files:
                photo_file = FSInputFile(str(f))
                await callback.message.answer_photo(
                    photo=photo_file,
                    caption=f"📷 <b>{title}</b>\n\n🤖 {bot_mention}",
                    parse_mode="HTML"
                )
        elif media_type == "album":
            # Instagram karusel yoki bir nechta fayllar
            media_group = []
            for f in files[:10]:  # Telegram media guruhida maksimal 10 ta
                ext = f.suffix.lower()
                if ext in [".jpg", ".jpeg", ".png", ".webp"]:
                    media_group.append(InputMediaPhoto(media=FSInputFile(str(f))))
                else:
                    media_group.append(InputMediaVideo(media=FSInputFile(str(f))))
            
            if media_group:
                media_group[0].caption = f"📦 <b>{title}</b>\n\n🤖 {bot_mention}"
                media_group[0].parse_mode = "HTML"
                await callback.message.answer_media_group(media=media_group)
        else:
            # Standart video
            for f in files:
                video_file = FSInputFile(str(f))
                await callback.message.answer_video(
                    video=video_file,
                    caption=f"🎬 <b>{title}</b>\n\n🤖 {bot_mention}",
                    parse_mode="HTML"
                )

        await increment_download(user_id, platform, url, status="success")
        # Jarayon xabarini tozalash
        try:
            await callback.message.delete()
        except Exception:
            pass

    finally:
        # Vaqtinchalik fayllarni o'chirish
        remove_file(temp_dir)
