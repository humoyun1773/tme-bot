import re
from typing import Tuple, Optional

# Havolalarni aniqlash uchun regex andozalari
PATTERNS = {
    "youtube": re.compile(
        r"(https?://)?(www\.|m\.)?(youtube\.com/(?:watch\?v=|shorts/|live/|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})"
    ),
    "instagram": re.compile(
        r"(https?://)?(www\.)?instagram\.com/(?:p|reel|reels|tv|stories)/([a-zA-Z0-9_\-\.]+)"
    ),
    "tiktok": re.compile(
        r"(https?://)?(www\.|vm\.|vt\.)?tiktok\.com/(@[a-zA-Z0-9_\.]+/video/\d+|[a-zA-Z0-9_\-\.]+)"
    ),
    "twitter": re.compile(
        r"(https?://)?(www\.)?(twitter\.com|x\.com)/[a-zA-Z0-9_]+/status/\d+"
    ),
    "facebook": re.compile(
        r"(https?://)?(www\.|m\.|fb\.)?(facebook\.com|fb\.watch)/"
    ),
    "pinterest": re.compile(
        r"(https?://)?(www\.|pin\.)?pinterest\.(com|[a-z]{2})/|pin\.it/"
    ),
    "soundcloud": re.compile(
        r"(https?://)?(www\.)?soundcloud\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+"
    )
}

GENERAL_URL_PATTERN = re.compile(r"https?://[^\s]+")

def extract_url(text: str) -> Optional[str]:
    """Matn ichidan birinchi to'liq URL manzilni ajratib oladi."""
    if not text:
        return None
    match = GENERAL_URL_PATTERN.search(text)
    return match.group(0) if match else None

def detect_platform(url: str) -> Tuple[str, str]:
    """
    URL qaysi platformaga tegishli ekanini aniqlaydi.
    Qaytaradi: (platform_nomi, tozalangan_url)
    """
    for platform, pattern in PATTERNS.items():
        if pattern.search(url):
            return platform, url

    # Umumiy yt-dlp qo'llab-quvvatlaydigan boshqa manbalar
    if GENERAL_URL_PATTERN.match(url):
        return "other", url

    return "unknown", url
