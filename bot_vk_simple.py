# bot_vk_simple.py
import re
import json
import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from config import VK_TOKEN
from database import Database
from api_mealdb import RecipeAPI

print("🚀 Запуск VK бота...")

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

db = Database()
api = RecipeAPI()

# Хранилище последних показанных рецептов
last_recipes = {}

def get_main_keyboard():
    """Главная клавиатура"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("🔍 Поиск", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("🍲 Ингредиенты", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🔥 Популярное", color=VkKeyboardColor.SECONDARY)
    keyboard.add_button("❤️ Избранное", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("🎲 Случайный", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("🗑 Очистить всё", color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()

def send_message(user_id, text, keyboard=None, attachment=None):
    """Отправка сообщения"""
    try:
        vk.messages.send(
            user_id=user_id,
            message=text,
            random_id=0,
            keyboard=keyboard,
            attachment=attachment
        )
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def upload_photo_to_vk(image_url):
    """Загружает фото в VK и возвращает attachment"""
    try:
        # Скачиваем фото
        response = requests.get(image_url, timeout=10)
        if response.status_code != 200:
            return None
        
        # Получаем сервер для загрузки
        upload_server = vk.photos.getMessagesUploadServer()
        upload_url = upload_server['upload_url']
        
        # Загружаем фото
        files = {'photo': ('photo.jpg', response.content, 'image/jpeg')}
        upload_response = requests.post(upload_url, files=files).json()
        
        # Сохраняем фото
        photo_data = vk.photos.saveMessagesPhoto(**upload_response)
        photo = photo_data[0]
        
        return f"photo{photo['owner_id']}_{photo['id']}"
    except Exception as e:
        print(f"Ошибка загрузки фото: {e}")
        return None

def send_recipe(user_id, recipe, show_commands=True):
    """Отправляет полный рецепт с ID и командами"""
    
    recipe_id = recipe['id']
    
    # Название
    if recipe.get('title_ru'):
        title = recipe['title_ru']
        original = recipe.get('title', '')
        if original and original != title:
            text = f"🍽 *{title}*\n({original})\n\n"
        else:
            text = f"🍽 *{title}*\n\n"
    else:
        text = f"🍽 *{recipe['title']}*\n\n"
    
    # Категория и кухня
    if recipe.get('category'):
        text += f"📌 Категория: {recipe['category']}\n"
    if recipe.get('area'):
        text += f"🌍 Кухня: {recipe['area']}\n\n"
    
    # Ингредиенты
    if recipe.get('extendedIngredients'):
        text += "📝 *Ингредиенты:*\n"
        for ing in recipe['extendedIngredients']:
            if isinstance(ing, dict) and 'russian' in ing:
                text += f"• {ing['russian']}\n"
            elif isinstance(ing, dict) and 'original' in ing:
                text += f"• {ing['original']}\n"
            else:
                text += f"• {ing}\n"
        text += "\n"
    
    # Инструкция
    instructions = recipe.get('instructions', '')
    if instructions:
        instructions = re.sub('<[^<]+?>', '', instructions)
        if len(instructions) > 300:
            instructions = instructions[:300] + "..."
        text += f"👨‍🍳 *Приготовление:*\n{instructions}\n\n"
    
    # Команды для взаимодействия
    if show_commands:
        text += f"━━━━━━━━━━━━━━━━━━━━\n"
        text += f"📌 *ID рецепта:* `{recipe_id}`\n\n"
        text += f"📌 *Команды:*\n"
        text += f"   `добавить {recipe_id}` - в избранное\n"
        text += f"   `шаги {recipe_id}` - полная инструкция\n"
        text += f"   `избранное` - мои рецепты"
    
    # Сохраняем ID
    last_recipes[user_id] = recipe_id
    
    # Отправляем фото
    if recipe.get('image'):
        attachment = upload_photo_to_vk(recipe['image'])
        if attachment:
            send_message(user_id, text, keyboard=get_main_keyboard(), attachment=attachment)
        else:
            send_message(user_id, text, keyboard=get_main_keyboard())
    else:
        send_message(user_id, text, keyboard=get_main_keyboard())

def send_full_instructions(user_id, recipe):
    """Отправляет полную пошаговую инструкцию"""
    
    if recipe.get('title_ru'):
        title = recipe['title_ru']
    else:
        title = recipe['title']
    
    text = f"📖 *{title} - Полный пошаговый рецепт*\n\n"
    
    instructions = recipe.get('instructions', '')
    if instructions:
        instructions = re.sub('<[^<]+?>', '', instructions)
        # Разбиваем на шаги, если есть номера
        if 'step' in instructions.lower():
            text += instructions
        else:
            # Пытаемся разбить по точкам
            steps = instructions.split('.')
            for i, step in enumerate(steps, 1):
                if step.strip():
                    text += f"{i}. {step.strip()}.\n\n"
    else:
        text += "Инструкция отсутствует."
    
    send_message(user_id, text, keyboard=get_main_keyboard())

print("✅ VK бот запущен!")

# Состояния пользователей
user_states = {}

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        text = event.text.lower().strip()
        
        # Состояние: ожидание названия
        state = user_states.get(user_id, {})
        if state.get('waiting_for') == 'recipe_name':
            user_states.pop(user_id, None)
            send_message(user_id, f"🔍 Ищу: {event.text}")
            recipes = api.search_by_name(event.text)
            if recipes:
                for recipe in recipes[:3]:
                    recipe_info = api.get_recipe_info(recipe['id'])
                    send_recipe(user_id, recipe_info)
            else:
                send_message(user_id, "😕 Ничего не найдено.", keyboard=get_main_keyboard())
            continue
        
        # Состояние: ожидание ингредиентов
        if state.get('waiting_for') == 'ingredients':
            user_states.pop(user_id, None)
            ing_list = [i.strip() for i in event.text.split(',')]
            send_message(user_id, f"🔍 Ищу по ингредиентам: {', '.join(ing_list)}")
            recipes = api.search_by_ingredients(ing_list)
            if recipes:
                for recipe in recipes[:3]:
                    recipe_info = api.get_recipe_info(recipe['id'])
                    send_recipe(user_id, recipe_info)
            else:
                send_message(user_id, "😕 Ничего не найдено.", keyboard=get_main_keyboard())
            continue
        
        # === КОМАНДА: добавить в избранное ===
        if text.startswith("добавить "):
            try:
                recipe_id = text.replace("добавить ", "").strip()
                recipe_info = api.get_recipe_info(recipe_id)
                if recipe_info:
                    recipe_name = recipe_info.get('title_ru', recipe_info.get('title', 'Рецепт'))
                    success = db.add_favorite(user_id, recipe_id, recipe_name, recipe_info)
                    if success:
                        send_message(user_id, f"✅ Рецепт «{recipe_name}» добавлен в избранное!", keyboard=get_main_keyboard())
                    else:
                        send_message(user_id, "❌ Ошибка при добавлении.", keyboard=get_main_keyboard())
                else:
                    send_message(user_id, "❌ Рецепт не найден.", keyboard=get_main_keyboard())
            except Exception as e:
                send_message(user_id, f"❌ Ошибка: {e}", keyboard=get_main_keyboard())
            continue
        
        # === КОМАНДА: пошаговый рецепт ===
        if text.startswith("шаги "):
            try:
                recipe_id = text.replace("шаги ", "").strip()
                recipe_info = api.get_recipe_info(recipe_id)
                if recipe_info:
                    send_full_instructions(user_id, recipe_info)
                else:
                    send_message(user_id, "❌ Рецепт не найден.", keyboard=get_main_keyboard())
            except Exception as e:
                send_message(user_id, f"❌ Ошибка: {e}", keyboard=get_main_keyboard())
            continue
        
        # === КОМАНДЫ С КНОПОК ===
        
        if text == "🔍 поиск":
            user_states[user_id] = {'waiting_for': 'recipe_name'}
            send_message(user_id, "📝 Напиши название блюда:")
            continue
        
        if text == "🍲 ингредиенты":
            user_states[user_id] = {'waiting_for': 'ingredients'}
            send_message(user_id, "🥕 Напиши ингредиенты через запятую:\nНапример: курица, картошка, лук")
            continue
        
        if text == "🔥 популярное":
            send_message(user_id, "🔥 Загружаю популярные рецепты...")
            recipes = api.get_random_recipes(5)
            if recipes:
                for recipe in recipes[:5]:
                    send_recipe(user_id, recipe)
            else:
                send_message(user_id, "😕 Не удалось загрузить рецепты.")
            continue
        
        if text == "❤️ избранное":
            favs = db.get_favorites(user_id)
            if favs:
                send_message(user_id, "❤️ *Ваши избранные рецепты:*")
                for recipe_id, recipe_name, recipe_data in favs:
                    try:
                        data = json.loads(recipe_data)
                        send_recipe(user_id, data, show_commands=True)
                    except:
                        send_message(user_id, f"🍽 {recipe_name}\n`шаги {recipe_id}` - посмотреть")
            else:
                send_message(user_id, "❤️ У вас пока нет избранных рецептов.", keyboard=get_main_keyboard())
            continue
        
        if text == "🎲 случайный":
            send_message(user_id, "🎲 Генерирую случайный рецепт...")
            recipes = api.get_random_recipes(1)
            if recipes:
                send_recipe(user_id, recipes[0])
            else:
                send_message(user_id, "😕 Не удалось получить рецепт.")
            continue
        
        if text == "🗑 очистить всё":
            if db.clear_favorites(user_id):
                send_message(user_id, "✅ Всё избранное очищено!", keyboard=get_main_keyboard())
            else:
                send_message(user_id, "❌ Ошибка при очистке.", keyboard=get_main_keyboard())
            continue
        
        # === ПОИСК ПО ТЕКСТУ ===
        
        if text.startswith("ингредиенты "):
            ing_list = [i.strip() for i in text.replace("ингредиенты ", "").split(',')]
            send_message(user_id, f"🔍 Ищу по ингредиентам...")
            recipes = api.search_by_ingredients(ing_list)
            if recipes:
                for recipe in recipes[:3]:
                    recipe_info = api.get_recipe_info(recipe['id'])
                    send_recipe(user_id, recipe_info)
            else:
                send_message(user_id, "😕 Ничего не найдено.", keyboard=get_main_keyboard())
            continue
        
        if len(text) > 2 and text not in ["start"]:
            send_message(user_id, f"🔍 Ищу: {event.text}")
            recipes = api.search_by_name(event.text)
            if recipes:
                for recipe in recipes[:3]:
                    recipe_info = api.get_recipe_info(recipe['id'])
                    send_recipe(user_id, recipe_info)
            else:
                send_message(user_id, "😕 Ничего не найдено.", keyboard=get_main_keyboard())
            continue
        
        if text == "start":
            db.add_user(user_id, str(user_id))
            send_message(user_id, "👨‍🍳 *Кулинарный бот*\n\nЯ понимаю русский язык!\n\n📌 *Как пользоваться:*\n• Нажми на кнопку «🔍 Поиск» и введи название блюда\n• Нажми на кнопку «🍲 Ингредиенты» и введи продукты\n• Под каждым рецептом будет ID и команды:\n   `добавить ID` - в избранное\n   `шаги ID` - полная инструкция", keyboard=get_main_keyboard())