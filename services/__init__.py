from .link_detector import detect_platform, extract_url
from .media_downloader import get_media_info, download_media
from .cleanup import remove_file, clean_downloads_folder
from .search_service import search_music

__all__ = [
    "detect_platform",
    "extract_url",
    "get_media_info",
    "download_media",
    "remove_file",
    "clean_downloads_folder",
    "search_music",
]
