import os
import logging
from aiogram import Router, types, F
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from database import increment_download, add_user
from services import (
    extract_url,
    detect_platform,
    get_media_info,
    download_media,
    search_music,
    remove_file
)
from keyboards import (
    store_url_in_cache,
    get_url_from_cache,
    get_quality_keyboard,
    get_search_results_keyboard,
    get_retry_keyboard,
    format_duration
)
from keyboards.inline import NUMBER_EMOJIS

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text & ~F.text.startswith("/"))
async def handle_incoming_text(message: types.Message):
    user = message.from_user
    if user:
        await add_user(user.id, user.username, user.full_name)

    text = message.text.strip()
    url = extract_url(text)

    # 1. AGAR HAVOLA (URL) BO'LSA
    if url:
        platform, clean_url = detect_platform(url)
        if platform == "unknown":
            await message.answer(
                "❌ <b>Kechirasiz, bu havola qo'llab-quvvatlanmaydi.</b>\n\n"
                "Qo'llab-quvvatlanadigan platformalar:\n"
                "• YouTube, Instagram, TikTok, Twitter/X, Pinterest va b.",
                parse_mode="HTML"
            )
            return

        status_msg = await message.answer("🔍 <i>Havola tahlil qilinmoqda...</i>", parse_mode="HTML")

        info = await get_media_info(clean_url)
        if not info:
            await status_msg.edit_text(
                "❌ <b>Kontent topilmadi yoki bu hisob yopiq (private).</b>\n"
                "Iltimos, havolani tekshirib qaytadan yuboring.",
                parse_mode="HTML"
            )
            await increment_download(user.id, platform, clean_url, status="failed")
            return

        cache_key = store_url_in_cache(clean_url)
        title = info.get("title", "Media")
        uploader = info.get("uploader", "Noma'lum")
        duration = format_duration(info.get("duration"))
        available_formats = info.get("available_formats", [])

        caption = (
            f"🎬 <b>{title}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Kanal / Muallif:</b> {uploader}\n"
            f"⏱ <b>Davomiyligi:</b> {duration}\n"
            f"🌐 <b>Platforma:</b> {platform.capitalize()}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👇 <i>Kerakli sifat yoki formatni tanlang:</i>"
        )

        kb = get_quality_keyboard(cache_key, available_formats)
        await status_msg.edit_text(caption, parse_mode="HTML", reply_markup=kb)
        return

    # 2. AGAR ODDIY MATN BO'LSA -> QO'SHIQ QIDIRUVI
    query = text
    status_msg = await message.answer(
        f"🔎 <i>«{query}» bo'yicha qo'shiqlar qidirilmoqda...</i>",
        parse_mode="HTML"
    )

    results = await search_music(query, limit=5)
    if not results:
        await status_msg.edit_text(
            "❌ <b>Kechirasiz, bunday qo'shiq topilmadi.</b>\n"
            "Boshqacha nom yoki ijrochi nomi bilan qayta urinib ko'ring.",
            parse_mode="HTML"
        )
        return

    songs_list_text = (
        f"🎧 <b>Musiqa qidiruvi:</b> <i>«{query}»</i>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    for i, r in enumerate(results):
        emoji_num = NUMBER_EMOJIS[i] if i < len(NUMBER_EMOJIS) else f"{i+1}."
        dur = format_duration(r.get("duration"))
        title = r.get("title", "Noma'lum")
        uploader = r.get("uploader", "Noma'lum ijrochi")
        songs_list_text += (
            f"{emoji_num} <b>{title}</b>\n"
            f"    👤 <i>{uploader}</i>  •  ⏱ <code>{dur}</code>\n\n"
        )

    songs_list_text += (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <i>Yuklab olish uchun quyidagi raqamlardan birini bosing:</i>"
    )

    kb = get_search_results_keyboard(results)
    await status_msg.edit_text(songs_list_text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("song:"))
async def handle_song_download_callback(callback: types.CallbackQuery):
    await callback.answer("⏳ Qo'shiq yuklanmoqda...")
    video_id = callback.data.split(":", 1)[1]
    song_url = f"https://www.youtube.com/watch?v={video_id}"
    user_id = callback.from_user.id

    # Asosiy qidiruv xabarini o'chirmaymiz!
    status_msg = await callback.message.answer(
        "⏳ <b>Qo'shiq yuklanmoqda...</b>\n"
        "<i>MP3 formatga o'tkazilib, muqova rasmi va teglari joylanmoqda...</i>",
        parse_mode="HTML"
    )

    res = await download_media(song_url, is_audio=True)
    temp_dir = res.get("temp_dir")

    try:
        if res["status"] == "error":
            err = res.get("error_message", "Noma'lum xatolik")
            await status_msg.edit_text(
                f"❌ <b>Qo'shiqni yuklashda xatolik yuz berdi:</b>\n{err}",
                parse_mode="HTML"
            )
            await increment_download(user_id, "music_search", song_url, status="failed")
            return

        if res["status"] == "size_exceeded":
            await status_msg.edit_text(
                "⚠️ <b>Fayl hajmi 50 MB dan oshib ketdi.</b> Telegram orqali yuborib bo'lmadi.",
                parse_mode="HTML"
            )
            await increment_download(user_id, "music_search", song_url, status="size_exceeded")
            return

        files = res.get("files", [])
        if not files:
            await status_msg.edit_text("❌ Audio fayl topilmadi.")
            return

        mp3_file = files[0]
        title = res.get("title", "Qo'shiq")
        uploader = res.get("uploader", "Ijrochi")
        duration = int(res.get("duration", 0))
        thumbnail = res.get("thumbnail")

        thumb_input = FSInputFile(str(thumbnail)) if (thumbnail and thumbnail.is_file()) else None

        await callback.message.answer_audio(
            audio=FSInputFile(str(mp3_file)),
            title=title,
            performer=uploader,
            duration=duration,
            thumbnail=thumb_input,
            caption=(
                f"🎵 <b>{title}</b>\n"
                f"👤 <i>{uploader}</i>\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "🤖 @audio_x_bot orqali yuklandi"
            ),
            parse_mode="HTML"
        )

        await increment_download(user_id, "music_search", song_url, status="success")

        # Status xabarini o'chirish
        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Audio yuborishda xatolik: {e}")
        try:
            await status_msg.edit_text(f"❌ Xatolik yuz berdi: {str(e)[:100]}")
        except Exception:
            pass
    finally:
        remove_file(temp_dir)


@router.callback_query(F.data == "cancel_search")
async def handle_cancel_search(callback: types.CallbackQuery):
    await callback.answer("Qidiruv bekor qilindi")
    try:
        await callback.message.delete()
    except Exception:
        await callback.message.edit_text("❌ Qidiruv bekor qilindi.")


@router.callback_query(F.data.startswith("dl:"))
async def handle_download_callback(callback: types.CallbackQuery):
    await callback.answer("⏳ Yuklab olish boshlandi...")
    data_parts = callback.data.split(":")
    if len(data_parts) < 3:
        return

    quality = data_parts[1]
    cache_key = data_parts[2]
    url = get_url_from_cache(cache_key)

    if not url:
        await callback.message.answer(
            "⚠️ Havola eskirgan. Iltimos, havolani qaytadan yuboring."
        )
        return

    platform, _ = detect_platform(url)
    user_id = callback.from_user.id

    status_msg = await callback.message.answer(
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
            await status_msg.edit_text(
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
            await status_msg.edit_text(
                f"❌ <b>Yuklashda xatolik yuz berdi:</b>\n{err}",
                parse_mode="HTML",
                reply_markup=kb
            )
            await increment_download(user_id, platform, url, status="failed")
            return

        # Muvaffaqiyatli yuklandi -> Telegramga jo'natish
        media_type = res.get("type")
        files = res.get("files", [])
        title = res.get("title", "Yuklangan media")
        uploader = res.get("uploader", "Noma'lum")
        duration = int(res.get("duration", 0))
        thumbnail = res.get("thumbnail")
        thumb_input = FSInputFile(str(thumbnail)) if (thumbnail and thumbnail.is_file()) else None
        bot_mention = "🤖 @audio_x_bot orqali yuklandi"

        caption_text = (
            f"🎬 <b>{title}</b>\n"
            f"👤 <i>{uploader}</i>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"{bot_mention}"
        )

        if media_type == "audio":
            for f in files:
                audio_file = FSInputFile(str(f))
                await callback.message.answer_audio(
                    audio=audio_file,
                    title=title,
                    performer=uploader,
                    duration=duration,
                    thumbnail=thumb_input,
                    caption=(
                        f"🎵 <b>{title}</b>\n"
                        f"👤 <i>{uploader}</i>\n\n"
                        "━━━━━━━━━━━━━━━━━━━━\n"
                        f"{bot_mention}"
                    ),
                    parse_mode="HTML"
                )
        elif media_type == "photo":
            for f in files:
                photo_file = FSInputFile(str(f))
                await callback.message.answer_photo(
                    photo=photo_file,
                    caption=caption_text,
                    parse_mode="HTML"
                )
        elif media_type == "album":
            media_group = []
            for f in files[:10]:
                ext = f.suffix.lower()
                if ext in [".jpg", ".jpeg", ".png", ".webp"]:
                    media_group.append(InputMediaPhoto(media=FSInputFile(str(f))))
                else:
                    media_group.append(InputMediaVideo(media=FSInputFile(str(f))))

            if media_group:
                media_group[0].caption = caption_text
                media_group[0].parse_mode = "HTML"
                await callback.message.answer_media_group(media=media_group)
        else:
            for f in files:
                video_file = FSInputFile(str(f))
                await callback.message.answer_video(
                    video=video_file,
                    caption=caption_text,
                    parse_mode="HTML"
                )

        await increment_download(user_id, platform, url, status="success")

        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Fayl yuborishda xatolik: {e}")
        try:
            await status_msg.edit_text(f"❌ Fayl yuborishda xatolik: {str(e)[:100]}")
        except Exception:
            pass
    finally:
        remove_file(temp_dir)
