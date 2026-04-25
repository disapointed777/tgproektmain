# translator_google.py
from googletrans import Translator

# Создаём один экземпляр переводчика на всё время работы
_translator = Translator()
_cache = {}  # кэш, чтобы не переводить одно и то же много раз

def translate_to_russian(text: str) -> str:
    """
    Переводит английский текст на русский с кэшированием.
    Если текст пустой или перевод не нужен – возвращает как есть.
    """
    if not text or len(text) < 3:
        return text
    
    # Проверяем кэш
    if text in _cache:
        return _cache[text]
    
    try:
        result = _translator.translate(text, src='en', dest='ru')
        translated = result.text
        _cache[text] = translated
        return translated
    except Exception as e:
        print(f"❌ Ошибка перевода: {e}")
        return text  # если ошибка, возвращаем оригинал