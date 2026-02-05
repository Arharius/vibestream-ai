import os, time, shutil, uuid
from fastapi import FastAPI, Query, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import database
from services.audio_service import process_video_or_audio
from services.gpt_service import analyze_text

app = FastAPI(title="VibeStream PRO")

# Разрешаем CORS для стабильной работы из браузера
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Глобальное хранилище статусов
tasks_status = {}

# Асинхронная инициализация базы, чтобы не тормозить запуск сервера
@app.on_event("startup")
async def startup_event():
    try:
        database.init_db()
        print("✅ База данных Neon готова к работе")
    except Exception as e:
        print(f"⚠️ Ошибка БД при старте: {e}")

os.makedirs("downloads", exist_ok=True)
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")

# Фоновый воркер
async def background_worker(task_id, url_or_path, user_id, is_url=True):
    try:
        tasks_status[task_id] = "📥 Загрузка медиа..."
        if is_url:
            data = process_video_or_audio(url_or_path)
            audio_path, video_id = data["audio"], data["id"]
        else:
            audio_path, video_id = url_or_path, task_id

        tasks_status[task_id] = "🤖 ИИ-анализ (транскрибация)..."
        analysis = analyze_text(audio_path)
        
        try:
            database.save_project(user_id, video_id, "Анализ", analysis)
        except: pass
        
        tasks_status[task_id] = {"result": analysis}
    except Exception as e:
        tasks_status[task_id] = f"❌ Ошибка: {str(e)}"

@app.get("/process-live")
async def process_live(background_tasks: BackgroundTasks, url: str = Query(...), user_id: str = "guest"):
    task_id = str(uuid.uuid4())
    tasks_status[task_id] = "Запуск..."
    # Мгновенный ответ для предотвращения 504 ошибки
    background_tasks.add_task(background_worker, task_id, url, user_id, True)
    return {"status": "started", "task_id": task_id}

@app.post("/upload-audio")
async def upload_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...), user_id: str = "guest"):
    task_id = str(uuid.uuid4())
    p_dir = os.path.join("downloads", task_id)
    os.makedirs(p_dir, exist_ok=True)
    file_path = os.path.join(p_dir, "original.m4a")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    background_tasks.add_task(background_worker, task_id, file_path, user_id, False)
    return {"status": "started", "task_id": task_id}

@app.get("/check-status")
async def check_status(task_id: str):
    return {"data": tasks_status.get(task_id, "Ожидание...")}

app.mount("/", StaticFiles(directory="static", html=True), name="static")