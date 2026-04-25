# test_api.py
from config import SPOONACULAR_KEY
from api_spoonacular import RecipeAPI

api = RecipeAPI(SPOONACULAR_KEY)

print("\n=== ТЕСТ 1: Поиск по названию 'борщ' ===")
recipes = api.search_by_name("борщ")
if recipes:
    for r in recipes:
        print(f" - {r['title']}")
else:
    print("❌ Ничего не найдено")

print("\n=== ТЕСТ 2: Поиск по ингредиентам ['курица', 'картошка'] ===")
recipes = api.search_by_ingredients(['курица', 'картошка'])
if recipes:
    for r in recipes:
        print(f" - {r.get('title', r.get('id'))}")
else:
    print("❌ Ничего не найдено")

print("\n=== ТЕСТ 3: Случайный рецепт ===")
random_rec = api.get_random_recipes(1)
if random_rec:
    print(f" - {random_rec[0].get('title')}")
else:
    print("❌ Не удалось получить случайный рецепт")