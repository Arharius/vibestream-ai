import os
import subprocess
import yt_dlp
import requests

def split_audio(file_path, chunk_seconds=600):
    """Разбивает аудио на части, если оно больше 25МБ (лимит Whisper)"""
    if os.path.getsize(file_path) < 24 * 1024 * 1024:
        return [file_path]
    
    project_dir = os.path.dirname(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_pattern = os.path.join(project_dir, f"{base_name}_part_%03d.m4a")
    
    # Используем FFmpeg для быстрой нарезки без перекодирования
    cmd = [
        'ffmpeg', '-i', file_path, 
        '-f', 'segment', 
        '-segment_time', str(chunk_seconds), 
        '-c', 'copy', 
        output_pattern, '-y'
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    chunks = []
    idx = 0
    while True:
        part_path = os.path.join(project_dir, f"{base_name}_part_{idx:03d}.m4a")
        if os.path.exists(part_path):
            chunks.append(part_path)
            idx += 1
        else:
            break
    return chunks

def process_video_or_audio(url):
    """Скачивает аудио и обложку, обходя блокировки YouTube"""
    
    # Заголовки, чтобы YouTube думал, что мы - обычный браузер
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    common_opts = {
        'quiet': True,
        'no_check_certificate': True,
        'source_address': '0.0.0.0', # Принудительно используем IPv4 (решает ошибку DNS/Resolve)
        'user_agent': USER_AGENT,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(common_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            vid = info.get('id', 'temp')
            thumb_url = info.get('thumbnail')

        # Создаем папку для проекта внутри облачного хранилища
        p_dir = os.path.join("downloads", vid)
        if not os.path.exists(p_dir):
            os.makedirs(p_dir)

        # 1. Скачиваем превью (нужно для красоты в PDF-отчете)
        t_path = os.path.join(p_dir, "thumb.jpg")
        if not os.path.exists(t_path) and thumb_url:
            try:
                r = requests.get(thumb_url, timeout=10, headers={'User-Agent': USER_AGENT})
                with open(t_path, 'wb') as f:
                    f.write(r.content)
            except Exception as e:
                print(f"Ошибка загрузки превью: {e}")

        # 2. Скачиваем аудио
        a_path = os.path.join(p_dir, "original.m4a")
        if not os.path.exists(a_path):
            download_opts = {
                **common_opts,
                'format': 'm4a/bestaudio/best',
                'outtmpl': os.path.join(p_dir, 'original.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                }],
            }
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                ydl.download([url])
        
        return {
            "audio": a_path, 
            "thumb": t_path if os.path.exists(t_path) else None, 
            "id": vid
        }
    except Exception as e:
        # Пробрасываем ошибку выше для вывода в интерфейс [cite: 2026-02-02]
        raise Exception(f"YouTube Error: {str(e)}")