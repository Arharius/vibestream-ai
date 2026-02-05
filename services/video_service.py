import yt_dlp
import os
import time

def download_audio(url: str):
    timestamp = int(time.time())
    output_filename = f"audio_{timestamp}"
    
    # Очищаем старые файлы куки, если они есть, чтобы не мешали
    if os.path.exists("cookies.txt"):
        print("⚠️ Вижу старый файл cookies.txt, но сейчас мы будем брать ключи прямо из Chrome.")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_filename,
        
        # 🔥 ГЛАВНАЯ ФИШКА: Берем куки прямо из браузера Chrome
        # Если у тебя основной браузер Safari или Firefox, напиши мне — поменяем одну строчку.
        'cookiesfrombrowser': ('chrome',), 
        
        # Маскировка
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'android'],
            }
        },
        
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        
        'quiet': False,
        'no_warnings': False,
        'nocheckcertificate': True,
    }

    try:
        print(f"⬇️ Попытка скачивания через Chrome-ключи: {url}")
        print("⏳ Если Mac спросит пароль или доступ к связке ключей — нажми 'Разрешить' (это доступ к шифрованным кукам).")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        final_path = output_filename + ".mp3"
        
        if os.path.exists(final_path):
            print(f"✅ ПОБЕДА! Файл создан: {final_path}")
            return {"status": "success", "file_path": final_path}
        else:
            return {"status": "error", "message": "Файл не появился после скачивания."}

    except Exception as e:
        error_msg = str(e)
        print(f"❌ ОШИБКА: {error_msg}")
        
        # Подсказка для отладки
        if "permission" in error_msg.lower() or "keychain" in error_msg.lower():
            return {"status": "error", "message": "Mac не дал доступ к кукам Chrome. Попробуй перезапустить терминал."}
            
        return {"status": "error", "message": error_msg}