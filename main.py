from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import shutil
from services.video_service import download_audio
from services.audio_service import transcribe_audio
from services.gpt_service import analyze_content

app = FastAPI()

# Подключаем папку со стилями и скриптами
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

# --- ЭНДПОИНТ 1: Работа по ССЫЛКЕ (YouTube, RuTube и т.д.) ---
@app.get("/process-live")
async def process_live_endpoint(url: str):
    print(f"\n🚀 Запрос на анализ ссылки: {url}")
    
    try:
        # 1. Скачивание
        download_result = download_audio(url)
        if download_result["status"] == "error":
            raise Exception(download_result["message"])
        
        audio_path = download_result["file_path"]
        
        # 2. Транскрибация
        transcript = transcribe_audio(audio_path)
        if not transcript:
            raise Exception("Не удалось распознать речь.")

        # 3. Анализ GPT
        analysis = analyze_content(transcript)
        
        # 4. Уборка (удаляем файл)
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return {"status": "success", "content": analysis}

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

# --- ЭНДПОИНТ 2: Работа с ЗАГРУЖЕННЫМ ФАЙЛОМ ---
@app.post("/process-upload")
async def process_upload_endpoint(file: UploadFile = File(...)):
    print(f"\n📂 Получен файл: {file.filename}")
    
    temp_filename = f"upload_{file.filename}"
    
    try:
        # 1. Сохраняем файл на диск
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Транскрибация (используем тот же сервис)
        print("🎧 Начинаю транскрибацию загруженного файла...")
        transcript = transcribe_audio(temp_filename)
        if not transcript:
            raise Exception("Не удалось распознать речь в файле.")

        # 3. Анализ GPT
        print("🧠 Отправляю текст в AI...")
        analysis = analyze_content(transcript)
        
        # 4. Уборка
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

        return {"status": "success", "content": analysis}

    except Exception as e:
        print(f"❌ Ошибка обработки файла: {e}")
        if os.path.exists(temp_filename):
            os.remove(temp_filename) # Убираем мусор даже при ошибке
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)