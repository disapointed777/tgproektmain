# translator.py
# Словарь популярных русских блюд и продуктов с переводом на английский

RUSSIAN_TO_ENGLISH = {
    # Супы
    "борщ": "borscht",
    "щи": "shchi",
    "солянка": "solyanka",
    "рассольник": "rassolnik",
    "уха": "fish soup",
    "суп": "soup",
    "грибной суп": "mushroom soup",
    "куриный суп": "chicken soup",
    "гороховый суп": "pea soup",
    "том ям": "tom yam",
    "лапша": "noodle soup",
    
    # Вторые блюда
    "плов": "pilaf",
    "паста": "pasta",
    "спагетти": "spaghetti",
    "карбонара": "carbonara",
    "болоньезе": "bolognese",
    "лазанья": "lasagna",
    "пельмени": "dumplings",
    "вареники": "varenyky",
    "манты": "manti",
    "хинкали": "khinkali",
    "блины": "pancakes",
    "оладьи": "fritters",
    "сырники": "syrniki",
    "запеканка": "casserole",
    "макароны": "macaroni",
    "котлеты": "cutlets",
    "тефтели": "meatballs",
    "голубцы": "stuffed cabbage",
    "жаркое": "roast",
    "гуляш": "goulash",
    "бефстроганов": "beef stroganoff",
    "пюре": "mashed potatoes",
    "картошка": "potatoes",
    "картофель": "potatoes",
    "гречка": "buckwheat",
    "рис": "rice",
    "каша": "porridge",
    "омлет": "omelette",
    "яичница": "fried eggs",
    
    # Мясо
    "курица": "chicken",
    "цыпленок": "chicken",
    "индейка": "turkey",
    "утка": "duck",
    "гусь": "goose",
    "свинина": "pork",
    "говядина": "beef",
    "баранина": "lamb",
    "телятина": "veal",
    "кролик": "rabbit",
    "фарш": "minced meat",
    "шашлык": "shashlik",
    "стейк": "steak",
    
    # Рыба
    "рыба": "fish",
    "семга": "salmon",
    "лосось": "salmon",
    "форель": "trout",
    "тунец": "tuna",
    "скумбрия": "mackerel",
    "треска": "cod",
    "судак": "pike perch",
    "щука": "pike",
    "карп": "carp",
    "морепродукты": "seafood",
    "креветки": "shrimp",
    "кальмары": "squid",
    "мидии": "mussels",
    
    # Салаты
    "салат": "salad",
    "оливье": "olivier salad",
    "цезарь": "caesar salad",
    "греческий салат": "greek salad",
    "винегрет": "vinaigrette",
    "селедка под шубой": "herring under fur coat",
    "крабовый салат": "crab salad",
    "овощной салат": "vegetable salad",
    "фруктовый салат": "fruit salad",
    
    # Выпечка и десерты
    "пирог": "pie",
    "пирожки": "pies",
    "ватрушки": "vatrushka",
    "шарлотка": "charlotte",
    "торт": "cake",
    "медовик": "honey cake",
    "наполеон": "napoleon cake",
    "печенье": "cookies",
    "пряники": "gingerbread",
    "булочки": "buns",
    "кекс": "muffin",
    "пончики": "donuts",
    "пицца": "pizza",
    "хачапури": "khachapuri",
    
    # Напитки
    "компот": "compote",
    "морс": "berry drink",
    "квас": "kvass",
    "кисель": "kissel",
    "смузи": "smoothie",
    "коктейль": "cocktail",
    "чай": "tea",
    "кофе": "coffee",
    
    # Кухни
    "русская": "russian",
    "итальянская": "italian",
    "французская": "french",
    "китайская": "chinese",
    "японская": "japanese",
    "грузинская": "georgian",
    "узбекская": "uzbek",
}

def translate_query(query: str) -> str:
    """
    Переводит русский запрос на английский, используя словарь.
    Если слово не найдено, возвращает его без изменений.
    """
    words = query.lower().split()
    translated_words = []
    for word in words:
        # Сначала ищем точное совпадение
        if word in RUSSIAN_TO_ENGLISH:
            translated_words.append(RUSSIAN_TO_ENGLISH[word])
        else:
            # Ищем по частям (для составных запросов типа "куриный суп")
            found = False
            for i in range(len(word)):
                if word[i:] in RUSSIAN_TO_ENGLISH:
                    translated_words.append(RUSSIAN_TO_ENGLISH[word[i:]])
                    found = True
                    break
            if not found:
                translated_words.append(word)
    return ' '.join(translated_words)