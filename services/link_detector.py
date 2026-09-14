import re
from typing import Tuple, Optional

# Aniq platforma regex andozalari
PATTERNS = {
    "youtube": re.compile(
        r"(https?://)?((?:www\.|m\.|music\.)?youtube\.com/(?:watch\?v=|shorts/|live/|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})",
        re.IGNORECASE
    ),
    "instagram": re.compile(
        r"(https?://)?((?:www\.)?instagram\.com/(?:p|reel|reels|tv|stories)/[a-zA-Z0-9_\-\.]+)",
        re.IGNORECASE
    ),
    "tiktok": re.compile(
        r"(https?://)?((?:www\.|vm\.|vt\.)?tiktok\.com/(?:@[a-zA-Z0-9_\.]+/video/\d+|[a-zA-Z0-9_\-\.]+))",
        re.IGNORECASE
    ),
    "twitter": re.compile(
        r"(https?://)?((?:www\.)?(?:twitter\.com|x\.com)/[a-zA-Z0-9_]+/status/\d+)",
        re.IGNORECASE
    ),
    "facebook": re.compile(
        r"(https?://)?((?:www\.|m\.|fb\.)?(?:facebook\.com|fb\.watch)/[^\s]+)",
        re.IGNORECASE
    ),
    "pinterest": re.compile(
        r"(https?://)?((?:www\.|pin\.)?(?:pinterest\.(?:com|[a-z]{2})|pin\.it)/[^\s]+)",
        re.IGNORECASE
    ),
    "soundcloud": re.compile(
        r"(https?://)?((?:www\.)?soundcloud\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)",
        re.IGNORECASE
    )
}

# Umumiy havolalarni (http/https yoki domen bilan) aniqlash
GENERAL_URL_REGEX = re.compile(
    r"(https?://[^\s]+)|((?:[a-zA-Z0-9-]+\.)*(?:youtube\.com|youtu\.be|instagram\.com|tiktok\.com|twitter\.com|x\.com|facebook\.com|fb\.watch|pinterest\.com|pin\.it|soundcloud\.com)/[^\s]+)",
    re.IGNORECASE
)

CLEAN_TRAILING = ".,!?)>\"'`:;]"

def extract_url(text: str) -> Optional[str]:
    """
    Matn ichidan havolani ajratib oladi.
    Agar foydalanuvchi 'https://' siz yozsa ham (masalan: instagram.com/reel/...) to'g'ri taniydi.
    """
    if not text:
        return None

    match = GENERAL_URL_REGEX.search(text)
    if not match:
        return None

    url = match.group(0).rstrip(CLEAN_TRAILING)

    # Agar protokol bo'lmasa, https:// qo'shamiz
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url

def detect_platform(url: str) -> Tuple[str, str]:
    """
    URL qaysi platformaga tegishli ekanini aniqlaydi.
    """
    for platform, pattern in PATTERNS.items():
        if pattern.search(url):
            return platform, url

    if url.startswith(("http://", "https://")):
        return "other", url

    return "unknown", url
