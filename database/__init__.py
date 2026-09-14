from .db import (
    init_db,
    add_user,
    increment_download,
    get_stats,
    get_all_user_ids,
    get_user_history,
    add_to_favorites,
    remove_from_favorites,
    get_favorites,
    is_favorite
)

__all__ = [
    "init_db",
    "add_user",
    "increment_download",
    "get_stats",
    "get_all_user_ids",
    "get_user_history",
    "add_to_favorites",
    "remove_from_favorites",
    "get_favorites",
    "is_favorite"
]
