import os
import sys
import json
import re
import subprocess
import argparse
from pathlib import Path
from typing import Optional, Tuple, Dict
import whisper
import logging
from datetime import datetime
import textwrap
import google.generativeai as genai
import glob
import pathlib
from tqdm import tqdm
import shutil
import time
import requests
from dotenv import load_dotenv

# --- Docker/團隊部署防呆：檢查 .env 與金鑰 ---
def check_env_and_key():
    # 先從環境變數抓 VIDEO2SUM_GEMINI_API_KEY
    api_key = os.getenv("VIDEO2SUM_GEMINI_API_KEY")
    if not api_key or api_key.strip() == "":
        # 再嘗試從 /app/.env 讀（Docker 內部）
        from dotenv import load_dotenv
        load_dotenv('/app/.env', override=True)
        api_key = os.getenv("VIDEO2SUM_GEMINI_API_KEY")
    if not api_key or api_key.strip() == "":
        print("❌ 未偵測到 VIDEO2SUM_GEMINI_API_KEY，請確認已正確設置環境變數或 .env。")
        sys.exit(1)

check_env_and_key()

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('video_to_summary.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

CATEGORIES = {
    "01": ("Programming", "語言教學、框架實作、演算法、程式範例", "Python、Rust、React"),
    "02": ("ComputerGraphics", "Shading、PBR、GPU、渲染管線", "SIGGRAPH、GDC 光影"),
    "03": ("AI_ML_Datasci", "機器學習、深度學習、資料科學、CV / NLP", "Coursera DL、Kaggle"),
    "04": ("GameDev_Design", "關卡設計、系統設計、玩法迭代、敘事", "GDC 設計論壇"),
    "05": ("Art_VFX_Motion", "動畫、VFX、分鏡、構圖、燈光", "Blender Guru"),
    "06": ("Product_Business", "PM、UX、Growth、商業模型", "YC Startup School"),
    "07": ("SoftSkills", "演講技巧、團隊協作、學習法", "TED、Productivity"),
    "08": ("Science_Edu", "數學、物理、天文、通識課程", "Khan、3Blue1Brown"),
}

# 從環境變數讀取模型，若無則使用預設值
GEMINI_MODEL_NAME = os.getenv("VIDEO2SUM_GEMINI_MODEL", "gemini-2.5-pro")

class VideoProcessor:
    def __init__(self, url, base_dir=None, category:str|None=None, subcategory:str|None=None):
        self.url = url
        self.base_dir = Path(base_dir or os.getenv("VIDEO_BASE", "Media_Notes"))
        # ▼ 若未指定分類，列出選單讓使用者輸入代號
        if not category:
            # 僅抓非隱藏資料夾（不論是否空資料夾）
            base_folders = [f.name for f in self.base_dir.iterdir() if f.is_dir() and not f.name.startswith('.')]
            # 預設分類名稱清單
            preset_names = [CATEGORIES[k][0] for k in CATEGORIES]
            # 自建分類 = 非預設分類且非隱藏資料夾
            custom_folders = [f for f in base_folders if f not in preset_names]
            if not base_folders:
                print("\n⚠️ 目前 Media_Notes 下沒有任何分類資料夾。")
                print("\n=== 預設 01-08 分類說明 ===")
                print("  代號│分類名稱              │說明 (常放哪些影片)             │範例")
                print("────┼────────────────────┼-----------------------------┼----------------------")
                for k, (name, desc, ex) in CATEGORIES.items():
                    print(f" [{k}]│{name:<20}│{desc:<28}│{ex}")
                print("\n1. 自動建立預設 01-08 分類資料夾")
                print("2. 自訂分類名稱並建立新分類")
                while True:
                    choice = input("請選擇 1 或 2：").strip()
                    if choice == '1' or choice == '2':
                        break
                    else:
                        print("請只輸入 1 或 2，不要輸入說明文字！\n")
                if choice == '1':
                    for k in CATEGORIES:
                        folder = self.base_dir / CATEGORIES[k][0]
                        if not folder.exists():
                            folder.mkdir(parents=True, exist_ok=True)
                    print("已建立預設 01-08 分類（已存在的不會覆蓋）。\n")
                    base_folders = [f.name for f in self.base_dir.iterdir() if f.is_dir() and not f.name.startswith('.')
                                    ]
                elif choice == '2':
                    cname = input("請輸入新分類名稱：").strip()
                    (self.base_dir / cname).mkdir(parents=True, exist_ok=True)
                    print(f"分類 [{cname}] 已建立，繼續下個階段...\n", flush=True)
                    # 新增：自建後仍詢問是否要建立預設 01-08 分類
                    print("\n是否要一併建立預設 01-08 分類資料夾？")
                    print("  代號│分類名稱              │說明 (常放哪些影片)             │範例")
                    print("────┼────────────────────┼-----------------------------┼----------------------")
                    for k, (name, desc, ex) in CATEGORIES.items():
                        print(f" [{k}]│{name:<20}│{desc:<28}│{ex}")
                    while True:
                        yn = input("輸入 Y 建立，N 跳過：").strip().lower()
                        if yn in ('y', 'n', ''):
                            break
                        else:
                            print("請只輸入 Y 或 N，不要輸入說明文字！\n")
                    if yn == 'y':
                        for k in CATEGORIES:
                            folder = self.base_dir / CATEGORIES[k][0]
                            if not folder.exists():
                                folder.mkdir(parents=True, exist_ok=True)
                        print("已建立預設 01-08 分類（已存在的不會覆蓋）。\n")
                    category = cname
            if not category:
                print("\n=== 請選擇影片分類 ===")
                print("  代號│分類名稱              │說明 (常放哪些影片)             │範例")
                print("────┼────────────────────┼-----------------------------┼----------------------")
                for k, (name, desc, ex) in CATEGORIES.items():
                    print(f" [{k}]│{name:<20}│{desc:<28}│{ex}")
                print(" [09]│自訂分類                │自訂資料夾                     │自訂")
                # 額外列出自建分類
                if custom_folders:
                    print("\n--- 其他自建分類 ---")
                    for idx, name in enumerate(custom_folders, 1):
                        print(f" [C{idx}]│{name}")
                while True:
                    code = input("輸入代號 (01-09 或 C1...Cn)：").strip()
                    valid_codes = list(CATEGORIES.keys()) + ['09'] + [f'C{i+1}' for i in range(len(custom_folders))]
                    if code in valid_codes or (code.startswith('C') and code[1:].isdigit() and 0 < int(code[1:]) <= len(custom_folders)):
                        break
                    else:
                        print("請輸入有效代號（01-09 或 C1...Cn），不要輸入說明文字！\n")
                if code == '09':
                    cname = input("請輸入新分類名稱：").strip()
                    (self.base_dir / cname).mkdir(parents=True, exist_ok=True)
                    print(f"分類 [{cname}] 已建立，繼續下個階段...\n", flush=True)
                    category = cname
                elif code.startswith('C') and code[1:].isdigit():
                    idx = int(code[1:]) - 1
                    if 0 <= idx < len(custom_folders):
                        category = custom_folders[idx]
                        print(f"分類 [{category}] 已選擇，繼續下個階段...\n", flush=True)
                    else:
                        print("輸入錯誤，預設為 Misc")
                        category = "Misc"
                else:
                    category = CATEGORIES.get(code, ("Misc", "", ""))[0]
                    print(f"分類 [{category}] 已選擇，繼續下個階段...\n", flush=True)
        self.category = category
        # ▼ 子分類互動
        if not subcategory:
            cat_dir = self.base_dir / self.category
            cat_dir.mkdir(parents=True, exist_ok=True)
            subfolders = [f.name for f in cat_dir.iterdir() if f.is_dir()]
            print("\n=== 子分類選擇 ===")
            print("1. 新建子分類")
            print("2. 沿用既有子分類")
            while True:
                choice = input("請選擇 1 或 2：").strip()
                if choice == '1' or choice == '2':
                    break
                else:
                    print("請只輸入 1 或 2，不要輸入說明文字！\n")
            if choice == '1':
                subcategory = input("請輸入新子分類資料夾名稱：").strip()
                (cat_dir / subcategory).mkdir(parents=True, exist_ok=True)
                print(f"子分類 [{subcategory}] 已建立，繼續下個階段...\n", flush=True)
            elif choice == '2':
                if subfolders:
                    print("現有子分類：")
                    for idx, name in enumerate(subfolders, 1):
                        print(f"  {idx}. {name}")
                    while True:
                        sel = input("請輸入要沿用的子分類編號：").strip()
                        if sel.isdigit() and 1 <= int(sel) <= len(subfolders):
                            subcategory = subfolders[int(sel)-1]
                            print(f"子分類 [{subcategory}] 已選擇，繼續下個階段...\n", flush=True)
                            break
                        else:
                            print("請輸入正確的子分類編號，不要輸入說明文字！\n")
                else:
                    print("⚠️ 沒有任何子分類，請新建一個！")
                    subcategory = input("請輸入新子分類資料夾名稱：").strip()
                    (cat_dir / subcategory).mkdir(parents=True, exist_ok=True)
                    print(f"子分類 [{subcategory}] 已建立，繼續下個階段...\n", flush=True)
            else:
                print("輸入錯誤，預設為 Misc")
                subcategory = "Misc"
        self.subcategory = subcategory
        
        # ▼ 語言選擇互動
        print("\n=== 影片語言選擇 ===")
        print("1. 英文 (English)")
        print("2. 中文 (Chinese)")
        print("3. 日文 (Japanese)")
        while True:
            lang_choice = input("請選擇影片語言 (1-3)：").strip()
            if lang_choice == '1':
                self.language = "en"
                break
            elif lang_choice == '2':
                self.language = "zh"
                break
            elif lang_choice == '3':
                self.language = "ja"
                break
            else:
                print("請只輸入 1、2 或 3，不要輸入說明文字！\n")
        print(f"語言 [{self.language}] 已選擇，繼續下個階段...\n", flush=True)
        
        # ▼ Whisper 模型選擇互動
        print("\n=== Whisper 模型選擇 ===")
        print("  代號│模型名稱 │記憶體需求│速度    │準確度│適用場景")
        print("────┼────────┼────────┼──────┼──────┼────────────────")
        whisper_models = [
            ("1", "tiny", "~1GB", "最快", "一般", "快速測試、短影片"),
            ("2", "base", "~1GB", "快", "較好", "一般用途、平衡選擇"),
            ("3", "small", "~2GB", "中等", "好", "推薦預設、多語言"),
            ("4", "medium", "~5GB", "較慢", "很好", "高品質需求"),
            ("5", "large", "~10GB", "最慢", "最佳", "專業用途、複雜內容")
        ]
        for code, name, mem, speed, acc, scene in whisper_models:
            print(f"  [{code}] │{name:<7} │{mem:<7} │{speed:<6} │{acc:<6} │{scene}")
        print("\n建議：")
        print("- 首次使用或一般用途：選擇 3 (small)")
        print("- 快速測試：選擇 1 (tiny)")
        print("- 高品質需求：選擇 4 或 5 (medium/large)")
        print("- 記憶體有限：選擇 1 或 2 (tiny/base)")
        model_map = {code: name for code, name, *_ in whisper_models}
        while True:
            model_choice = input("請選擇 Whisper 模型代號 (1-5，預設 3)：").strip()
            if not model_choice:
                self.whisper_model = "small"
                break
            elif model_choice in model_map:
                self.whisper_model = model_map[model_choice]
                break
            else:
                print("請只輸入 1~5 的代號，不要輸入說明文字！\n")
        print(f"Whisper 模型 [{self.whisper_model}] 已選擇，繼續下個階段...\n", flush=True)
        
        self.is_m3u8 = 'gdcvault.com' in url
        self.video_title = self._get_video_title()
        self.output_dir = self.base_dir / self.category / self.subcategory / f"{self.video_title}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.audio_path = self.output_dir / f"{self.video_title}.mp3"
        self.srt_path = self.output_dir / f"{self.video_title}.srt"
        
    def _get_video_title(self) -> str:
        """獲取影片標題並格式化"""
        # 若是本地檔案或 SRT，直接用檔名
        if self.url.endswith('.srt') or self.url.endswith('.mp4') or self.url.endswith('.mkv') or self.url.endswith('.mov') or self.url.endswith('.avi') or self.url.endswith('.webm') or self.url.startswith('/') or self.url.startswith('input/'):
            return Path(self.url).stem
        elif self.is_m3u8:
            # 對於 M3U8/GDC Vault 串流，先嘗試提取 ID
            try:
                # 尋找 GDC Vault ID 格式
                m = re.search(r'play/(\d+)/', self.url)
                if m:
                    raw_title = f"gdcvault_{m.group(1)}"
                    logger.info(f"提取到的 GDC ID: {raw_title}")
                else:
                    # 退回使用 URL 最後一段
                    raw_title = self.url.split('/')[-1]
                    if not raw_title:
                        raw_title = "m3u8_stream"
                    logger.info(f"使用 URL 段落作為標題: {raw_title}")
            except Exception as e:
                logger.error(f"從 M3U8 URL 提取標題時發生錯誤: {e}")
                raw_title = "m3u8_stream"
        else:
            # 對於 YouTube 和其他影片，使用 yt-dlp
            try:
                cmd = ['yt-dlp', '--socket-timeout', '10', '--print', '%(title)s', self.url]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                raw_title = result.stdout.strip()
            except subprocess.CalledProcessError as e:
                logger.error(f"使用 yt-dlp 獲取影片標題時發生錯誤: {e}")
                raise

        # 統一格式化所有來源的標題
        # 1. 移除特殊字符
        title = re.sub(r'[\'"\(\)\[\]\{\}、：]', '', raw_title)
        # 2. 空格和連字符轉換為底線
        title = re.sub(r'[\s\-]+', '_', title)
        # 3. 只保留英文字母、數字和底線
        title = re.sub(r'[^a-zA-Z0-9_]', '', title)
        
        # 確保標題不為空
        if not title:
            title = "default_video_title"
            logger.warning("格式化後的標題為空，使用預設標題")

        return title
            
    def get_video_duration(self) -> int:
        """獲取影片時長（秒）"""
        # 如果是本地檔案，使用 ffprobe 獲取時長
        if not is_url(self.url):
            try:
                cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json',
                      '-show_format', self.url]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                data = json.loads(result.stdout)
                duration = int(float(data['format']['duration']))
                logger.info(f"Local video duration: {duration} seconds")
                return duration
            except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
                logger.error(f"Failed to get local video duration: {e}")
                return 0
        
        # 如果是網路影片，使用 yt-dlp
        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES):
            try:
                cmd = ['yt-dlp', '--socket-timeout', '10', '--print', '%(duration)s', self.url]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                duration = int(result.stdout.strip())
                logger.info(f"Video duration: {duration} seconds")
                return duration
            except subprocess.CalledProcessError as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Retry {attempt + 1}/{MAX_RETRIES} getting duration")
                    continue
                logger.error(f"Failed to get video duration: {e}")
                return 0
        return 0

    def download_audio(self) -> bool:
        """下載音訊"""
        try:
            # 如果是本地檔案，直接提取音訊
            if not is_url(self.url):
                cmd = [
                    'ffmpeg',
                    '-i', self.url,
                    '-vn',  # 不包含視訊
                    '-acodec', 'mp3',
                    '-ab', '192k',  # 音訊位元率
                    '-ar', '44100',  # 取樣率
                    '-y',  # 覆蓋輸出檔案
                    str(self.audio_path)
                ]
                subprocess.run(cmd, check=True)
                logger.info(f"音訊成功提取至 {self.audio_path}")
                return True
            
            # 如果是網路影片
            if self.is_m3u8:
                # 使用 M3U8 下載工具
                m3u8_downloader = str(Path(__file__).parent / "m3u8_downloader.py")
                
                # 啟用虛擬環境中的 Python
                venv_python = str(Path(self.base_dir) / ".venv" / "Scripts" / "python.exe")
                if Path(venv_python).exists():
                    python_exe = venv_python
                else:
                    python_exe = sys.executable
                
                cmd = [
                    python_exe,
                    m3u8_downloader,
                    self.url,
                    '-o', str(self.audio_path),
                    '--type', 'audio'
                ]
            else:
                # 使用 yt-dlp 下載
                cmd = [
                    'yt-dlp',
                    '-x',
                    '--audio-format', 'mp3',
                    '--continue',
                    '--no-part',
                    '-o', str(self.audio_path),
                    self.url
                ]
            
            subprocess.run(cmd, check=True)
            logger.info(f"音訊成功下載至 {self.audio_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"下載音訊時發生錯誤: {e}")
            return False

    def verify_audio_duration(self, original_duration: int) -> bool:
        """驗證下載的音訊時長"""
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json',
                  '-show_format', str(self.audio_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            audio_duration = float(data['format']['duration'])
            
            # 允許 ±2 秒的誤差
            if abs(audio_duration - original_duration) <= 2:
                logger.info("Audio duration verification passed")
                return True
            else:
                logger.warning(f"Audio duration mismatch: {audio_duration} vs {original_duration}")
                return False
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error verifying audio duration: {e}")
            return False

    def transcribe_audio(self, model_size: str = "small", language: str = "en") -> Optional[str]:
        """轉錄音訊為 SRT"""
        try:
            logger.info(f"Loading Whisper model ({model_size})...")
            model = whisper.load_model(model_size)
            
            logger.info("Starting transcription...")
            result = model.transcribe(
                str(self.audio_path),
                language=language,
                task="transcribe",
                verbose=True
            )
            
            # 生成 SRT 檔案路徑
            srt_path = self.srt_path
            segments = result["segments"]
            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, seg in enumerate(tqdm(segments, desc="寫入 SRT", unit="段落"), 1):
                    print(f"{i}\n"
                          f"{self._format_timestamp(seg['start'])} --> "
                          f"{self._format_timestamp(seg['end'])}\n"
                          f"{seg['text'].strip()}\n",
                          file=f)
            
            logger.info(f"Transcription saved to {srt_path}")
            return str(srt_path)
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return None

    def verify_srt(self, original_duration: int, srt_path: str) -> bool:
        """驗證 SRT 轉錄完整性"""
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 找出最後一個時間碼
            time_pattern = r'\d{2}:\d{2}:\d{2},\d{3} --> (\d{2}:\d{2}:\d{2},\d{3})'
            matches = re.findall(time_pattern, content)
            if not matches:
                logger.error("No timestamps found in SRT file")
                return False
            
            last_timestamp = matches[-1]
            # 轉換時間碼為秒數
            time_match = re.match(r'(\d{2}):(\d{2}):(\d{2})', last_timestamp)
            if not time_match:
                logger.error(f"Could not parse last timestamp: {last_timestamp}")
                return False
            h, m, s = map(float, time_match.groups())
            srt_duration = h * 3600 + m * 60 + s
            
            # 允許 SRT 時長不少於原始時長的 95%，且絕對差異小於 120 秒
            if (srt_duration >= original_duration * 0.95 and 
                abs(srt_duration - original_duration) < 120):
                logger.info("SRT verification passed")
                return True
            else:
                logger.warning(f"SRT duration mismatch: {srt_duration} vs {original_duration}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying SRT: {e}")
            return False

    def cleanup_temp_files(self) -> None:
        """清理暫存檔案"""
        try:
            if self.audio_path.exists():
                self.audio_path.unlink()
                logger.info(f"Cleaned up temporary audio file: {self.audio_path}")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """格式化時間戳為 SRT 格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

    def summarize_srt(self, srt_path):
        """讀取 SRT 檔案，使用 Gemini API 進行摘要"""
        logger.info("開始生成摘要...")
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
        except FileNotFoundError:
            logger.error(f"SRT 檔案未找到: {srt_path}")
            return

        # 移除時間戳和序列號
        text_content = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', srt_content)
        text_content = text_content.replace('\n', ' ')

        # 檢查文本長度
        if len(text_content.strip()) < 50:
            logger.warning("SRT 文本內容過短，可能無法生成有意義的摘要。")
            # 仍然繼續嘗試，讓模型決定
        
        # 使用 textwrap 來處理過長的提示詞
        prompt_template = textwrap.dedent("""
你是一位專業的影片內容分析師，請根據下方 SRT 逐字稿，產生一份完全符合下列規範的繁體中文重點筆記：

【產出規範】
1. 嚴格依照下方「參考格式」產出，不能有任何 code block 標記（如 ``` 或 ```markdown）。
2. 最上方用 HTML 註解（<!-- ... -->）儲存影片原始時長與影片URL（YAML格式，MD內不顯示）。
3. 以主題分段，每個主題標題下方必須有 Markdown 超連結的時間碼，使用實際的影片URL：{video_url}。
4. 每主題下分層條列：「流程/步驟」、「技術重點」、「挑戰與解決」、「關鍵詞」等，標題與項目符號清楚。
5. 條列重點需涵蓋：概念、術語（中英文並列，首次出現時簡要說明）、流程、挑戰、解決方案、具體操作步驟、工具用法、參數設置、遇到的問題與解決方式。
6. 對於流程導向內容，請用「步驟 1、2、3」或流程圖方式呈現，避免僅列舉結果，需涵蓋過程與思考脈絡。
7. 內容需以高中畢業生為對象，確保易懂。
8. 若影片含多語言或文化背景差異，請標註語言切換點並簡要說明文化脈絡。
9. 產出內容必須是純 markdown，不得有任何 code block 標記。
10. 重要：所有時間碼連結必須使用實際的影片URL：{video_url}，不要使用範例URL。

【參考格式】
<!--
原始時長: "1:11:14"
影片URL: "{video_url}"
-->

### 主題優先 (Thematics First)
原始影片：[hh:mm:ss]({video_url})
* 靈感來源：劍橋分析 (Cambridge Analytica)

---

#### 主題一標題
[00:01:23]({video_url}&t=83s)
- 流程/步驟：
    1. ...
    2. ...
- 技術重點：
    - ...
- 挑戰與解決：
    - ...
- 關鍵詞：
    - ...
- 術語標註：
    - ...

#### 主題二標題
[00:12:34]({video_url}&t=754s)
- ...（依上方格式繼續）

---

【SRT 逐字稿】
{text_content}

請嚴格依上述規範與格式產出，不得有任何 code block 標記，也不得添加多餘說明。所有時間碼連結必須使用實際的影片URL：{video_url}。
""")
        
        # 取得實際的影片URL，如果是本地檔案則使用空字串
        video_url = getattr(self, 'url', '') if is_url(getattr(self, 'url', '')) else ''
        prompt = prompt_template.format(text_content=text_content, video_url=video_url)
        
        try:
            # logger.info(f"使用的模型: {GEMINI_MODEL}")
            logger.info(f"使用的模型: {GEMINI_MODEL_NAME}")
            
            # 使用 VIDEO2SUM_GEMINI_API_KEY 環境變數
            api_key = os.getenv("VIDEO2SUM_GEMINI_API_KEY")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            response = model.generate_content(
                prompt,
                generation_config={"temperature":0.3}
            )
            md_text = response.text.strip()
            
            # 自動移除開頭/結尾的 code block 標記
            md_text = re.sub(r'^(\s*```markdown\s*|\s*```\s*)', '', md_text)
            md_text = re.sub(r'(\s*```\s*)$', '', md_text)
            
            md_path = self.output_dir / f"{self.video_title}.md"
            md_path.write_text(md_text.strip(), encoding="utf-8")
            print(f"✅ 已產生重點筆記 → {md_path}")
            
            # 只有在處理本地檔案時才複製 SRT（URL 處理時 SRT 已在正確位置）
            if not is_url(getattr(self, 'url', '')):
                # 分析完自動複製 SRT 檔案到分類後資料夾，若目標已存在則自動備份
                output_srt = self.output_dir / f"{self.video_title}.srt"
                output_srt.parent.mkdir(parents=True, exist_ok=True)
                if output_srt.exists():
                    backup_path = output_srt.with_suffix(f".srt.bak_{int(time.time())}")
                    output_srt.rename(backup_path)
                    print(f"⚠️  目標 SRT 已存在，已自動備份為 {backup_path}")
                try:
                    # 使用移動，更有效率且避免重複檔案
                    shutil.move(str(srt_path), str(output_srt))
                    print(f"✅ 已將 {srt_path} 移動到 {output_srt}")
                except Exception as e:
                    print(f"⚠️  移動 SRT 檔案時發生錯誤：{e}")
                    print(f"   原始檔案仍在：{srt_path}")
            else:
                print(f"✅ SRT 檔案已保存在 {srt_path}")
            
        except Exception as e:
            logger.error(f"Error during summarization: {e}")

    def run(self):
        # 獲取原始影片時長用於驗證
        original_duration = self.get_video_duration()
        
        # 下載/提取音訊
        if not self.download_audio():
            print("❌ 音訊下載/提取失敗")
            return
            
        # 驗證音訊時長（如果是網路影片）
        if is_url(self.url) and original_duration > 0:
            if not self.verify_audio_duration(original_duration):
                print("⚠️  音訊時長驗證失敗，但繼續進行轉錄")
        
        # 轉錄音訊
        srt_path = self.transcribe_audio(model_size=self.whisper_model, language=self.language)
        if not srt_path:
            print("❌ 音訊轉錄失敗")
            return
            
        # 驗證 SRT 完整性（如果是網路影片）
        if is_url(self.url) and original_duration > 0:
            if not self.verify_srt(original_duration, srt_path):
                print("⚠️  SRT 完整性驗證失敗，但繼續進行重點整理")
        
        # 進行重點整理
        srt_file = self.srt_path
        if srt_file.exists():
            print("🟢 SRT 已產生，開始進行重點整理（MD 產出）...")
            self.summarize_srt(srt_file)
            # 清理暫存檔案
            self.cleanup_temp_files()

def is_url(s):
    return s.startswith('http://') or s.startswith('https://')

def ensure_dirs():
    # 自動建立 input、outputs、temp、Media_Notes 主要資料夾
    # 在 Docker 環境下，input 目錄掛載在 /input，所以優先檢查絕對路徑
    input_paths = ["/input", "input"]
    for input_path in input_paths:
        if pathlib.Path(input_path).exists():
            # 如果找到 input 目錄，就在同層建立其他目錄
            base_dir = pathlib.Path(input_path).parent
            break
    else:
        # 如果都沒找到，使用目前目錄
        base_dir = pathlib.Path(".")
    
    for d in ["input", "outputs", "temp", "Media_Notes"]:
        if d == "input" and pathlib.Path("/input").exists():
            # 在 Docker 環境下，input 已經掛載在 /input，不需要建立
            continue
        (base_dir / d).mkdir(parents=True, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument("input", help="影片網址或 input 資料夾內檔名（不含副檔名）", nargs="?")
args = parser.parse_args()

if __name__ == "__main__":
    ensure_dirs()
    # 新增主選單互動，防呆處理
    if not args.input:
        while True:
            print("請選擇要處理的來源：")
            print("[1] input 資料夾內的本地影片/SRT（只需輸入檔名）")
            print("[2] 連結（YouTube、m3u8）")
            print("[Q] 離開")
            user_choice = input("請輸入 1、2 或 Q：").strip().lower()
            if user_choice == '1':
                file_name = input("請輸入 input 資料夾內的檔名（不含副檔名）：").strip()
                args.input = file_name
                break
            elif user_choice == '2':
                url = input("請輸入影片連結（YouTube、m3u8）：").strip()
                args.input = url
                break
            elif user_choice == 'q':
                print("已離開程式。")
                sys.exit(0)
            else:
                print("請只輸入 1、2 或 Q，不要輸入說明文字！\n")
    if args.input:
        if is_url(args.input):
            vp = VideoProcessor(args.input)
            # 新增：詢問是否要一併下載影片（只允許 y/n/空白，其他重問）
            while True:
                ans = input("要一併下載影片檔嗎？(Y/N)：").strip().lower()
                if ans in ('', 'y'):
                    download_video = True
                    break
                elif ans == 'n':
                    download_video = False
                    break
                else:
                    print("請輸入 Y 或 N")
            if download_video:
                video_path = vp.output_dir / f"{vp.video_title}.mp4"
                if vp.is_m3u8:
                    # 用 m3u8_downloader 下載影片
                    m3u8_downloader = str(Path(__file__).parent / "m3u8_downloader.py")
                    venv_python = str(Path(vp.base_dir) / ".venv" / "Scripts" / "python.exe")
                    if Path(venv_python).exists():
                        python_exe = venv_python
                    else:
                        python_exe = sys.executable
                    cmd = [
                        python_exe,
                        m3u8_downloader,
                        vp.url,
                        '-o', str(video_path),
                        '--type', 'video'
                    ]
                    print(f"▶️  下載 GDC/m3u8 影片到 {video_path} ...")
                    subprocess.run(cmd, check=True)
                else:
                    # 其他來源預設用 yt-dlp
                    cmd = [
                        'yt-dlp',
                        '-f', 'bestvideo+bestaudio/best',
                        '--merge-output-format', 'mp4',
                        '-o', str(video_path),
                        vp.url
                    ]
                    print(f"▶️  下載影片到 {video_path} ...")
                    subprocess.run(cmd, check=True)
            vp.run()
        else:
            # 優先檢查 Docker 環境下的 /input 目錄
            input_dirs = [pathlib.Path("/input"), pathlib.Path("input")]
            video_path = None
            srt_path = None
            
            for input_dir in input_dirs:
                if not input_dir.exists():
                    continue
                    
                for ext in [".mp4", ".mkv", ".mov", ".avi", ".webm"]:
                    candidate = input_dir / f"{args.input}{ext}"
                    if candidate.exists():
                        video_path = candidate
                        break
                srt_candidate = input_dir / f"{args.input}.srt"
                if srt_candidate.exists():
                    srt_path = srt_candidate
                    
                if video_path or srt_path:
                    break
                    
            if srt_path:
                print(f"🟢 SRT 已搜尋到，開始進行重點整理：{srt_path}")
                # 使用完整的互動流程，與 URL 處理保持一致
                vp = VideoProcessor(srt_path.as_posix())
                vp.summarize_srt(srt_path)
            elif video_path:
                print(f"▶️  找到影片檔，開始提取音訊與轉錄：{video_path}")
                # 使用完整的互動流程，與 URL 處理保持一致
                vp = VideoProcessor(video_path.as_posix())
                vp.run()
            else:
                print(f"❌ input 資料夾找不到指定影片或 SRT：{args.input}")
    else:
        print("❌ 請提供影片網址或 input 資料夾內檔名（不含副檔名）")

