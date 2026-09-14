import asyncio
from typing import List, Dict, Any
import yt_dlp

async def search_music(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Qo'shiq nomi yoki ijrochi bo'yicha YouTube'dan qidiradi va mos keluvchi natijalarni qaytaradi.
    """
    opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 15,
    }

    search_query = f"ytsearch{limit}:{query}"

    def _do_search():
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(search_query, download=False)

    try:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, _do_search)
        if not info or "entries" not in info:
            return []

        results = []
        for entry in info["entries"]:
            if not entry:
                continue
            video_id = entry.get("id")
            if not video_id:
                continue

            title = entry.get("title", "Noma'lum qo'shiq")
            uploader = entry.get("uploader") or entry.get("channel", "Noma'lum ijrochi")
            duration = entry.get("duration", 0)

            results.append({
                "id": video_id,
                "title": title,
                "uploader": uploader,
                "duration": duration,
                "url": f"https://www.youtube.com/watch?v={video_id}"
            })

        return results[:limit]

    except Exception as e:
        print(f"Qo'shiq qidiruvida xatolik: {e}")
        return []
