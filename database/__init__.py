from .db import (
    init_db,
    add_user,
    increment_download,
    get_stats,
    get_all_user_ids,
    get_all_users,
    find_user,
    get_user_history,
    add_to_favorites,
    remove_from_favorites,
    get_favorites,
    is_favorite,
    get_cached_file,
    set_cached_file
)

__all__ = [
    "init_db",
    "add_user",
    "increment_download",
    "get_stats",
    "get_all_user_ids",
    "get_all_users",
    "find_user",
    "get_user_history",
    "add_to_favorites",
    "remove_from_favorites",
    "get_favorites",
    "is_favorite",
    "get_cached_file",
    "set_cached_file"
]
