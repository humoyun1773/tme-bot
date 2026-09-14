import uuid
from typing import Dict, List, Optional, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

URL_CACHE: Dict[str, str] = {}
SONG_INFO_CACHE: Dict[str, Dict[str, Any]] = {}

def store_url_in_cache(url: str) -> str:
    """URL ni keshda saqlab, qisqa kalit qaytaradi."""
    key = uuid.uuid4().hex[:10]
    URL_CACHE[key] = url
    if len(URL_CACHE) > 1000:
        oldest_key = next(iter(URL_CACHE))
        URL_CACHE.pop(oldest_key, None)
    return key

def get_url_from_cache(key: str) -> Optional[str]:
    """Qisqa kalit bo'yicha URL ni oladi."""
    return URL_CACHE.get(key)

def store_song_info(info: Dict[str, Any]) -> str:
    key = uuid.uuid4().hex[:10]
    SONG_INFO_CACHE[key] = info
    if len(SONG_INFO_CACHE) > 1000:
        oldest_key = next(iter(SONG_INFO_CACHE))
        SONG_INFO_CACHE.pop(oldest_key, None)
    return key

def get_song_info(key: str) -> Optional[Dict[str, Any]]:
    return SONG_INFO_CACHE.get(key)

def format_duration(seconds: int | float | None) -> str:
    if not seconds:
        return "Noma'lum"
    s = int(seconds)
    mins = s // 60
    secs = s % 60
    return f"{mins}:{secs:02d}"

NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

def get_quality_keyboard(cache_key: str, available_formats: List[str] = None) -> InlineKeyboardMarkup:
    """
    Video va Audio sifatlarini (Bitrate) tanlash uchun inline tugmalar.
    """
    buttons = []

    # Video sifatlari
    if available_formats:
        hd_row = []
        if "720p" in available_formats:
            hd_row.append(InlineKeyboardButton(text="🎬 720p HD", callback_data=f"dl:720p:{cache_key}"))
        if "1080p" in available_formats:
            hd_row.append(InlineKeyboardButton(text="🎬 1080p FHD", callback_data=f"dl:1080p:{cache_key}"))
        if hd_row:
            buttons.append(hd_row)

        sd_row = []
        if "360p" in available_formats:
            sd_row.append(InlineKeyboardButton(text="📱 360p", callback_data=f"dl:360p:{cache_key}"))
        if "480p" in available_formats:
            sd_row.append(InlineKeyboardButton(text="📺 480p", callback_data=f"dl:480p:{cache_key}"))
        if sd_row:
            buttons.append(sd_row)

    buttons.append([
        InlineKeyboardButton(text="⚡ Eng yaxshi sifat (Video)", callback_data=f"dl:best:{cache_key}")
    ])

    # Audio bitrate tanlovlari
    buttons.append([
        InlineKeyboardButton(text="🎵 MP3 320k (HD)", callback_data=f"dl:mp3_320:{cache_key}"),
        InlineKeyboardButton(text="🎵 MP3 192k", callback_data=f"dl:mp3_192:{cache_key}"),
        InlineKeyboardButton(text="🎵 MP3 128k", callback_data=f"dl:mp3_128:{cache_key}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_search_results_keyboard(results: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Qo'shiq qidiruv natijalari uchun ixcham va estetik raqamli tugmalar qatori.
    """
    number_buttons = []
    for i, item in enumerate(results):
        emoji_num = NUMBER_EMOJIS[i] if i < len(NUMBER_EMOJIS) else f"[{i+1}]"
        number_buttons.append(
            InlineKeyboardButton(text=emoji_num, callback_data=f"song:{item['id']}")
        )

    buttons = [number_buttons]
    buttons.append([
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_search")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_song_action_keyboard(song_key: str, is_fav: bool = False) -> InlineKeyboardMarkup:
    """
    Yuborilgan qo'shiq ostidagi sevimli qilish tugmasi.
    """
    if is_fav:
        btn_text = "💔 Sevimlilardan o'chirish"
        cb_data = f"fav:del:{song_key}"
    else:
        btn_text = "❤️ Sevimlilarga qo'shish"
        cb_data = f"fav:add:{song_key}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_text, callback_data=cb_data)]
    ])

def get_retry_keyboard(cache_key: str) -> InlineKeyboardMarkup:
    """Xatolik yuz berganda qayta urinish tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Qayta urinib ko'rish", callback_data=f"dl:best:{cache_key}")]
    ])
