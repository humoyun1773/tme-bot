import asyncio
import logging
import os
import sys
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, BASE_DIR
from database import init_db
from services import clean_downloads_folder
from handlers import start_router, admin_router, downloader_router

# Log sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

PID_FILE = BASE_DIR / "bot.pid"

def acquire_pid_lock():
    """Faqat bitta bot nusxasi ishlashini kafolatlaydi."""
    current_pid = os.getpid()
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            if old_pid != current_pid:
                logger.warning(f"Eski bot jarayoni aniqlandi (PID {old_pid}).")
        except Exception:
            pass
    PID_FILE.write_text(str(current_pid))

def release_pid_lock():
    try:
        if PID_FILE.exists():
            PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass

async def main():
    acquire_pid_lock()
    logger.info("Bot ishga tushirilmoqda...")

    # Baza va fayl tizimini tayyorlash
    await init_db()
    clean_downloads_folder()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Routerlarni ulash
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(downloader_router)

    # Eski pending xabarlarni tozalash
    await bot.delete_webhook(drop_pending_updates=True)

    bot_info = await bot.get_me()
    logger.info(f"Bot muvaffaqiyatli ishga tushdi: @{bot_info.username} ({bot_info.first_name})")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        release_pid_lock()
        logger.info("Bot to'xtatildi.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        release_pid_lock()
        logger.info("Bot qo'lda to'xtatildi.")
