import os
from dotenv import load_dotenv

# Загружаем переменные
load_dotenv()

google_key = os.getenv("GOOGLE_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")

print("-" * 30)
print("🔍 ДИАГНОСТИКА КЛЮЧЕЙ")
print("-" * 30)

if google_key:
    print(f"✅ GOOGLE_API_KEY: Найден! (Начинается на: {google_key[:5]}...)")
else:
    print("❌ GOOGLE_API_KEY: НЕ НАЙДЕН. Проверь название в .env")

if groq_key:
    print(f"✅ GROQ_API_KEY:   Найден! (Начинается на: {groq_key[:5]}...)")
else:
    print("❌ GROQ_API_KEY:   НЕ НАЙДЕН.")
print("-" * 30)