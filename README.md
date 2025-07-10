# 快速安裝與協作（for Git）

1. 下載專案
   ```bash
   git clone https://github.com/Mike168Yeah/video2sum.git video-to-summary
   cd video-to-summary
   ```
   > 你可以在任何資料夾下執行 clone 指令，或直接指定完整路徑，專案會安裝在你指定的位置。

   #### 範例1：先切換到目標資料夾再 clone
   ```powershell
   cd C:\MyProjects\AI
   git clone https://github.com/Mike168Yeah/video2sum.git video-to-summary
   cd video-to-summary
   ```

   #### 範例2：直接指定完整路徑 clone
   ```powershell
   git clone https://github.com/Mike168Yeah/video2sum.git "C:\MyProjects\AI\video-to-summary"
   cd "C:\MyProjects\AI\video-to-summary"
   ```

2. 執行安裝腳本
   ```bash
   ./install_video2sum.bat
   ```

3. 執行主程式
   ```bash
   ./run_video2sum.bat
   ```

> `.env` 會自動建立，API 金鑰請依照指示輸入即可。

# Video2Sum - 影片重點整理工具

自動將影片或 SRT 字幕整理成繁體中文重點筆記，支援 Docker、批次檔、Gemini API 模型自訂，適合團隊協作與 Obsidian 筆記整合。

---

## 目錄結構說明

```
video-to-summary/
├─ app/                  # 主要程式碼
├─ input/                # 放入待處理的 SRT 或影片檔案
├─ Media_Notes/          # 產生的 md 筆記與分類/子分類/主題 資料夾
├─ run_video2sum.bat     # 一鍵啟動（推薦）
├─ install_video2sum.bat # 安裝/設定/驗證/建置 Docker
├─ Dockerfile            # Docker 映像檔設定
└─ README.md             # 本說明文件
```

---

## 資料夾層級範例

```
Media_Notes/
    Programming/
        AI入門/
            How_God_of_War_uses_WHIP_PANS_One_Minute_Game_Design/
                How_God_of_War_uses_WHIP_PANS_One_Minute_Game_Design.md
                How_God_of_War_uses_WHIP_PANS_One_Minute_Game_Design.srt
```

---

## 分類互動流程

- 程式會自動偵測 Media_Notes 下所有分類資料夾（01-08 預設分類與自建分類）
- 09 代號可自訂分類名稱，C1、C2... 代表自建分類
- 若沒有任何分類，會詢問是否自動建立預設 01-08 分類，或自訂新分類
- 自建分類後仍可選擇是否一併建立預設分類
- 所有選擇都會有明確提示與防呆

### 互動範例

```
=== 請選擇影片分類 ===
  代號│分類名稱              │說明 (常放哪些影片)             │範例
────┼────────────────────┼-----------------------------┼----------------------
 [01]│Programming         │語言教學、框架實作、演算法、程式範例│Python、Rust、React
 ...
 [09]│自訂分類            │自訂資料夾                         │自訂

--- 其他自建分類 ---
 [C1]│影音教學
 [C2]│AI專案
 [C3]│深度學習

輸入代號 (01-09 或 C1...Cn)：
```

- 選 09 可自訂分類名稱，並可選擇是否一併建立預設分類
- 選 C1...Cn 直接選用自建分類
- 沒有分類時會詢問是否自動建立預設分類或自訂新分類

---

## 安裝與初始化（只需一次）

1. **安裝 Docker Desktop**（如未安裝，請先安裝）
2. **雙擊 `install_video2sum.bat`**
   - 依指示輸入 Gemini API 金鑰
   - 選擇 Gemini 模型（pro/flash/自訂）
   - 自動驗證金鑰與模型
   - 問你是否要 build Docker，建議直接同意
   - 完成後會自動建立 input、Media_Notes 等資料夾

---

## 處理影片或 SRT（每次使用）

### 方法一：雙擊批次檔（推薦）

1. **雙擊 `run_video2sum.bat`**
2. 依畫面指示輸入：
   - 影片連結（YouTube、GDC Vault...）或 input 資料夾內檔名
3. 程式會自動引導你完成：
   - 分類選擇（01-08 預設分類或自訂）
   - 子分類選擇（新建或沿用既有）
   - 語言選擇（英文/中文/日文）
   - **Whisper 模型選擇**（tiny/base/small/medium/large，預設 small）
4. 等待進度條完成，結果自動產生於 Media_Notes/分類/子分類/主題/
5. **連續處理**：完成後會詢問是否要分析下一個影片，可連續處理多個影片

### 方法二：手動 Docker 指令

```powershell
# 處理影片連結或 input 資料夾內檔案
# 請將 <API_KEY>、<影片連結或檔名> 替換成你的內容

docker run -it --rm \
  -v "${PWD}/input:/input" \
  -v "${PWD}/Media_Notes:/Media_Notes" \
  -v "${PWD}/.env:/app/.env" \
  -e VIDEO2SUM_GEMINI_API_KEY=<API_KEY> \
  -e VIDEO2SUM_GEMINI_MODEL=gemini-2.5-pro \
  video2sum <影片連結或檔名>
```

**注意：** 分類和主題會在執行時互動選擇，不需要在命令列指定。

---

## Obsidian 整合建議

- 直接將 `Media_Notes` 設為 Obsidian Vault，所有新產生的 md 檔會自動被 Obsidian 撈到
- 不需手動搬移或同步

---

## 常見問題排查

- **批次檔亂碼/echo 錯誤**：請用記事本另存為 UTF-8 (無 BOM)
- **Docker volume 掛載失敗**：請確認 Docker Desktop 的 File Sharing 有包含你的專案路徑
- **資料夾權限問題**：請用管理員權限執行 Docker 或調整資料夾權限
- **環境變數污染**：本專案只寫入 .env，不會污染全域
- **SRT/影片未自動分類**：請確認有正確輸入分類與主題
- **API 金鑰/模型錯誤**：請重新執行 install_video2sum.bat 設定

---

## 進階：自訂模型選擇

### Gemini 模型
- 安裝時可自訂 Gemini 模型名稱（如 pro、flash、其他）
- 執行時會自動讀取 .env 內的 VIDEO2SUM_GEMINI_MODEL
- 所有 Gemini API 呼叫都會用這個模型

### Whisper 模型選擇
執行時可選擇以下五種 Whisper 模型大小：

| 模型 | 記憶體需求 | 速度 | 準確度 | 適用場景 |
|------|------------|------|--------|----------|
| tiny | ~1GB | 最快 | 一般 | 快速測試、短影片 |
| base | ~1GB | 快 | 較好 | 一般用途、平衡選擇 |
| small | ~2GB | 中等 | 好 | **推薦預設、多語言** |
| medium | ~5GB | 較慢 | 很好 | 高品質需求 |
| large | ~10GB | 最慢 | 最佳 | 專業用途、複雜內容 |

**建議選擇：**
- 首次使用或一般用途：選擇 `small`
- 快速測試：選擇 `tiny`
- 高品質需求：選擇 `medium` 或 `large`
- 記憶體有限：選擇 `tiny` 或 `base`

---

## 完全可攜、彈性設計

- 專案資料夾可任意複製到任何路徑，所有邏輯自動運作
- 不需手動建資料夾，程式會自動建立
- 只要 Docker Desktop File Sharing 設定正確，任何路徑都能用

---

## 參考與詳細流程

- 詳細流程與分類規則請見 `app/Automation - Video to Summary.md`
- 有問題歡迎提 issue 或直接討論

- 所有自動產生的 md 檔案，會自動移除多餘的 ```（code block 標記），確保內容純淨、易於閱讀。
- Gemini 產生的時間碼（[hh:mm:ss] 或 hh:mm:ss）會自動轉換為 Markdown 超連結，方便直接跳轉影片片段。例如：[00:01:23](影片連結?t=83) 
