import asyncio
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
import yt_dlp

from config import DOWNLOADS_DIR, FFMPEG_PATH, MAX_FILE_SIZE_BYTES

# Umumiy yt-dlp standart opsiyalari
BASE_YTDL_OPTS = {
    "outtmpl": str(DOWNLOADS_DIR / "%(id)s_%(epoch)s.%(ext)s"),
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "socket_timeout": 30,
}

if FFMPEG_PATH:
    BASE_YTDL_OPTS["ffmpeg_location"] = FFMPEG_PATH

async def get_media_info(url: str) -> Optional[Dict[str, Any]]:
    """
    Havola haqidagi asosiy ma'lumotlarni (sarlavha, davomiyligi, mavjud sifatlar) oladi.
    """
    opts = dict(BASE_YTDL_OPTS)
    opts["extract_flat"] = "in_playlist"

    def _extract():
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    try:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, _extract)
        if not info:
            return None

        # Agar playlist bo'lmasa yoki bitta video bo'lsa
        title = info.get("title", "Noma'lum kontent")
        duration = info.get("duration", 0)
        thumbnail = info.get("thumbnail")
        uploader = info.get("uploader") or info.get("channel", "Noma'lum muallif")

        # Mavjud sifatlarni aniqlash
        available_formats = set()
        formats = info.get("formats") or []
        for f in formats:
            h = f.get("height")
            if h:
                if h >= 1080:
                    available_formats.add("1080p")
                elif h >= 720:
                    available_formats.add("720p")
                elif h >= 480:
                    available_formats.add("480p")
                elif h >= 360:
                    available_formats.add("360p")

        # Agar entries bo'lsa (Instagram karusel yoki postlar)
        is_carousel = False
        entries_count = 0
        if "entries" in info and info["entries"]:
            is_carousel = True
            entries_count = len(list(info["entries"]))

        return {
            "title": title,
            "duration": duration,
            "thumbnail": thumbnail,
            "uploader": uploader,
            "available_formats": sorted(list(available_formats)),
            "is_carousel": is_carousel,
            "entries_count": entries_count,
            "raw_info": info
        }
    except Exception as e:
        print(f"Ma'lumot olishda xatolik: {e}")
        return None

async def download_media(url: str, quality: str = "best", is_audio: bool = False) -> Dict[str, Any]:
    """
    Media (video, audio yoki rasm) yuklab oladi.
    Qaytaradi: {
        "status": "success" | "size_exceeded" | "error",
        "type": "video" | "audio" | "photo" | "album",
        "files": [list of filepaths],
        "title": title,
        "duration": duration,
        "error_message": str
    }
    """
    unique_sub = DOWNLOADS_DIR / f"job_{uuid.uuid4().hex[:8]}"
    unique_sub.mkdir(parents=True, exist_ok=True)
    out_template = str(unique_sub / "%(title).80s_%(id)s.%(ext)s")

    opts = dict(BASE_YTDL_OPTS)
    opts["outtmpl"] = out_template
    opts["noplaylist"] = True

    if is_audio:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        if quality == "1080p":
            opts["format"] = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
        elif quality == "720p":
            opts["format"] = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
        elif quality == "480p":
            opts["format"] = "bestvideo[height<=480]+bestaudio/best[height<=480]/best"
        elif quality == "360p":
            opts["format"] = "bestvideo[height<=360]+bestaudio/best[height<=360]/best"
        else:
            opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        opts["merge_output_format"] = "mp4"

    def _do_download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, _do_download)

        # Yuklangan fayllarni topish
        downloaded_files = list(unique_sub.glob("*"))
        if not downloaded_files:
            return {
                "status": "error",
                "error_message": "Fayl yuklab olinmadi.",
                "temp_dir": unique_sub
            }

        title = info.get("title", "Fayl") if info else "Fayl"
        duration = info.get("duration", 0) if info else 0

        # Fayl hajmini tekshirish (Telegram Bot API 50 MB limiti)
        total_size = sum(f.stat().st_size for f in downloaded_files)
        if total_size > MAX_FILE_SIZE_BYTES:
            return {
                "status": "size_exceeded",
                "size_mb": round(total_size / (1024 * 1024), 1),
                "temp_dir": unique_sub,
                "files": downloaded_files,
                "title": title
            }

        # Fayl turlarini aniqlash
        if is_audio:
            media_type = "audio"
        elif len(downloaded_files) > 1:
            media_type = "album"
        else:
            single = downloaded_files[0]
            ext = single.suffix.lower()
            if ext in [".jpg", ".jpeg", ".png", ".webp"]:
                media_type = "photo"
            elif ext in [".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav"]:
                media_type = "audio"
            else:
                media_type = "video"

        return {
            "status": "success",
            "type": media_type,
            "files": downloaded_files,
            "title": title,
            "duration": duration,
            "temp_dir": unique_sub
        }

    except yt_dlp.utils.DownloadError as de:
        err = str(de)
        msg = "Kontent topilmadi yoki bu hisob yopiq (private)."
        if "login" in err.lower() or "private" in err.lower():
            msg = "Kechirasiz, bu profil/kontent yopiq (private) yoki avtorizatsiya talab qiladi."
        elif "copyright" in err.lower():
            msg = "Bu kontent mualliflik huquqi sababli bloklangan."
        return {
            "status": "error",
            "error_message": msg,
            "temp_dir": unique_sub
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Kutilmagan xatolik yuz berdi: {str(e)[:150]}",
            "temp_dir": unique_sub
        }
