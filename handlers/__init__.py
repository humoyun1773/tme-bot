from .start import router as start_router
from .admin import router as admin_router
from .downloader import router as downloader_router
from .music_features import router as music_features_router

__all__ = ["start_router", "admin_router", "downloader_router", "music_features_router"]
