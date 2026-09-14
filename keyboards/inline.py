import uuid
from typing import Dict, List, Optional, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

URL_CACHE: Dict[str, str] = {}
SONG_INFO_CACHE: Dict[str, Dict[str, Any]] = {}
SEARCH_CACHE: Dict[str, Dict[str, Any]] = {}

def store_url_in_cache(url: str) -> str:
    key = uuid.uuid4().hex[:10]
    URL_CACHE[key] = url
    if len(URL_CACHE) > 1000:
        oldest_key = next(iter(URL_CACHE))
        URL_CACHE.pop(oldest_key, None)
    return key

def get_url_from_cache(key: str) -> Optional[str]:
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

def store_search_cache(query: str, results: List[Dict[str, Any]]) -> str:
    key = uuid.uuid4().hex[:10]
    SEARCH_CACHE[key] = {"query": query, "results": results}
    if len(SEARCH_CACHE) > 1000:
        oldest_key = next(iter(SEARCH_CACHE))
        SEARCH_CACHE.pop(oldest_key, None)
    return key

def get_search_cache(key: str) -> Optional[Dict[str, Any]]:
    return SEARCH_CACHE.get(key)

def format_duration(seconds: int | float | None) -> str:
    if not seconds:
        return "Noma'lum"
    s = int(seconds)
    mins = s // 60
    secs = s % 60
    return f"{mins}:{secs:02d}"

def get_quality_keyboard(cache_key: str, available_formats: List[str] = None) -> InlineKeyboardMarkup:
    """
    Havolalar uchun Video va Audio yuklash tugmalari.
    """
    buttons = [
        [InlineKeyboardButton(text="🗂 Video", callback_data=f"dl:best:{cache_key}")],
        [InlineKeyboardButton(text="🎵 Audio (MP3)", callback_data=f"dl:mp3_192:{cache_key}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_search_results_keyboard(
    results: List[Dict[str, Any]], 
    cache_key: str = "", 
    page: int = 0, 
    page_size: int = 10,
    mode: str = "audio"
) -> InlineKeyboardMarkup:
    """
    Musiqa qidiruvi uchun raqamli tugmalar va [ ⬅️ ] [ ❌ ] [ ➡️ ] navigatsiyasi:
    [ 1 ] [ 2 ] [ 3 ] [ 4 ] [ 5 ]
    [ 6 ] [ 7 ] [ 8 ] [ 9 ] [ 10 ]
    [ ⬅️ ] [ ❌ ] [ ➡️ ]
    """
    start_idx = page * page_size
    page_results = results[start_idx : start_idx + page_size]

    prefix = "song:"
    row1 = []
    row2 = []
    for i, item in enumerate(page_results, start=start_idx + 1):
        btn = InlineKeyboardButton(text=str(i), callback_data=f"{prefix}{item['id']}")
        if len(row1) < 5:
            row1.append(btn)
        else:
            row2.append(btn)

    nav_row = [
        InlineKeyboardButton(text="⬅️", callback_data=f"page:{cache_key}:{page - 1}"),
        InlineKeyboardButton(text="❌", callback_data="close_search"),
        InlineKeyboardButton(text="➡️", callback_data=f"page:{cache_key}:{page + 1}")
    ]

    buttons = []
    if row1:
        buttons.append(row1)
    if row2:
        buttons.append(row2)
    buttons.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_audio_sent_keyboard() -> InlineKeyboardMarkup:
    """
    Qo'shiq yuborilgandagi yagona tugma: faqat Guruhga qo'shish ⤴️
    """
    buttons = [
        [InlineKeyboardButton(text="Guruhga qo'shish ⤴️", url="https://t.me/audio_x_bot?startgroup=true")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_video_sent_keyboard(cache_key: str) -> InlineKeyboardMarkup:
    """
    Video yuborilgandagi tugmalar:
    1. Musiqani yuklash
    2. Guruhga qo'shish
    """
    buttons = [
        [InlineKeyboardButton(text="🎵 Musiqani yuklab olish", callback_data=f"dl:mp3_160:{cache_key}")],
        [InlineKeyboardButton(text="Guruhga qo'shish ⤴️", url="https://t.me/audio_x_bot?startgroup=true")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_retry_keyboard(cache_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Qayta urinib ko'rish", callback_data=f"dl:best:{cache_key}")]
    ])
