import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import Database
from api_mealdb import RecipeAPI
import keyboards as kb

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация
print("🚀 Запуск бота...")
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database()
api = RecipeAPI()

# Состояния для поиска
class SearchStates(StatesGroup):
    waiting_for_ingredients = State()
    waiting_for_recipe_name = State()

# =================== КОМАНДА START ===================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    db.add_user(message.from_user.id, message.from_user.username)
    
    await message.answer(
        "👨‍🍳 *Кулинарный бот*\n\n"
        "Я понимаю русский язык! Напиши название блюда или используй кнопки.\n\n"
        "Примеры: `борщ`, `пельмени`, `блины`, `курица с картошкой`\n\n"
        "👇 Используй кнопки внизу",
        parse_mode="Markdown",
        reply_markup=kb.main_menu
    )

# =================== ПОИСК ПО НАЗВАНИЮ ===================
@dp.message(F.text == "🔍 Поиск по названию")
async def search_name_start(message: Message, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_recipe_name)
    await message.answer("📝 Введите название блюда на русском:")

@dp.message(SearchStates.waiting_for_recipe_name)
async def process_name(message: Message, state: FSMContext):
    query = message.text
    await message.answer(f"🔍 Ищу: *{query}*", parse_mode="Markdown")
    
    recipes = api.search_by_name(query)
    
    if not recipes:
        await message.answer(
            "😕 Ничего не найдено. Попробуйте другое название.",
            reply_markup=kb.main_menu
        )
        await state.clear()
        return
    
    # Создаем кнопки с рецептами
    buttons = []
    for r in recipes[:5]:
        # Показываем русское название
        title = r.get('title_ru', r['title'])
        buttons.append([types.InlineKeyboardButton(
            text=f"🍽 {title}",
            callback_data=f"show_{r['id']}"
        )])
    
    await message.answer(
        f"✅ Найдено {len(recipes)} рецептов:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.clear()

# =================== ПОИСК ПО ИНГРЕДИЕНТАМ ===================
@dp.message(F.text == "🍲 Поиск по ингредиентам")
async def search_ing_start(message: Message, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_ingredients)
    await message.answer(
        "🥕 Введите ингредиенты через запятую:\n"
        "Например: `курица, картошка, лук`"
    )

@dp.message(SearchStates.waiting_for_ingredients)
async def process_ingredients(message: Message, state: FSMContext):
    ingredients = [i.strip() for i in message.text.split(',')]
    await message.answer("🔍 Ищу рецепты по ингредиентам...")
    
    recipes = api.search_by_ingredients(ingredients)
    
    if not recipes:
        await message.answer(
            "😕 Ничего не найдено. Попробуйте другие ингредиенты.",
            reply_markup=kb.main_menu
        )
        await state.clear()
        return
    
    buttons = []
    for r in recipes[:5]:
        title = r.get('title_ru', r.get('title', 'Рецепт'))
        buttons.append([types.InlineKeyboardButton(
            text=f"🍽 {title}",
            callback_data=f"show_{r['id']}"
        )])
    
    await message.answer(
        f"✅ Найдено {len(recipes)} рецептов:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.clear()

# =================== ПОПУЛЯРНОЕ ===================
@dp.message(F.text == "🔥 Популярное")
async def popular_recipes(message: Message):
    """Показывает 5 случайных рецептов"""
    await message.answer("🔥 Загружаю популярные рецепты...")
    
    recipes = api.get_random_recipes(1)
    
    if not recipes:
        await message.answer("😕 Не удалось загрузить рецепты.")
        return
    
    for recipe in recipes:
        await show_recipe(message, recipe)

# =================== ИЗБРАННОЕ ===================
@dp.message(F.text == "❤️ Мои избранные")
async def show_favorites(message: Message):
    favorites = db.get_favorites(message.from_user.id)
    
    if not favorites:
        await message.answer(
            "❤️ *Избранное*\n\n"
            "У вас пока нет избранных рецептов.\n"
            "Нажмите ⭐ В избранное под любым рецептом.",
            parse_mode="Markdown"
        )
        return
    
    await message.answer(
        "❤️ *Ваши избранные рецепты:*",
        parse_mode="Markdown",
        reply_markup=kb.favorites_keyboard(favorites)
    )

# =================== СЛУЧАЙНЫЙ РЕЦЕПТ ===================
@dp.message(F.text == "🎲 Случайный рецепт")
async def random_recipe(message: Message):
    await message.answer("🎲 Генерирую случайный рецепт...")
    
    recipes = api.get_random_recipes(1)
    if recipes:
        await show_recipe(message, recipes[0])
    else:
        await message.answer("😕 Не удалось получить рецепт.")

# =================== ФУНКЦИЯ ПОКАЗА РЕЦЕПТА ===================
async def show_recipe(message: Message, recipe):
    """Показывает рецепт с русскими названиями и ингредиентами"""
    
    # Проверяем, есть ли в избранном
    favorites = db.get_favorites(message.from_user.id)
    is_favorite = any(fav[0] == str(recipe['id']) for fav in favorites)
    
    # Определяем название для показа
    if recipe.get('title_ru'):
        title_display = recipe['title_ru']
        original = recipe.get('title', '')
        if original and original != title_display:
            text = f"*{title_display}*\n_({original})_\n\n"
        else:
            text = f"*{title_display}*\n\n"
    else:
        text = f"*{recipe['title']}*\n\n"
    
    # Категория и кухня
    if recipe.get('category'):
        text += f"📌 *Категория:* {recipe['category']}\n"
    if recipe.get('area'):
        text += f"🌍 *Кухня:* {recipe['area']}\n\n"
    
    # Ингредиенты (на русском)
    if recipe.get('extendedIngredients'):
        text += "*Ингредиенты:*\n"
        for ing in recipe['extendedIngredients']:
            # Показываем русский вариант, если есть
            if isinstance(ing, dict) and 'russian' in ing:
                text += f"• {ing['russian']}\n"
            elif isinstance(ing, dict) and 'original' in ing:
                text += f"• {ing['original']}\n"
            else:
                text += f"• {ing}\n"
        text += "\n"
    
    # Инструкция (на русском)
    instructions = recipe.get('instructions', '')
    if instructions:
        # Очищаем от возможных HTML-тегов
        instructions = re.sub('<[^<]+?>', '', instructions)
        if len(instructions) > 500:
            instructions = instructions[:500] + "...\n\n(полная инструкция по кнопке ниже)"
        text += f"*Приготовление:*\n{instructions}\n"
    
    # Отправляем фото
    if recipe.get('image'):
        try:
            await message.answer_photo(
                photo=recipe['image'],
                caption=text,
                parse_mode="Markdown",
                reply_markup=kb.recipe_keyboard(recipe['id'], title_display, is_favorite)
            )
        except:
            await message.answer(
                text,
                parse_mode="Markdown",
                reply_markup=kb.recipe_keyboard(recipe['id'], title_display, is_favorite)
            )
    else:
        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=kb.recipe_keyboard(recipe['id'], title_display, is_favorite)
        )

# =================== ОБРАБОТЧИКИ КНОПОК ===================
@dp.callback_query(F.data.startswith("show_"))
async def callback_show(callback: CallbackQuery):
    await callback.answer()
    recipe_id = callback.data.split("_")[1]
    
    recipe = api.get_recipe_info(recipe_id)
    if recipe:
        await show_recipe(callback.message, recipe)

# Обработчик для добавления в избранное
@dp.callback_query(F.data.startswith("addfav_"))
async def callback_add_fav(callback: CallbackQuery):
    await callback.answer()
    
    recipe_id = callback.data.split("_")[1]
    
    # Получаем информацию о рецепте, чтобы узнать название
    recipe = api.get_recipe_info(recipe_id)
    if not recipe:
        await callback.answer("❌ Ошибка загрузки рецепта")
        return
    
    recipe_name = recipe.get('title_ru', recipe.get('title', 'Рецепт'))
    
    success = db.add_favorite(callback.from_user.id, recipe_id, recipe_name, recipe)
    
    if success:
        await callback.answer("✅ Добавлено в избранное!")
        # Обновляем клавиатуру
        await callback.message.edit_reply_markup(
            reply_markup=kb.recipe_keyboard(recipe_id, recipe_name, True)
        )

# Обработчик для показа рецепта из избранного
@dp.callback_query(F.data.startswith("fav_"))
async def callback_fav_show(callback: CallbackQuery):
    """Обработчик для кнопок из списка избранного"""
    await callback.answer()
    recipe_id = callback.data.split("_")[1]
    
    recipe = api.get_recipe_info(recipe_id)
    if recipe:
        await show_recipe(callback.message, recipe)

@dp.callback_query(F.data.startswith("steps_"))
async def callback_steps(callback: CallbackQuery):
    await callback.answer()
    recipe_id = callback.data.split("_")[1]
    
    recipe = api.get_recipe_info(recipe_id)
    
    if recipe and recipe.get('instructions'):
        instructions = re.sub('<[^<]+?>', '', recipe['instructions'])
        title = recipe.get('title_ru', recipe.get('title', 'Рецепт'))
        text = f"*{title} - Пошаговый рецепт*\n\n{instructions}"
        
        # Разбиваем на части, если длинное
        if len(text) > 4000:
            for i in range(0, len(text), 4000):
                await callback.message.answer(text[i:i+4000], parse_mode="Markdown")
        else:
            await callback.message.answer(text, parse_mode="Markdown")
    else:
        await callback.message.answer("📝 Пошаговая инструкция отсутствует.")

# =================== ОБРАБОТЧИКИ ДЛЯ ИЗБРАННОГО ===================
@dp.callback_query(F.data == "clear_favorites")
async def callback_clear_favorites(callback: CallbackQuery):
    """Очищает всё избранное пользователя"""
    await callback.answer()
    
    # Запрашиваем подтверждение
    confirm_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✅ Да, очистить", callback_data="confirm_clear")],
        [types.InlineKeyboardButton(text="❌ Нет, отмена", callback_data="cancel_clear")]
    ])
    
    await callback.message.answer(
        "🗑 *Вы уверены?*\n\n"
        "Это действие удалит ВСЕ рецепты из избранного.",
        parse_mode="Markdown",
        reply_markup=confirm_keyboard
    )

@dp.callback_query(F.data == "confirm_clear")
async def callback_confirm_clear(callback: CallbackQuery):
    """Подтверждение очистки избранного"""
    await callback.answer()
    
    success = db.clear_favorites(callback.from_user.id)
    
    if success:
        await callback.message.edit_text(
            "✅ *Избранное очищено!*\n\n"
            "Все рецепты удалены.",
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            "❌ *Ошибка*\n\n"
            "Не удалось очистить избранное.",
            parse_mode="Markdown"
        )

@dp.callback_query(F.data == "cancel_clear")
async def callback_cancel_clear(callback: CallbackQuery):
    """Отмена очистки избранного"""
    await callback.answer()
    await callback.message.edit_text("❌ Очистка отменена.")

@dp.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery):
    """Заглушка для неактивных кнопок"""
    await callback.answer()

# =================== ОБРАБОТКА ТЕКСТА ===================
@dp.message()
async def handle_text(message: Message):
    """Обрабатывает любой текст как поисковый запрос"""
    if len(message.text) > 2 and not message.text.startswith('/'):
        await message.answer(f"🔍 Ищу: *{message.text}*", parse_mode="Markdown")
        
        recipes = api.search_by_name(message.text)
        
        if recipes:
            buttons = []
            for r in recipes[:3]:
                title = r.get('title_ru', r['title'])
                buttons.append([types.InlineKeyboardButton(
                    text=f"🍽 {title}",
                    callback_data=f"show_{r['id']}"
                )])
            
            await message.answer(
                f"✅ Найдено {len(recipes)} рецептов:",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons)
            )
        else:
            await message.answer(
                "😕 Ничего не найдено. Попробуйте другое название.",
                reply_markup=kb.main_menu
            )

# =================== ЗАПУСК ===================
async def main():
    print("✅ Бот запущен!")
    print("📝 Доступные команды в меню")
    print("🇷🇺 Поддерживается русский язык")
    print("🗑 Добавлена очистка избранного")
    print("=" * 40)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Бот остановлен")