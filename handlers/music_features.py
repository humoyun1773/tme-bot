import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import (
    get_user_history,
    get_favorites,
    add_to_favorites,
    remove_from_favorites,
    is_favorite
)
from keyboards import (
    store_url_in_cache,
    get_song_info,
    get_audio_sent_keyboard,
)

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("history"))
async def cmd_history(message: types.Message):
    user_id = message.from_user.id
    history = await get_user_history(user_id, limit=8)

    if not history:
        await message.answer(
            "📜 <b>Tarix bo'sh.</b>\n"
            "Qo'shiq yuklaganingizda, oxirgi taronalar shu yerda ko'rinadi.",
            parse_mode="HTML"
        )
        return

    text = (
        "📜 <b>Oxirgi yuklab olingan qo'shiqlar:</b>\n"
        "<i>Qayta yuklash uchun kerakli taronani tanlang 👇</i>"
    )

    buttons = []
    for item in history:
        title = item.get("song_title", "Qo'shiq")
        performer = item.get("performer", "Noma'lum")
        source_url = item.get("source_url")
        if not source_url:
            continue

        cache_key = store_url_in_cache(source_url)
        full_name = f"{title} - {performer}"
        display_name = (full_name[:36] + "..") if len(full_name) > 36 else full_name

        buttons.append([
            InlineKeyboardButton(text=f"▶️ {display_name}", callback_data=f"dl:mp3_192:{cache_key}")
        ])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.message(Command("favorites"))
async def cmd_favorites(message: types.Message):
    user_id = message.from_user.id
    favorites = await get_favorites(user_id, limit=10)

    if not favorites:
        await message.answer(
            "❤️ <b>Sevimlilar ro'yxatingiz bo'sh.</b>\n"
            "Har qanday qo'shiq yuklanganda pastidagi <b>❤️ Sevimlilarga qo'shish</b> tugmasini bosib saqlab qo'yishingiz mumkin!",
            parse_mode="HTML"
        )
        return

    text = (
        "❤️ <b>Sevimli qo'shiqlaringiz:</b>\n"
        "<i>Yuklab olish uchun tanlang 👇</i>"
    )

    buttons = []
    for item in favorites:
        title = item.get("song_title", "Qo'shiq")
        performer = item.get("performer", "Noma'lum")
        source_url = item.get("source_url")
        if not source_url:
            continue

        cache_key = store_url_in_cache(source_url)
        full_name = f"{title} - {performer}"
        display_name = (full_name[:36] + "..") if len(full_name) > 36 else full_name

        buttons.append([
            InlineKeyboardButton(text=f"▶️ {display_name}", callback_data=f"dl:mp3_192:{cache_key}")
        ])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("fav:"))
async def handle_favorite_toggle(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) < 3:
        return

    action = parts[1]
    song_key = parts[2]
    info = get_song_info(song_key)

    if not info:
        await callback.answer("Ma'lumot eskirgan.", show_alert=True)
        return

    user_id = callback.from_user.id
    url = info.get("url")
    title = info.get("title", "Qo'shiq")
    performer = info.get("performer", "Noma'lum")

    if action == "add":
        await add_to_favorites(user_id, title, performer, url)
        await callback.answer("❤️ Sevimlilarga qo'shildi!", show_alert=False)
        kb = get_audio_sent_keyboard(song_key, is_fav=True)
        await callback.message.edit_reply_markup(reply_markup=kb)
    elif action == "del":
        await remove_from_favorites(user_id, url)
        await callback.answer("💔 Sevimlilardan o'chirildi!", show_alert=False)
        kb = get_audio_sent_keyboard(song_key, is_fav=False)
        await callback.message.edit_reply_markup(reply_markup=kb)
