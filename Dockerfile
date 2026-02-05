FROM python:3.10-slim

# Системные зависимости
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё остальное
COPY . .

# Папка для скачивания
RUN mkdir -p downloads && chmod 777 downloads

# Запуск на порту 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]