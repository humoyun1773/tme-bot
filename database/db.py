import aiosqlite
from datetime import datetime
from typing import Optional
from config import DATABASE_PATH

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_downloads INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS downloads_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                platform TEXT,
                link TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                song_title TEXT,
                performer TEXT,
                source_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                song_title TEXT,
                performer TEXT,
                source_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, source_url)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS file_cache (
                source_url TEXT PRIMARY KEY,
                file_id TEXT,
                media_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def get_cached_file(source_url: str, media_type: str = "audio") -> Optional[str]:
    """Tezkor yuklash: Telegram serverlaridagi file_id orqali 0.2 soniyada qaytarish."""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute(
                "SELECT file_id FROM file_cache WHERE source_url = ? AND media_type = ?",
                (source_url, media_type)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None
    except Exception:
        return None

async def set_cached_file(source_url: str, file_id: str, media_type: str = "audio"):
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                INSERT INTO file_cache (source_url, file_id, media_type)
                VALUES (?, ?, ?)
                ON CONFLICT(source_url) DO UPDATE SET
                    file_id = excluded.file_id,
                    media_type = excluded.media_type
            """, (source_url, file_id, media_type))
            await db.commit()
    except Exception:
        pass

async def add_user(user_id: int, username: str | None, full_name: str | None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO users (id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name
        """, (user_id, username, full_name))
        await db.commit()

async def increment_download(user_id: int, platform: str, link: str, status: str = "success", title: str = None, performer: str = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if status == "success":
            await db.execute("""
                UPDATE users
                SET total_downloads = total_downloads + 1
                WHERE id = ?
            """, (user_id,))
            if title:
                await db.execute("""
                    INSERT INTO downloads (user_id, song_title, performer, source_url)
                    VALUES (?, ?, ?, ?)
                """, (user_id, title, performer or "Noma'lum", link))

        await db.execute("""
            INSERT INTO downloads_log (user_id, platform, link, status)
            VALUES (?, ?, ?, ?)
        """, (user_id, platform, link, status))
        await db.commit()

async def get_user_history(user_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT song_title, performer, source_url, created_at 
            FROM downloads
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def add_to_favorites(user_id: int, song_title: str, performer: str, source_url: str) -> bool:
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                INSERT OR IGNORE INTO favorites (user_id, song_title, performer, source_url)
                VALUES (?, ?, ?, ?)
            """, (user_id, song_title, performer or "Noma'lum", source_url))
            await db.commit()
            return True
    except Exception:
        return False

async def remove_from_favorites(user_id: int, source_url: str) -> bool:
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                DELETE FROM favorites
                WHERE user_id = ? AND source_url = ?
            """, (user_id, source_url))
            await db.commit()
            return True
    except Exception:
        return False

async def is_favorite(user_id: int, source_url: str) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT 1 FROM favorites
            WHERE user_id = ? AND source_url = ?
        """, (user_id, source_url)) as cursor:
            row = await cursor.fetchone()
            return bool(row)

async def get_favorites(user_id: int, limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT song_title, performer, source_url, created_at
            FROM favorites
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_stats() -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            total_users = row[0] if row else 0

        async with db.execute("SELECT COUNT(*) FROM downloads_log WHERE status = 'success'") as cursor:
            row = await cursor.fetchone()
            total_downloads = row[0] if row else 0

        today_str = datetime.now().strftime("%Y-%m-%d")
        async with db.execute("""
            SELECT COUNT(*) FROM downloads_log 
            WHERE status = 'success' AND date(created_at) = date(?)
        """, (today_str,)) as cursor:
            row = await cursor.fetchone()
            today_downloads = row[0] if row else 0

        async with db.execute("""
            SELECT platform, COUNT(*) FROM downloads_log
            WHERE status = 'success'
            GROUP BY platform
            ORDER BY COUNT(*) DESC
        """) as cursor:
            platforms = await cursor.fetchall()

        return {
            "total_users": total_users,
            "total_downloads": total_downloads,
            "today_downloads": today_downloads,
            "platforms": dict(platforms)
        }

async def get_all_user_ids() -> list[int]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]
