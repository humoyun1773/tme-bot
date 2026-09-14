import os
import shutil
from pathlib import Path
from config import DOWNLOADS_DIR

def remove_file(filepath: str | Path | list[str | Path] | None):
    """Vaqtinchalik yuklangan fayl yoki fayllar ro'yxatini xavfsiz o'chiradi."""
    if not filepath:
        return

    if isinstance(filepath, (list, tuple)):
        for f in filepath:
            remove_file(f)
        return

    try:
        p = Path(filepath)
        if p.is_file() or p.is_symlink():
            p.unlink(missing_ok=True)
        elif p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
    except Exception as e:
        print(f"Faylni o'chirishda xatolik: {filepath} -> {e}")

def clean_downloads_folder():
    """downloads papkasidagi barcha qolib ketgan vaqtinchalik fayllarni tozalaydi."""
    try:
        for item in DOWNLOADS_DIR.iterdir():
            if item.is_file():
                item.unlink(missing_ok=True)
            elif item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
    except Exception as e:
        print(f"Downloads papkasini tozalashda xatolik: {e}")
