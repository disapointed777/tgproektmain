# api_spoonacular.py
import requests
from translator import translate_query  # импортируем переводчик

class RecipeAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.spoonacular.com"
        print("✅ Spoonacular API инициализирован")

    def _request(self, endpoint, params):
        url = f"{self.base_url}{endpoint}"
        params['apiKey'] = self.api_key
        try:
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code != 200:
                print(f"❌ Ошибка {resp.status_code}: {resp.text[:200]}")
                return None
            return resp.json()
        except Exception as e:
            print(f"❌ Исключение: {e}")
            return None

    def search_by_name(self, query):
        # Переводим запрос на английский
        translated = translate_query(query)
        print(f"🔍 Русский запрос: '{query}' -> английский: '{translated}'")
        data = self._request("/recipes/complexSearch", {
            'query': translated,
            'number': 5,
            'addRecipeInformation': True,
            'fillIngredients': True,
            'instructionsRequired': True
        })
        if data:
            return data.get('results', [])
        return []

    def search_by_ingredients(self, ingredients):
        # Переводим каждый ингредиент
        translated = [translate_query(ing) for ing in ingredients]
        print(f"🔍 Ингредиенты (рус): {ingredients} -> (англ): {translated}")
        data = self._request("/recipes/findByIngredients", {
            'ingredients': ','.join(translated),
            'number': 5,
            'ranking': 1,
            'ignorePantry': True
        })
        return data if data else []

    def get_recipe_info(self, recipe_id):
        data = self._request(f"/recipes/{recipe_id}/information", {})
        return data if data else {}

    def get_random_recipes(self, number=1):
        data = self._request("/recipes/random", {'number': number})
        if data:
            return data.get('recipes', [])
        return []