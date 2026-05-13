# run_both.py
import subprocess
import sys
import os

print("=" * 50)
print("🚀 ЗАПУСК ОБОИХ БОТОВ (Telegram + VK)")
print("=" * 50)

# Запускаем Telegram бота
print("\n📱 Запуск Telegram бота...")
tg_process = subprocess.Popen([sys.executable, "bot.py"])

# Запускаем VK бота
print("📱 Запуск VK бота...")
vk_process = subprocess.Popen([sys.executable, "bot_vk.py"])

print("\n✅ Оба бота работают!")
print("📌 Для остановки нажми Ctrl+C")
print("=" * 50)

try:
    tg_process.wait()
    vk_process.wait()
except KeyboardInterrupt:
    print("\n\n🛑 Остановка ботов...")
    tg_process.terminate()
    vk_process.terminate()
    print("✅ Боты остановлены")