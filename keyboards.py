# keyboards.py
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Поиск по названию")],
        [KeyboardButton(text="🍲 Поиск по ингредиентам")],
        [KeyboardButton(text="🔥 Популярное")],
        [KeyboardButton(text="❤️ Мои избранные")],
        [KeyboardButton(text="🎲 Случайный рецепт")]
    ],
    resize_keyboard=True
)

def recipe_keyboard(recipe_id: str, recipe_name: str, is_favorite: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура под рецептом"""
    buttons = [
        [InlineKeyboardButton(text="📝 Пошаговый рецепт", callback_data=f"steps_{recipe_id}")]
    ]
    
    if is_favorite:
        buttons.append([InlineKeyboardButton(text="✅ В избранном", callback_data="noop")])
    else:
        buttons.append([InlineKeyboardButton(
            text="⭐ В избранное",
            callback_data=f"addfav_{recipe_id}"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def favorites_keyboard(favorites: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком избранного и кнопкой очистки"""
    buttons = []
    
    for recipe_id, recipe_name, _ in favorites:
        buttons.append([InlineKeyboardButton(
            text=f"❤️ {recipe_name}",
            callback_data=f"fav_{recipe_id}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="🗑 Очистить всё избранное",
        callback_data="clear_favorites"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)