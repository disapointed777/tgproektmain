# api_mealdb.py
import requests
from translator import translate_query
from translator_google import translate_to_russian

class RecipeAPI:
    def __init__(self, api_key=None):
        self.base_url = "https://www.themealdb.com/api/json/v1/1"
        print("✅ TheMealDB API инициализирован")

    def search_by_name(self, query):
        english_query = translate_query(query)
        print(f"🔍 Поиск: '{query}' -> '{english_query}'")
        url = f"{self.base_url}/search.php"
        params = {'s': english_query}
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            meals = data.get('meals', [])
            if meals:
                results = []
                for meal in meals:
                    title_ru = translate_to_russian(meal['strMeal'])
                    results.append({
                        'id': meal['idMeal'],
                        'title': meal['strMeal'],
                        'title_ru': title_ru,
                        'image': meal['strMealThumb']
                    })
                return results
            return []
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return []

    def search_by_ingredients(self, ingredients):
        english_ing = [translate_query(ing) for ing in ingredients]
        if not english_ing:
            return []
        url = f"{self.base_url}/filter.php"
        params = {'i': english_ing[0]}
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            meals = data.get('meals', [])
            if meals:
                results = []
                for meal in meals[:5]:
                    full = self.get_recipe_info(meal['idMeal'])
                    results.append({
                        'id': meal['idMeal'],
                        'title': full.get('title', meal['strMeal']),
                        'title_ru': full.get('title_ru', meal['strMeal']),
                        'image': meal['strMealThumb']
                    })
                return results
            return []
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return []

    def get_recipe_info(self, recipe_id):
        url = f"{self.base_url}/lookup.php"
        params = {'i': recipe_id}
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            meal = data.get('meals', [])[0] if data.get('meals') else None
            if meal:
                # Собираем и переводим ингредиенты
                ingredients = []
                for i in range(1, 21):
                    ing = meal.get(f'strIngredient{i}')
                    measure = meal.get(f'strMeasure{i}')
                    if ing and ing.strip():
                        # Переводим название ингредиента на русский
                        ing_ru = translate_to_russian(ing)
                        # Оставляем меру на английском (можно тоже переводить, но сложнее)
                        ingredients.append({
                            'original': f"{measure} {ing}",      # оригинал
                            'russian': f"{measure} {ing_ru}"     # перевод
                        })
                
                # Переводим всё остальное
                title_ru = translate_to_russian(meal['strMeal'])
                instructions_ru = translate_to_russian(meal['strInstructions'])
                category_ru = translate_to_russian(meal.get('strCategory', ''))
                area_ru = translate_to_russian(meal.get('strArea', ''))
                
                return {
                    'id': meal['idMeal'],
                    'title': meal['strMeal'],
                    'title_ru': title_ru,
                    'image': meal['strMealThumb'],
                    'instructions': instructions_ru,
                    'instructions_original': meal['strInstructions'],
                    'extendedIngredients': ingredients,  # теперь с русскими названиями
                    'category': category_ru,
                    'area': area_ru
                }
            return {}
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return {}

    def get_random_recipes(self, number=1):
        url = f"{self.base_url}/random.php"
        try:
            recipes = []
            for _ in range(number):
                resp = requests.get(url, timeout=10)
                data = resp.json()
                if data.get('meals'):
                    meal = data['meals'][0]
                    recipes.append(self.get_recipe_info(meal['idMeal']))
            return recipes
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return []