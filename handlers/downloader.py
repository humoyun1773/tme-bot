import asyncio
import os
import logging
from aiogram import Router, types, F
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from database import (
    increment_download,
    add_user,
    get_cached_file,
    set_cached_file
)
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
    store_search_cache,
    get_search_cache,
    get_quality_keyboard,
    get_search_results_keyboard,
    get_audio_sent_keyboard,
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

async def keep_chat_action(bot, chat_id: int, action: str):
    """Yuklash davomida Telegramda uzluksiz 'yuborilmoqda...' indikatorini ko'rsatish."""
    try:
        while True:
            await bot.send_chat_action(chat_id, action)
            await asyncio.sleep(4)
    except asyncio.CancelledError:
        pass
    except Exception:
        pass


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

    # 2. AGAR ODDIY MATN BO'LSA -> QO'SHIQ QIDIRUVI
    query = text
    status_msg = await message.answer("🔍 Qidirilmoqda...")

    results = await search_music(query, limit=10)
    if not results:
        await status_msg.edit_text("❌ Hech narsa topilmadi.")
        return

    search_key = store_search_cache(query, results)
    msg_text = build_search_message_text(query, results, mode="audio")
    kb = get_search_results_keyboard(results, search_key, mode="audio")

    await status_msg.edit_text(msg_text, reply_markup=kb)


@router.callback_query(F.data.startswith("mode:"))
async def handle_mode_toggle(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) < 3:
        return

    new_mode = parts[1]
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
    video_id = callback.data.split(":", 1)[1]
    song_url = f"https://www.youtube.com/watch?v={video_id}"
    user_id = callback.from_user.id
    kb = get_audio_sent_keyboard()

    # 1. Tezkor kesh (agar oldin yuklangan bo'lsa 0.2 soniyada yuboriladi!)
    cached_file_id = await get_cached_file(song_url, "audio")
    if cached_file_id:
        await callback.answer("⚡ Yuborilmoqda...")
        try:
            await callback.message.answer_audio(
                audio=cached_file_id,
                caption=BOT_PROMO,
                reply_markup=kb
            )
            await increment_download(user_id, "music_search", song_url, status="success")
            return
        except Exception:
            pass  # Agar eski file_id eskirgan bo'lsa, qayta yuklaymiz

    await callback.answer("⚡ Yuklanmoqda...")
    status_msg = await callback.message.reply("⚡ <i>Yuklanmoqda...</i>", parse_mode="HTML")
    action_task = asyncio.create_task(keep_chat_action(callback.bot, callback.message.chat.id, "upload_voice"))

    res = await download_media(song_url, is_audio=True, bitrate="160")
    temp_dir = res.get("temp_dir")

    try:
        action_task.cancel()
        if res["status"] != "success":
            err = res.get("error_message", "Yuklab bo'lmadi.")
            await status_msg.edit_text(f"❌ {err}")
            await increment_download(user_id, "music_search", song_url, status="failed")
            return

        files = res.get("files", [])
        if not files:
            await status_msg.edit_text("❌ Audio topilmadi.")
            return

        mp3_file = files[0]
        title = res.get("title", "Qo'shiq")
        uploader = res.get("uploader", "Ijrochi")
        duration = int(res.get("duration", 0))

        sent_msg = await callback.message.answer_audio(
            audio=FSInputFile(str(mp3_file)),
            title=title,
            performer=uploader,
            duration=duration,
            caption=BOT_PROMO,
            reply_markup=kb
        )

        # Telegram serverlaridagi file_id ni keshga saqlash (keyingi safar 0.2s da yuborish uchun)
        if sent_msg.audio:
            await set_cached_file(song_url, sent_msg.audio.file_id, "audio")

        await increment_download(user_id, "music_search", song_url, status="success", title=title, performer=uploader)

        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Audio yuborishda xatolik: {e}")
        try:
            await status_msg.edit_text("❌ Yuklashda xatolik yuz berdi.")
        except Exception:
            pass
    finally:
        remove_file(temp_dir)


@router.callback_query(F.data.startswith("vsong:"))
async def handle_vsong_download(callback: types.CallbackQuery):
    video_id = callback.data.split(":", 1)[1]
    song_url = f"https://www.youtube.com/watch?v={video_id}"
    user_id = callback.from_user.id
    kb = get_audio_sent_keyboard()

    # Kesh tekshirish
    cached_file_id = await get_cached_file(song_url, "video")
    if cached_file_id:
        await callback.answer("⚡ Yuborilmoqda...")
        try:
            await callback.message.answer_video(
                video=cached_file_id,
                caption=BOT_PROMO,
                reply_markup=kb
            )
            await increment_download(user_id, "video_search", song_url, status="success")
            return
        except Exception:
            pass

    await callback.answer("⚡ Video yuklanmoqda...")
    status_msg = await callback.message.reply("⚡ <i>Video yuklanmoqda...</i>", parse_mode="HTML")
    action_task = asyncio.create_task(keep_chat_action(callback.bot, callback.message.chat.id, "upload_video"))

    res = await download_media(song_url, quality="best", is_audio=False)
    temp_dir = res.get("temp_dir")

    try:
        action_task.cancel()
        if res["status"] != "success":
            err = res.get("error_message", "Videoni yuklab bo'lmadi.")
            await status_msg.edit_text(f"❌ {err}")
            await increment_download(user_id, "video_search", song_url, status="failed")
            return

        files = res.get("files", [])
        if not files:
            await status_msg.edit_text("❌ Video topilmadi.")
            return

        video_file = files[0]
        title = res.get("title", "Video")
        uploader = res.get("uploader", "Muallif")

        sent_msg = await callback.message.answer_video(
            video=FSInputFile(str(video_file)),
            caption=BOT_PROMO,
            reply_markup=kb
        )

        if sent_msg.video:
            await set_cached_file(song_url, sent_msg.video.file_id, "video")

        await increment_download(user_id, "video_search", song_url, status="success", title=title, performer=uploader)

        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Video yuborishda xatolik: {e}")
        try:
            await status_msg.edit_text("❌ Videoni yuklashda xatolik yuz berdi.")
        except Exception:
            pass
    finally:
        remove_file(temp_dir)


@router.callback_query(F.data.startswith("dl:"))
async def handle_download_callback(callback: types.CallbackQuery):
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
    media_key = "audio" if is_audio else "video"

    kb = get_audio_sent_keyboard()

    cached_file_id = await get_cached_file(url, media_key)
    if cached_file_id:
        await callback.answer("⚡ Yuborilmoqda...")
        try:
            if is_audio:
                await callback.message.answer_audio(audio=cached_file_id, caption=BOT_PROMO, reply_markup=kb)
            else:
                await callback.message.answer_video(video=cached_file_id, caption=BOT_PROMO, reply_markup=kb)
            await increment_download(user_id, platform, url, status="success")
            return
        except Exception:
            pass

    await callback.answer("⚡ Yuklanmoqda...")
    status_msg = await callback.message.reply("⚡ <i>Yuklanmoqda...</i>", parse_mode="HTML")
    action_type = "upload_voice" if is_audio else "upload_video"
    action_task = asyncio.create_task(keep_chat_action(callback.bot, callback.message.chat.id, action_type))

    bitrate = "160"
    if quality == "mp3_128":
        bitrate = "128"
    elif quality == "mp3_320":
        bitrate = "320"

    res = await download_media(url, quality=quality, is_audio=is_audio, bitrate=bitrate)
    temp_dir = res.get("temp_dir")

    try:
        action_task.cancel()
        if res["status"] != "success":
            err = res.get("error_message", "Yuklab bo'lmadi.")
            await status_msg.edit_text(f"❌ {err}")
            await increment_download(user_id, platform, url, status="failed")
            return

        media_type = res.get("type")
        files = res.get("files", [])
        title = res.get("title", "Media")
        uploader = res.get("uploader", "Noma'lum")
        duration = int(res.get("duration", 0))

        if media_type == "audio":
            for f in files:
                sent_msg = await callback.message.answer_audio(
                    audio=FSInputFile(str(f)),
                    title=title,
                    performer=uploader,
                    duration=duration,
                    caption=BOT_PROMO,
                    reply_markup=kb
                )
                if sent_msg.audio:
                    await set_cached_file(url, sent_msg.audio.file_id, "audio")
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
            for f in files:
                sent_msg = await callback.message.answer_video(
                    video=FSInputFile(str(f)),
                    caption=BOT_PROMO,
                    reply_markup=kb
                )
                if sent_msg.video:
                    await set_cached_file(url, sent_msg.video.file_id, "video")

        await increment_download(user_id, platform, url, status="success", title=title, performer=uploader)

        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Fayl yuborishda xatolik: {e}")
        try:
            await status_msg.edit_text("❌ Yuklashda xatolik yuz berdi.")
        except Exception:
            pass
    finally:
        remove_file(temp_dir)
