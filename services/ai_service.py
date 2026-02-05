import google.generativeai as genai
import os
import traceback
from dotenv import load_dotenv
from pathlib import Path

# 1. Загрузка настроек
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("GEMINI_API_KEY")

def analyze_audio(file_path: str):
    """Анализ аудио с помощью Gemini 3 Pro Preview"""
    if not api_key:
        print("❌ ОШИБКА: API_KEY не найден!")
        return {"status": "error", "message": "API_KEY missing"}

    try:
        genai.configure(api_key=api_key)

        # Проверяем файл перед отправкой
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"Файл не найден: {file_path}"}

        print(f"📡 Шаг 1: Загрузка на сервера Google... {file_path}")
        audio_file = genai.upload_file(path=file_path)

        # ИСПОЛЬЗУЕМ ТОЧНОЕ ИМЯ ИЗ ТВОЕГО СПИСКА
       # Используем Lite-версию, так как она самая экономичная и реже дает ошибку 429
        # Используем алиас, который Google балансирует автоматически
        print("🧠 Шаг 2: Анализ через gemini-flash-latest (обход блокировок)...")
        model = genai.GenerativeModel("gemini-flash-latest")
        
        prompt = """
        Ты — эксперт по виральному контенту. Проанализируй это аудио и напиши:
        1. Краткое резюме (о чем речь).
        2. Пост для Telegram с сочными эмодзи.
        3. Список из 5 трендовых хештегов.
        Отвечай на русском языке.
        """

        response = model.generate_content([prompt, audio_file])
        
        print("✅ Успех! Пост готов.")
        return {"status": "success", "content": response.text}

    except Exception as e:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА:")
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}