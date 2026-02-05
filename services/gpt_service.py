import os, groq, google.genai as genai
from dotenv import load_dotenv
from services.audio_service import split_audio

load_dotenv()
g_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
gem_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_text(audio_path):
    chunks = split_audio(audio_path)
    full_text = ""
    for c in chunks:
        with open(c, "rb") as f:
            t = g_client.audio.transcriptions.create(file=(c, f.read()), model="whisper-large-v3", response_format="text")
            full_text += t + " "
        if "_part_" in c: os.remove(c)

    # Сохраняем полный текст для PRO пользователей
    t_path = os.path.join(os.path.dirname(audio_path), "transcript.txt")
    with open(t_path, "w", encoding="utf-8") as f: f.write(full_text)

    try:
        # План А: Gemini (Лимит 1 млн токенов)
        res = gem_client.models.generate_content(model='gemini-1.5-flash', contents=f"Сделай SMM-отчет: {full_text}")
        return res.text, t_path
    except Exception as e:
        print(f"⚠️ План Б (Groq): {e}")
        comp = g_client.chat.completions.create(model="llama-3.1-8b-instant", 
                                               messages=[{"role": "user", "content": f"Саммари: {full_text[:12000]}"}])
        return comp.choices[0].message.content, t_path