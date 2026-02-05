import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Инициализация клиента Groq
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

def transcribe_audio(file_path: str):
    print(f"🚀 [GROQ] Отправляю аудио в облако (Super Speed): {file_path}")

    if not client:
        print("❌ Ошибка: Не найден GROQ_API_KEY в файле .env")
        return None

    if not os.path.exists(file_path):
        print("❌ Файл не найден")
        return None

    try:
        # Открываем файл и отправляем
        with open(file_path, "rb") as file:
            # Используем модель whisper-large-v3-turbo (самая быстрая)
            transcription = client.audio.transcriptions.create(
                file=(file_path, file.read()),
                model="whisper-large-v3-turbo",
                response_format="json",
                language="ru", 
                temperature=0.0
            )

        print(f"✅ Готово! Groq расшифровал мгновенно.")
        return transcription.text

    except Exception as e:
        print(f"❌ Ошибка Groq API: {e}")
        return None