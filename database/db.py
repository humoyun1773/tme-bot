import aiosqlite
from datetime import datetime
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
        await db.commit()

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

async def increment_download(user_id: int, platform: str, link: str, status: str = "success"):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if status == "success":
            await db.execute("""
                UPDATE users
                SET total_downloads = total_downloads + 1
                WHERE id = ?
            """, (user_id,))
        await db.execute("""
            INSERT INTO downloads_log (user_id, platform, link, status)
            VALUES (?, ?, ?, ?)
        """, (user_id, platform, link, status))
        await db.commit()

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
