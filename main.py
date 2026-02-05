import os
import shutil
import uuid
import logging
from fastapi import FastAPI, Query, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Импорт твоих модулей
import database
from services.audio_service import process_video_or_audio
from services.gpt_service import analyze_text

# Настройка логирования, чтобы видеть всё в терминале Mac [cite: 2026-02-02]
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VibeStream AI")

# Разрешаем CORS для локальной разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальный словарь статусов (в памяти сервера)
tasks_status = {}

# Безопасная инициализация базы данных
@app.on_event("startup")
async def startup_event():
    try:
        database.init_db()
        logger.info("✅ База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"⚠️ Ошибка БД при старте: {e}")

# Создаем папку для загрузок, если её нет
os.makedirs("downloads", exist_ok=True)
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")

# Основной фоновый воркер [cite: 1-7, 2026-02-02]
async def background_worker(task_id: str, url_or_path: str, user_id: str, is_url: bool):
    try:
        logger.info(f"🚀 Запуск воркера для задачи {task_id}")
        
        # ЭТАП 1: Загрузка/Скачивание
        tasks_status[task_id] = "📥 Загрузка медиа..."
        if is_url:
            data = process_video_or_audio(url_or_path)
            audio_path = data["audio"]
            video_id = data["id"]
        else:
            audio_path = url_or_path
            video_id = task_id

        # ЭТАП 2: ИИ Анализ
        tasks_status[task_id] = "🤖 Нейросеть анализирует контент..."
        logger.info(f"🔍 Отправка в ИИ: {audio_path}")
        analysis = analyze_text(audio_path)
        
        # ЭТАП 3: Сохранение результата
        try:
            database.save_project(user_id, video_id, "Анализ VibeStream", analysis)
            logger.info(f"💾 Результат сохранен в базу для {video_id}")
        except Exception as db_err:
            logger.error(f"⚠️ Не удалось сохранить в БД: {db_err}")

        # ФИНАЛ: Записываем объект с результатом
        tasks_status[task_id] = {"result": analysis}
        logger.info(f"✅ Задача {task_id} успешно завершена")

    except Exception as e:
        # Критически важно: записываем ошибку в статус, чтобы фронтенд её увидел [cite: 2026-02-02]
        error_msg = f"❌ Ошибка: {str(e)}"
        logger.error(f"💥 Сбой в воркере {task_id}: {e}")
        tasks_status[task_id] = error_msg

@app.get("/process-live")
async def process_live(background_tasks: BackgroundTasks, url: str = Query(...), user_id: str = "guest"):
    task_id = str(uuid.uuid4())
    tasks_status[task_id] = "Подготовка..."
    # Сразу запускаем в фоне и отдаем ID
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
        
    tasks_status[task_id] = "Файл загружен..."
    background_tasks.add_task(background_worker, task_id, file_path, user_id, False)
    return {"status": "started", "task_id": task_id}

@app.get("/check-status")
async def check_status(task_id: str):
    """Эндпоинт для фронтенда (polling)"""
    # Если ID нет в словаре, значит сервер перезагрузился или ID неверный
    status = tasks_status.get(task_id, "Задача не найдена (возможно, сервер был перезапущен)")
    return {"data": status}

# Раздача фронтенда (должна быть в самом конце)
app.mount("/", StaticFiles(directory="static", html=True), name="static")