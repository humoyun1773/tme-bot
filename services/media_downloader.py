import asyncio
import os
import subprocess
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
import yt_dlp
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
from mutagen.mp3 import MP3

from config import DOWNLOADS_DIR, FFMPEG_PATH, MAX_FILE_SIZE_BYTES

# YouTube va boshqa platformalar uchun maksimal tezlik sozlamalari
BASE_YTDL_OPTS = {
    "outtmpl": str(DOWNLOADS_DIR / "%(id)s_%(epoch)s.%(ext)s"),
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "socket_timeout": 20,
    "buffersize": 1024 * 1024,
    "concurrent_fragment_downloads": 4,
    "extractor_args": {
        "youtube": {
            "player_client": ["android", "mweb"]
        }
    },
    "http_headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
}

if FFMPEG_PATH:
    BASE_YTDL_OPTS["ffmpeg_location"] = FFMPEG_PATH

async def get_media_info(url: str) -> Optional[Dict[str, Any]]:
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

        title = info.get("title", "Noma'lum kontent")
        duration = info.get("duration", 0) or 0
        thumbnail = info.get("thumbnail")
        uploader = info.get("uploader") or info.get("channel", "Noma'lum muallif")

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

        is_carousel = False
        entries_count = 0
        if "entries" in info and info["entries"]:
            is_carousel = True
            entries_count = len(list(info["entries"]))

        is_long = duration > 900

        return {
            "title": title,
            "duration": duration,
            "thumbnail": thumbnail,
            "uploader": uploader,
            "available_formats": sorted(list(available_formats)),
            "is_carousel": is_carousel,
            "entries_count": entries_count,
            "is_long": is_long,
            "raw_info": info
        }
    except Exception as e:
        print(f"Ma'lumot olishda xatolik: {e}")
        return None

def _apply_id3_tags(mp3_path: Path, title: str, artist: str):
    """MP3 faylga nom va ijrochini tezkor yozadi (ortiqcha kechikishsiz)."""
    try:
        try:
            audio = MP3(mp3_path, ID3=ID3)
            audio.add_tags()
        except Exception:
            audio = MP3(mp3_path, ID3=ID3)

        audio.tags.add(TIT2(encoding=3, text=title))
        audio.tags.add(TPE1(encoding=3, text=artist))
        audio.tags.add(TALB(encoding=3, text="Universal Media Bot"))
        audio.save()
    except Exception as e:
        pass

async def download_media(url: str, quality: str = "best", is_audio: bool = False, bitrate: str = "160") -> Dict[str, Any]:
    """
    Media yuklab oladi (video, audio yoki rasm).
    """
    unique_sub = DOWNLOADS_DIR / f"job_{uuid.uuid4().hex[:8]}"
    unique_sub.mkdir(parents=True, exist_ok=True)
    out_template = str(unique_sub / "%(title).80s_%(id)s.%(ext)s")

    opts = dict(BASE_YTDL_OPTS)
    opts["outtmpl"] = out_template
    opts["noplaylist"] = True

    if is_audio:
        opts["format"] = "bestaudio/best"
        audio_quality = bitrate if bitrate in ["128", "160", "192", "320"] else "160"
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": audio_quality,
            }
        ]
        opts["postprocessor_args"] = {
            "ffmpeg": ["-threads", "0"]
        }
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
        opts["postprocessor_args"] = {
            "ffmpeg": ["-threads", "0"]
        }

    def _do_download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, _do_download)

        downloaded_files = list(unique_sub.glob("*"))
        if not downloaded_files:
            return {
                "status": "error",
                "error_message": "Fayl yuklab olinmadi.",
                "temp_dir": unique_sub
            }

        title = info.get("title", "Fayl") if info else "Fayl"
        uploader = info.get("uploader") or info.get("channel", "Noma'lum ijrochi") if info else "Noma'lum"
        duration = info.get("duration", 0) if info else 0

        total_size = sum(f.stat().st_size for f in downloaded_files)
        if total_size > MAX_FILE_SIZE_BYTES:
            return {
                "status": "size_exceeded",
                "size_mb": round(total_size / (1024 * 1024), 1),
                "temp_dir": unique_sub,
                "files": downloaded_files,
                "title": title
            }

        if is_audio:
            media_type = "audio"
            mp3_files = [f for f in downloaded_files if f.suffix.lower() == ".mp3"]
            if not mp3_files:
                mp3_files = [f for f in downloaded_files if f.suffix.lower() in [".m4a", ".ogg", ".opus", ".wav"]]
            
            for m in mp3_files:
                if m.suffix.lower() == ".mp3":
                    _apply_id3_tags(m, title, uploader)

            return {
                "status": "success",
                "type": media_type,
                "files": mp3_files,
                "title": title,
                "uploader": uploader,
                "duration": duration,
                "thumbnail": None,
                "temp_dir": unique_sub
            }

        # Video / Photo / Album
        if len(downloaded_files) > 1:
            media_type = "album"
            files_to_send = downloaded_files
        else:
            files_to_send = downloaded_files
            single = files_to_send[0]
            ext = single.suffix.lower()
            if ext in [".jpg", ".jpeg", ".png", ".webp"]:
                media_type = "photo"
            else:
                media_type = "video"

        return {
            "status": "success",
            "type": media_type,
            "files": files_to_send,
            "title": title,
            "uploader": uploader,
            "duration": duration,
            "thumbnail": None,
            "temp_dir": unique_sub
        }

    except yt_dlp.utils.DownloadError as de:
        err = str(de)
        msg = "Kontent topilmadi yoki yuklab olishda muammo yuz berdi."
        if "login" in err.lower() or "private" in err.lower():
            msg = "Kechirasiz, bu profil/kontent yopiq (private) yoki avtorizatsiya talab qiladi."
        elif "copyright" in err.lower():
            msg = "Bu kontent mualliflik huquqi sababli bloklangan."
        elif "403" in err:
            msg = "Manbaga ulanishda vaqtinchalik cheklov (403). Iltimos, qayta urinib ko'ring."
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
