import os
import base64
import logging
from google import genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Инициализация клиентов
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyze_text(audio_file_path):
    """
    Анализ аудио с жесткой изоляцией контекста и подробным пересказом.
    """
    
    # ФИНАЛЬНЫЙ СТРОГИЙ ПРОМПТ
    prompt = """
    ИНСТРУКЦИЯ ДЛЯ АНАЛИЗА (СТРОГО):
    1. Проанализируй ТОЛЬКО текущий контент. Полностью ИГНОРИРУЙ любые предыдущие темы, истории про стройку, крановщиков или алкоголь, если их нет в этом аудио.
    2. Твоя роль: Мастер пересказа. Напиши живой, подробный и захватывающий ПЕРЕСКАЗ сюжета. 
    3. Сохраняй хронологию: что было в начале, середине и конце. Указывай ключевые фразы и детали.
    4. Если это шутка или анекдот — передай юмор и смысл развязки.

    СТРУКТУРА ОТВЕТА:
    # 📝 Подробный пересказ сюжета
    (Детальное описание событий шаг за шагом)

    # 🧐 В чем соль (Анализ)
    (Разбор смысла, юмора или ключевых идей именно ЭТОЙ истории)

    # 💡 Итог
    (Короткое резюме конкретно по этой теме)

    ЯЗЫК: Русский.
    ФОРМАТ: Markdown.
    """
    
    # --- ПЛАН А: Gemini 1.5 Flash ---
    try:
        logger.info(f"🤖 [Gemini] Чистый запуск анализа: {audio_file_path}")
        with open(audio_file_path, "rb") as f:
            audio_data = f.read()
            
        response = gemini_client.models.generate_content(
            model="gemini-1.5-flash",
            config={
                "temperature": 0.2, # Снижаем температуру для точности
            },
            contents=[
                prompt,
                {"inline_data": {
                    "mime_type": "audio/mpeg", 
                    "data": base64.b64encode(audio_data).decode('utf-8')
                }}
            ]
        )
        if response.text:
            return response.text
    except Exception as e:
        logger.warning(f"⚠️ Gemini выдал ошибку, переход на План Б: {e}")

    # --- ПЛАН Б: Groq Whisper Turbo + Llama 3.3 ---
    try:
        # 1. Транскрибация
        with open(audio_file_path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=(os.path.basename(audio_file_path), audio_file.read()),
                model="whisper-large-v3-turbo",
                response_format="text",
                language="ru",
                temperature=0.0
            )
        
        # 2. Анализ текста в Llama 3.3 с изоляцией
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": "Ты — аналитик с чистой памятью. Ты видишь текст впервые и не используешь знания из прошлых диалогов. Твоя задача — сделать честный и подробный пересказ."
                },
                {
                    "role": "user", 
                    "content": f"{prompt}\n\nВОТ ЕДИНСТВЕННЫЙ ТЕКСТ ДЛЯ АНАЛИЗА:\n{transcription}"
                }
            ],
            temperature=0.3 
        )
        return completion.choices[0].message.content

    except Exception as e:
        logger.error(f"❌ Критический сбой: {e}")
        raise Exception(f"Ошибка ИИ: {str(e)}")