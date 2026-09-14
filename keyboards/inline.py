import uuid
from typing import Dict, List, Optional, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

URL_CACHE: Dict[str, str] = {}

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
    Sifat tanlash uchun zamonaviy va chiroyli inline tugmalar.
    """
    buttons = []

    # Agar formatlar bo'lsa, HD va SD qilib ajratamiz
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
    buttons.append([
        InlineKeyboardButton(text="🎵 Faqat audio (MP3)", callback_data=f"dl:audio:{cache_key}")
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

    # Tugmalarni ixcham qatorga joylaymiz
    buttons = [number_buttons]
    buttons.append([
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_search")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_retry_keyboard(cache_key: str) -> InlineKeyboardMarkup:
    """Xatolik yuz berganda qayta urinish tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Qayta urinib ko'rish", callback_data=f"dl:best:{cache_key}")]
    ])
