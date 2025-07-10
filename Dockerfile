FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app/ /app

RUN pip install -U yt-dlp openai-whisper requests m3u8 selenium --no-cache-dir google-generativeai tqdm python-dotenv

# --- 預設輸出資料夾 ---
ENV VIDEO_BASE=/Media_Notes

# --- 環境變數（會在執行時被覆蓋） ---
ENV VIDEO2SUM_GEMINI_API_KEY=""
ENV VIDEO2SUM_GEMINI_MODEL="gemini-2.5-pro"

ENTRYPOINT ["python","/app/video_to_summary.py"]
