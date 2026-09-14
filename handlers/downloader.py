import os
import logging
from aiogram import Router, types, F
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from database import increment_download, add_user, is_favorite
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
    store_song_info,
    store_search_cache,
    get_search_cache,
    get_quality_keyboard,
    get_search_results_keyboard,
    get_audio_sent_keyboard,
    get_retry_keyboard,
    format_duration
)

logger = logging.getLogger(__name__)
router = Router()

BOT_PROMO = "@audio_x_bot orqali istagan musiqangizni tez va oson toping!"

def build_search_message_text(query: str, results: list, mode: str = "audio") -> str:
    icon = "🎵" if mode == "audio" else "🎬"
    suffix = "" if mode == "audio" else " (Video)"
    lines = [f"{icon} {query}{suffix}\n"]
    for i, r in enumerate(results, 1):
        dur = format_duration(r.get("duration"))
        title = r.get("title", "Noma'lum")
        lines.append(f"{i}. {title} {dur}")
    return "\n".join(lines)


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
                "❌ Kechirasiz, bu havola qo'llab-quvvatlanmaydi.\n"
                "Qo'llab-quvvatlanadigan platformalar: YouTube, Instagram, TikTok, Twitter/X, Pinterest va b."
            )
            return

        status_msg = await message.answer("🔍 Qidirilmoqda...")

        info = await get_media_info(clean_url)
        if not info:
            await status_msg.edit_text("❌ Kontent topilmadi yoki bu hisob yopiq (private).")
            await increment_download(user.id, platform, clean_url, status="failed")
            return

        cache_key = store_url_in_cache(clean_url)
        title = info.get("title", "Media")
        duration = format_duration(info.get("duration"))

        caption = f"🎬 {title} {duration}"
        kb = get_quality_keyboard(cache_key)
        await status_msg.edit_text(caption, reply_markup=kb)
        return

    # 2. AGAR ODDIY MATN BO'LSA -> QO'SHIQ QIDIRUVI (2-skrinshotdagi aniq format)
    query = text
    status_msg = await message.answer("🔍 Qidirilmoqda...")

    results = await search_music(query, limit=5)
    if not results:
        await status_msg.edit_text("❌ Hech narsa topilmadi.")
        return

    search_key = store_search_cache(query, results)
    msg_text = build_search_message_text(query, results, mode="audio")
    kb = get_search_results_keyboard(results, search_key, mode="audio")

    await status_msg.edit_text(msg_text, reply_markup=kb)


@router.callback_query(F.data.startswith("mode:"))
async def handle_mode_toggle(callback: types.CallbackQuery):
    """Audio va Video rejimlari o'rtasida o'tish (🗂 Video <-> 🎵 Audio)."""
    parts = callback.data.split(":")
    if len(parts) < 3:
        return

    new_mode = parts[1]  # "video" yoki "audio"
    search_key = parts[2]
    cache = get_search_cache(search_key)

    if not cache:
        await callback.answer("Qidiruv eskirgan. Qaytadan qidiring.", show_alert=True)
        return

    query = cache["query"]
    results = cache["results"]

    msg_text = build_search_message_text(query, results, mode=new_mode)
    kb = get_search_results_keyboard(results, search_key, mode=new_mode)

    await callback.message.edit_text(msg_text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("song:"))
async def handle_song_download(callback: types.CallbackQuery):
    """1, 2, 3, 4, 5 bosilganda MP3 Audio yuklash."""
    await callback.answer("⏳ Yuklanmoqda...", show_alert=False)
    video_id = callback.data.split(":", 1)[1]
    song_url = f"https://www.youtube.com/watch?v={video_id}"
    user_id = callback.from_user.id

    try:
        await callback.bot.send_chat_action(callback.message.chat.id, "upload_voice")
    except Exception:
        pass

    res = await download_media(song_url, is_audio=True, bitrate="192")
    temp_dir = res.get("temp_dir")

    try:
        if res["status"] != "success":
            err = res.get("error_message", "Yuklab bo'lmadi.")
            await callback.answer(f"Xatolik: {err}", show_alert=True)
            await increment_download(user_id, "music_search", song_url, status="failed")
            return

        files = res.get("files", [])
        if not files:
            await callback.answer("Audio topilmadi.", show_alert=True)
            return

        mp3_file = files[0]
        title = res.get("title", "Qo'shiq")
        uploader = res.get("uploader", "Ijrochi")
        duration = int(res.get("duration", 0))
        thumbnail = res.get("thumbnail")

        thumb_input = FSInputFile(str(thumbnail)) if (thumbnail and thumbnail.is_file()) else None

        song_key = store_song_info({
            "url": song_url,
            "title": title,
            "performer": uploader
        })

        is_fav = await is_favorite(user_id, song_url)
        kb = get_audio_sent_keyboard(song_key, is_fav=is_fav)

        await callback.message.answer_audio(
            audio=FSInputFile(str(mp3_file)),
            title=title,
            performer=uploader,
            duration=duration,
            thumbnail=thumb_input,
            caption=BOT_PROMO,
            reply_markup=kb
        )

        await increment_download(user_id, "music_search", song_url, status="success", title=title, performer=uploader)

    except Exception as e:
        logger.error(f"Audio yuborishda xatolik: {e}")
        await callback.answer("Xatolik yuz berdi.", show_alert=True)
    finally:
        remove_file(temp_dir)


@router.callback_query(F.data.startswith("vsong:"))
async def handle_vsong_download(callback: types.CallbackQuery):
    """1, 2, 3, 4, 5 Video rejimida bosilganda MP4 Video yuklash."""
    await callback.answer("⏳ Video yuklanmoqda...", show_alert=False)
    video_id = callback.data.split(":", 1)[1]
    song_url = f"https://www.youtube.com/watch?v={video_id}"
    user_id = callback.from_user.id

    try:
        await callback.bot.send_chat_action(callback.message.chat.id, "upload_video")
    except Exception:
        pass

    res = await download_media(song_url, quality="best", is_audio=False)
    temp_dir = res.get("temp_dir")

    try:
        if res["status"] != "success":
            err = res.get("error_message", "Videoni yuklab bo'lmadi.")
            await callback.answer(f"Xatolik: {err}", show_alert=True)
            await increment_download(user_id, "video_search", song_url, status="failed")
            return

        files = res.get("files", [])
        if not files:
            await callback.answer("Video topilmadi.", show_alert=True)
            return

        video_file = files[0]
        title = res.get("title", "Video")
        uploader = res.get("uploader", "Muallif")
        kb = get_audio_sent_keyboard()

        await callback.message.answer_video(
            video=FSInputFile(str(video_file)),
            caption=BOT_PROMO,
            reply_markup=kb
        )

        await increment_download(user_id, "video_search", song_url, status="success", title=title, performer=uploader)

    except Exception as e:
        logger.error(f"Video yuborishda xatolik: {e}")
        await callback.answer("Xatolik yuz berdi.", show_alert=True)
    finally:
        remove_file(temp_dir)


@router.callback_query(F.data.startswith("dl:"))
async def handle_download_callback(callback: types.CallbackQuery):
    await callback.answer("⏳ Yuklanmoqda...", show_alert=False)
    data_parts = callback.data.split(":")
    if len(data_parts) < 3:
        return

    quality = data_parts[1]
    cache_key = data_parts[2]
    url = get_url_from_cache(cache_key)

    if not url:
        await callback.answer("Havola eskirgan.", show_alert=True)
        return

    platform, _ = detect_platform(url)
    user_id = callback.from_user.id

    is_audio = quality.startswith("mp3_") or quality == "audio"
    bitrate = "192"

    try:
        action = "upload_voice" if is_audio else "upload_video"
        await callback.bot.send_chat_action(callback.message.chat.id, action)
    except Exception:
        pass

    res = await download_media(url, quality=quality, is_audio=is_audio, bitrate=bitrate)
    temp_dir = res.get("temp_dir")

    try:
        if res["status"] != "success":
            err = res.get("error_message", "Yuklab bo'lmadi.")
            await callback.answer(f"Xatolik: {err}", show_alert=True)
            await increment_download(user_id, platform, url, status="failed")
            return

        media_type = res.get("type")
        files = res.get("files", [])
        title = res.get("title", "Media")
        uploader = res.get("uploader", "Noma'lum")
        duration = int(res.get("duration", 0))
        thumbnail = res.get("thumbnail")
        thumb_input = FSInputFile(str(thumbnail)) if (thumbnail and thumbnail.is_file()) else None

        if media_type == "audio":
            song_key = store_song_info({
                "url": url,
                "title": title,
                "performer": uploader
            })
            is_fav = await is_favorite(user_id, url)
            kb = get_audio_sent_keyboard(song_key, is_fav=is_fav)

            for f in files:
                await callback.message.answer_audio(
                    audio=FSInputFile(str(f)),
                    title=title,
                    performer=uploader,
                    duration=duration,
                    thumbnail=thumb_input,
                    caption=BOT_PROMO,
                    reply_markup=kb
                )
        elif media_type == "photo":
            for f in files:
                await callback.message.answer_photo(
                    photo=FSInputFile(str(f)),
                    caption=BOT_PROMO
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
                media_group[0].caption = BOT_PROMO
                await callback.message.answer_media_group(media=media_group)
        else:
            kb = get_audio_sent_keyboard()
            for f in files:
                await callback.message.answer_video(
                    video=FSInputFile(str(f)),
                    caption=BOT_PROMO,
                    reply_markup=kb
                )

        await increment_download(user_id, platform, url, status="success", title=title, performer=uploader)

    except Exception as e:
        logger.error(f"Fayl yuborishda xatolik: {e}")
        await callback.answer("Xatolik yuz berdi.", show_alert=True)
    finally:
        remove_file(temp_dir)
