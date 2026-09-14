import uuid
from typing import Dict, List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Callback_data 64 baytlik chekloviga tushmasligi uchun URL larni qisqa ID bilan keshda saqlaymiz
URL_CACHE: Dict[str, str] = {}

def store_url_in_cache(url: str) -> str:
    """URL ni keshda saqlab, qisqa kalit qaytaradi."""
    key = uuid.uuid4().hex[:10]
    URL_CACHE[key] = url
    # Kesh hajmini cheklash (oxirgi 1000 ta havola)
    if len(URL_CACHE) > 1000:
        oldest_key = next(iter(URL_CACHE))
        URL_CACHE.pop(oldest_key, None)
    return key

def get_url_from_cache(key: str) -> Optional[str]:
    """Qisqa kalit bo'yicha URL ni oladi."""
    return URL_CACHE.get(key)

def get_quality_keyboard(cache_key: str, available_formats: List[str] = None) -> InlineKeyboardMarkup:
    """
    Sifat tanlash uchun inline tugmalar yaratadi.
    """
    buttons = []

    # Agar YouTube bo'lib, aniq formatlar berilgan bo'lsa
    if available_formats:
        row = []
        if "360p" in available_formats:
            row.append(InlineKeyboardButton(text="🎬 360p", callback_data=f"dl:360p:{cache_key}"))
        if "480p" in available_formats:
            row.append(InlineKeyboardButton(text="🎬 480p", callback_data=f"dl:480p:{cache_key}"))
        if row:
            buttons.append(row)

        row2 = []
        if "720p" in available_formats:
            row2.append(InlineKeyboardButton(text="🎬 720p HD", callback_data=f"dl:720p:{cache_key}"))
        if "1080p" in available_formats:
            row2.append(InlineKeyboardButton(text="🎬 1080p FHD", callback_data=f"dl:1080p:{cache_key}"))
        if row2:
            buttons.append(row2)

    # Standart tezkor yuklash va Audio tugmalari
    buttons.append([
        InlineKeyboardButton(text="⚡ Eng yaxshi sifat (Video)", callback_data=f"dl:best:{cache_key}")
    ])
    buttons.append([
        InlineKeyboardButton(text="🎵 Faqat audio (MP3)", callback_data=f"dl:audio:{cache_key}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_retry_keyboard(cache_key: str) -> InlineKeyboardMarkup:
    """Xatolik yuz berganda qayta urinish tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Qayta urinib ko'rish", callback_data=f"dl:best:{cache_key}")]
    ])
