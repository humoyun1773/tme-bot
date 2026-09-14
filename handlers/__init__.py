from .start import router as start_router
from .admin import router as admin_router
from .downloader import router as downloader_router

__all__ = ["start_router", "admin_router", "downloader_router"]
