import os
from pathlib import Path
from dotenv import load_dotenv

# .env faylini yuklash
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN ko'rsatilmagan! Iltimos, .env faylini tekshiring.")

# Admin ID larini olish
admin_ids_raw = os.getenv("ADMIN_IDS", "").strip()
ADMIN_IDS = [int(i.strip()) for i in admin_ids_raw.split(",") if i.strip().isdigit()]
if 8746528646 not in ADMIN_IDS:
    ADMIN_IDS.append(8746528646)

# Fayl hajmi chegarasi (Telegram botlar uchun 50 MB)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Vaqtinchalik yuklamalar papkasi
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Ma'lumotlar bazasi fayli
DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "bot_database.db")

# Rate limit (soniyalarda)
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "3"))

# FFmpeg yo'lini aniqlash
def get_ffmpeg_path() -> str | None:
    try:
        import shutil
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            return system_ffmpeg
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None

FFMPEG_PATH = get_ffmpeg_path()
