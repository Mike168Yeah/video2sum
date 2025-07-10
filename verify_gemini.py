import os
import sys

print("=== Gemini API 金鑰驗證除錯腳本 ===")
print(f"[1] 目前工作目錄: {os.getcwd()}")

# 檢查 .env 檔案是否存在
env_path = os.path.join(os.getcwd(), '.env')
if os.path.exists(env_path):
    print(f"[2] .env 檔案存在於: {env_path}")
    # 不再印出 .env 內容，避免洩漏金鑰
else:
    print("[2] ❌ 找不到 .env 檔案於目前目錄！")

# 只在失敗時才顯示詳細步驟
show_debug = False

# 嘗試載入 dotenv
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
    print("[4] 已嘗試載入 .env 檔案")
except ImportError:
    if show_debug:
        print("[4] 未安裝 python-dotenv，略過 .env 載入")

# 顯示目前環境變數（移除金鑰內容顯示）
api_key = os.environ.get("VIDEO2SUM_GEMINI_API_KEY")
model_name = os.environ.get("VIDEO2SUM_GEMINI_MODEL", "gemini-2.5-pro")
print(f"[5] 目前環境變數 VIDEO2SUM_GEMINI_API_KEY: (已隱藏)")
print(f"[6] 目前環境變數 VIDEO2SUM_GEMINI_MODEL: {model_name}")

if not api_key:
    print("[驗證失敗] 找不到 VIDEO2SUM_GEMINI_API_KEY，請檢查 .env 或環境變數！")
    print(f"[DEBUG] cwd: {os.getcwd()}")
    print(f"[DEBUG] .env 存在: {os.path.exists(env_path)}")
    if os.path.exists(env_path):
        print(f"[DEBUG] .env 路徑: {env_path}")
    sys.exit(1)

try:
    import google.generativeai as genai
except ImportError:
    print("[驗證失敗] 未安裝 google-generativeai，請先安裝！")
    sys.exit(1)

print("[9] 開始驗證 Gemini API 金鑰與模型...")
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    r = model.generate_content("hello", generation_config={"temperature": 0.1})
    print("[10] ✅ 金鑰與模型驗證成功！Gemini API 可正常使用。")
except Exception as e:
    print("[驗證失敗] 金鑰或模型驗證失敗！")
    print(f"[DEBUG] cwd: {os.getcwd()}")
    print(f"[DEBUG] .env 存在: {os.path.exists(os.path.join(os.getcwd(), '.env'))}")
    print(f"[DEBUG] VIDEO2SUM_GEMINI_API_KEY: {'有值' if api_key else '無值'}")
    print(f"[DEBUG] VIDEO2SUM_GEMINI_MODEL: {model_name}")
    print(f"[DEBUG] 錯誤訊息: {e}")
    sys.exit(2) 