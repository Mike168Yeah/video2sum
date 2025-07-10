# Video2Sum - 完整使用指南與工作流程

自動將影片或 SRT 字幕整理成繁體中文重點筆記，支援 Docker、批次檔、Gemini API 模型自訂，適合團隊協作與 Obsidian 筆記整合。

---

## 📋 快速部署與使用

### 1. 準備環境
- 安裝 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- 確保 Docker Desktop 已啟動

### 2. 取得專案
```bash
# 方法一：從 Git 複製
git clone <你的專案URL>
cd video-to-summary

# 方法二：直接複製資料夾
# 將整個 video-to-summary 資料夾複製到任意位置
```

### 3. 初始化設定
```bash
# 雙擊執行安裝腳本
install_video2sum.bat
```

**注意**：
- 需要輸入你的 Gemini API 金鑰
- 選擇 Gemini 模型（建議使用 gemini-2.5-pro）
- 同意建立 Docker 映像檔

### 4. 開始使用
```bash
# 雙擊執行主程式
run_video2sum.bat
```

---

## 🏗️ 專案架構與路徑設計

### 完全可攜設計
- ✅ **完全可攜**：專案可在任何路徑執行（C:\、D:\、E:\ 等）
- ✅ **自動建立資料夾**：input、Media_Notes 等資料夾會自動建立
- ✅ **相對路徑**：所有路徑都是相對於專案根目錄

### 資料夾結構
```
video-to-summary/
├── app/                  # 主要程式碼
├── input/                # 放入待處理的 SRT 或影片檔案（自動建立）
├── Media_Notes/          # 產生的 md 筆記與分類/子分類/主題 資料夾（自動建立）
├── .env                  # API 金鑰設定（安裝時建立）
├── run_video2sum.bat     # 一鍵啟動（推薦）
├── install_video2sum.bat # 安裝/設定/驗證/建置 Docker
├── Dockerfile            # Docker 映像檔設定
└── README.md             # 本說明文件
```

### 環境變數
- `.env` 檔案包含你的 API 金鑰，**請妥善保管**
- 建議將 `.env` 加入 `.gitignore`，避免上傳到 Git

---

## 🎯 使用流程

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

## 📁 資料夾層級範例

```
Media_Notes/
    Programming/
        AI入門/
            How_God_of_War_uses_WHIP_PANS_One_Minute_Game_Design/
                How_God_of_War_uses_WHIP_PANS_One_Minute_Game_Design.md
                How_God_of_War_uses_WHIP_PANS_One_Minute_Game_Design.srt
```

---

## 🔧 進階設定

### Gemini 模型選擇
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

## 🤝 團隊協作與部署

### 多同事使用建議
- **每人複製一份專案資料夾**
- **或使用不同的 API 金鑰**
- **避免同時使用同一個 Media_Notes 資料夾**

### 常見問題

#### Q: 可以放在任何路徑嗎？
**A: 可以！** 專案使用相對路徑，放在 C:\、D:\、桌面、文件夾都可以。

#### Q: 需要修改任何設定嗎？
**A: 不需要！** 安裝完成後直接使用即可。

#### Q: 如果路徑包含空格怎麼辦？
**A: 沒問題！** 批次檔已處理路徑中的空格。

---

## 🔍 故障排除

### Docker 相關
```bash
# 檢查 Docker 是否正常
docker --version

# 檢查映像檔是否存在
docker images video2sum

# 重新建立映像檔
docker build -t video2sum .
```

### 權限問題
- 確保 Docker Desktop 有權限存取專案資料夾
- 在 Docker Desktop 設定中確認 File Sharing 包含專案路徑

### API 金鑰問題
- 重新執行 `install_video2sum.bat`
- 檢查 `.env` 檔案是否存在且格式正確

### 其他常見問題
- **批次檔亂碼/echo 錯誤**：請用記事本另存為 UTF-8 (無 BOM)
- **Docker volume 掛載失敗**：請確認 Docker Desktop 的 File Sharing 有包含你的專案路徑
- **資料夾權限問題**：請用管理員權限執行 Docker 或調整資料夾權限
- **環境變數污染**：本專案只寫入 .env，不會污染全域
- **SRT/影片未自動分類**：請確認有正確輸入分類與主題

---

## 📚 Obsidian 整合建議

- 直接將 `Media_Notes` 設為 Obsidian Vault，所有新產生的 md 檔會自動被 Obsidian 撈到
- 不需手動搬移或同步

---

## 工作流程：從網路影片到重點概要

本文檔記錄了將網路影片 (通常為英文 YouTube 影片) 轉換為帶時間碼的文字稿 (英文 SRT)，並進一步整理成繁體中文重點概要的處理流程。
使用者如果提供帶影片 URL 且「未經整理」的文檔，就自動「完整執行」下列流程。

## Python 工具使用方式

```powershell
# 基本用法
python video_to_summary.py "視頻URL"

# 語言選擇會在執行時互動選擇（英文/中文/日文）
# 模型大小會在執行時互動選擇（tiny, base, small, medium, large）
```

### 使用範例
# 主機端直接執行
python "./app/video_to_summary.py" "https://www.youtube.com/live/AjgxaDRreYs"

# Docker 環境執行（Linux/macOS）
docker run --rm -v "$(pwd)/input:/input" -v "$(pwd)/Media_Notes:/Media_Notes" -v "$(pwd)/.env:/app/.env" -e VIDEO2SUM_GEMINI_API_KEY=$VIDEO2SUM_GEMINI_API_KEY -e VIDEO2SUM_GEMINI_MODEL=$VIDEO2SUM_GEMINI_MODEL video2sum 檔名（不含副檔名）

# Docker 環境執行（Windows PowerShell）
docker run --rm -v "${PWD}/input:/input" -v "${PWD}/Media_Notes:/Media_Notes" -v "${PWD}/.env:/app/.env" -e VIDEO2SUM_GEMINI_API_KEY=$env:VIDEO2SUM_GEMINI_API_KEY -e VIDEO2SUM_GEMINI_MODEL=$env:VIDEO2SUM_GEMINI_MODEL video2sum 檔名（不含副檔名）

## 必要輸入與預設處理邏輯

*   **使用者需提供**: 
    *   **影片 URL**: 網路影片的有效連結。
*   **AI 助理預設處理**: 
    *   **Whisper 模型**: 支援選擇 tiny/base/small/medium/large 五種模型大小，預設使用 `small` 模型。各模型特點：
    *   **tiny**: ~1GB 記憶體，最快速度，一般準確度，適合快速測試
    *   **base**: ~1GB 記憶體，快速度，較好準確度，平衡選擇
    *   **small**: ~2GB 記憶體，中等速度，好準確度，推薦預設
    *   **medium**: ~5GB 記憶體，較慢速度，很好準確度，高品質需求
    *   **large**: ~10GB 記憶體，最慢速度，最佳準確度，專業用途
    *   **轉錄稿格式**: 預設輸出為 `srt` (包含時間碼)。
    *   **語言偵測**: 語言會在執行時互動選擇（英文/中文/日文），支援連續處理多個影片。
    *   **二次處理**: 如果使用 `small` 模型轉錄的結果不夠清晰或完整，AI 助理會詢問使用者是否同意使用更大的模型重新進行轉錄。
*   **自動建立資料夾**: 啟動 Docker 時會自動建立 input、outputs、temp、Media_Notes 等必要資料夾。
*   **SRT 自動搬移**: 若直接用 input/xxx.srt 進行重點整理，分析完會自動將該 srt 檔搬移到分類後的資料夾（如 outputs/分類/主題/xxx.srt）。

## 步驟概覽

1.  **準備工具**: 確保必要的工具已安裝。並檢查目標資料夾有哪些資料，用於確認跳轉到哪個步驟。
2.  **獲取影片元數據 (包含時長)**: 從影片 URL 獲取元數據，特別是影片總時長。
3.  **提取音訊**: 從影片 URL 下載音訊檔案。
    *   **3.1 驗證下載音訊時長**: 比對下載的音訊檔案時長與原始影片時長。
4.  **音訊轉文字 (預設 small 模型, SRT 格式)**: 使用語音辨識工具將音訊轉換為文字稿。
    *   **4.1 驗證 SRT 轉錄完整性**: 比對生成的 SRT 檔案的最後時間碼與原始影片時長。
5.  **（可選）二次轉錄**: 若首次結果不佳或驗證未通過，經使用者同意後，可使用更大模型重新轉錄。
6.  **內容整理**: 根據最終的文字稿整理重點概要。

## 詳細步驟與指令

**協作提示：** 此流程為標準化操作，AI 助理對 `yt-dlp` 或 `whisper` 命令的執行無需重複確認批准。

**命令執行規則：**
*   **Windows PowerShell 環境**:
    *   不使用 `&&` 連接多個命令，而是使用分號 `;` 或換行執行
    *   較長命令建議使用反引號 `` ` `` 換行，保持可讀性
    *   範例：
        ```powershell
        # 使用分號
        $duration = yt-dlp --print "%(duration)s" "[影片URL]"; echo $duration

        # 使用換行
        yt-dlp --print "%(duration)s" "[影片URL]" | `
        Set-Variable -Name "duration"

        # 長命令換行
        yt-dlp -x --audio-format mp3 `
            --continue --no-part `
            -o "[輸出路徑]/[影片英文標題].mp3" `
            "[影片URL]"
        ```

### 1. 準備工具

Python 工具 `video_to_summary.py` 會自動處理所有必要的流程

### 2. 獲取影片元數據 (包含時長)

Python 工具會自動取得影片時長資訊，用於後續驗證。

### 3. 提取音訊

#### URL 格式判斷

根據影片來源自動選擇下載方式：
- 一般視頻網站（如 YouTube）：使用 `yt-dlp` 下載
- 串流媒體（如 gdcvault.com）：使用 M3U8 下載工具
     ```powershell
     # 對於 GDC Vault 等串流媒體網站
     python ./app/m3u8_downloader.py "[串流URL]" -o "[影片英文標題].mp3" --type audio
     ```

Python 工具會自動下載影片音訊並轉換為 MP3 格式。下載完成後會自動驗證音訊時長是否與原始影片相符。

### 4. 音訊轉文字 (生成 SRT)

Python 工具會使用 Whisper 自動將音訊轉換為 SRT 字幕檔。轉換完成後會自動驗證 SRT 內容的完整性。
    
### 5. （可選）二次轉錄

若首次轉錄結果不佳或驗證未通過，經使用者同意後，可使用更大模型重新轉錄。Python 工具提供以下參數供選擇：
*   **模型大小**: tiny < base < small < medium < large


### 6. 內容整理

*   **輸入**: 最終生成的 SRT 檔案，以及目標 MD 檔的影片連結。
             (MD 檔內如果有影片連結需要按步驟7的格式保留下來)
*   **方法**: 
    *   讀取 SRT 檔案內容。
    *   根據時間碼和文字內容，理解影片結構。然後依據下列規範整理成"繁體中文"文檔，不允許縮減步驟、流程或簡化解釋。
    *   主題分段：通讀 SRT，根據明顯主題轉換（如新章節、話題切換、流程步驟）進行分段，可參考影片目錄、簡報標題、講者語氣轉折等。
    *   條列重點：每個主題下，明確列出最重要的概念、術語、流程、挑戰、解決方案，並涵蓋具體操作步驟、工具用法、參數設置、遇到的問題與解決方式。
    *   技術細節：對於流程導向內容，建議以「步驟 1、2、3」或流程圖方式呈現，避免僅列舉結果，需涵蓋過程與思考脈絡。
    *   層次結構：每個主題下建議分為「流程/步驟」、「技術重點」、「挑戰與解決」、「關鍵詞」等層級，利用標題和項目符號建立清晰層次。
    *   術語標註：對於專業術語、工具名稱，建議中英文並列，首次出現時簡要說明；如遇新技術、模型、專案名稱，應補充簡短解釋。
    *   資訊易懂性：請基於該領域專家的角度進行整理，將讀者的知識水平視為高中畢業生，確保讀者即使沒接觸過該領域也能理解內文。
    *   多語言處理：若影片含多語言或文化背景差異，應於摘要中標註語言切換點，並簡要說明文化脈絡。
    *   在每個主要段落的"標題下方"添加時間戳記的 YouTube 跳轉連結，**請直接用 Markdown 超連結格式**，如：
        - [00:12:34](https://www.youtube.com/watch?v=xxxx&t=754s) 這裡是重點內容
        - hh:mm:ss 是時間碼，xxxx 是影片 ID，NNN 是秒數（如 00:12:34 → 754）
        - 請勿重複貼出純網址或非標準格式
    *   **特別規範：Gemini 產生的 markdown 內容禁止加上 ``` 或 ```markdown 或任何 code block 標記，必須是純 markdown 內容。**

### 7. 參考格式 

<!-- 影片資訊: 原始時長: "1:11:14" 影片URL: "https://XXXX.XXX.XX" -->
(使用 yaml 語法儲存，在 MD 檔中不顯示)

### 主題優先 (Thematics First)
原始影片：[hh:mm:ss](https://www.youtube.com/watch?v=XXXX.XXX.XX)
*   靈感來源：劍橋分析 (Cambridge Analytica)
(上述為範例，但須嚴格按照上述模板進行斷行，確保文檔結構一致性與可讀性)

---

## 7.1 終極影片知識整理規範（Ultimate Video Knowledge Note Standard）

### 檔案結構與命名
- 每部影片一個資料夾，路徑：`Media_Notes/分類/主題/影片標題/`
- 主要檔案：`影片標題.md`（重點整理）、`影片標題.srt`（逐字稿）

### 檔案開頭格式
- **YAML 註解**（HTML 註解包裹，MD 內不顯示）：
  ```markdown
  <!--
  標題: "【GDC 2019】環境設計作為空間影像構建：理論與實踐"
  原始標題: "Environment Design as Spatial Cinematography: Theory and Practice"
  來源: "YouTube"
  影片URL: "https://www.youtube.com/watch?v=L27Qb20AYmc"
  原始時長: "00:51:54"
  分類: "GameDev_Design"
  主題: "環境設計"
  標籤: [GDC, 環境設計, 空間攝影, 遊戲美術]
  日期: "2025-06-24"
  作者: "Aven Chen"
  -->
  ```

### 主題分段與時間碼
- 每個主題（如「演講者介紹與團隊職責」、「環境設計作為空間電影攝影的核心概念」等）都應有 `#### 主題名稱` 標題，標題下方加上時間碼超連結。
  ```markdown
  #### 演講者介紹與團隊職責
  [00:00:18](https://www.youtube.com/watch?v=L27Qb20AYmc&t=18s)
  ```

### 條列與層次
- 條列內容可多層巢狀，建議如下：
    - 流程/步驟
    - 技術重點
        - 攝影構圖
            - 三分法則：將主體放在三分線上，提升畫面張力
            - 避免切線：調整物體位置，避免視覺混淆
        - 深度營造
            - 前景/中景/背景分層，創造空間感
        - 顯著性（Saliency）
            - 色彩對比、形狀、運動吸引注意力
    - 挑戰與解決
        - 玩家自由移動 vs. 開發者引導
            - 解法：利用地標、光線、路徑設計引導玩家
    - 關鍵詞
    - 術語標註
- 條列下的每一點，建議盡量「具體描述」講者的原意與案例，避免僅列名詞。

#### 更細緻且具體的條列範例
```markdown
#### 技術重點
- 控制 2D 螢幕：
    - 3D 環境的 2D 構圖：遊戲開發與其他媒體（繪畫、攝影、電影）的關鍵區別在於，我們需要為 2D 螢幕構圖 3D 環境。
        - Previs 模型應用：用於預先視覺化螢幕上的呈現效果，並解決遊戲設計、環境藝術、藝術指導和敘事等方面的功能性問題。
        - 設計考量：圍繞「瓶頸點 (choke points)」和「通過路徑 (through routes)」進行設計，這些是玩家視角可預測的區域。
        - 實例：GTA5 線上 DLC 實驗室區域，最終構圖與 Previs 不同，但 Previs 提供良好基礎。
    - 構圖技巧：
        - 三分法則：將螢幕分為三等份，將主要構圖重心放在這些分割線上，而非中心。
        - 避免切線：調整物體位置或大小，避免視覺上的混淆。
        - 實例：調整桌子長度，使其不再與後方牆壁對齊，改善空間可讀性。
```

### 內容易讀性
- 每個主題下的條列內容要具體、明確，避免空泛描述。
- 若有多語言或文化脈絡，請標註並簡要說明。

### 參考資料
- 參考資料區塊可用 `#### 參考資料`，條列所有引用書籍、論文、線上資源，並加上時間碼。

#### 綜合範例
```markdown
<!--
標題: "【GDC 2019】環境設計作為空間影像構建：理論與實踐"
原始標題: "Environment Design as Spatial Cinematography: Theory and Practice"
來源: "YouTube"
影片URL: "https://www.youtube.com/watch?v=L27Qb20AYmc"
原始時長: "00:51:54"
分類: "GameDev_Design"
主題: "環境設計"
標籤: [GDC, 環境設計, 空間攝影, 遊戲美術]
日期: "2025-06-24"
作者: "Aven Chen"
-->

### 主題優先 (Thematics First)
原始影片：[00:00:00](https://www.youtube.com/watch?v=L27Qb20AYmc)

#### 演講者介紹與團隊職責
[00:00:18](https://www.youtube.com/watch?v=L27Qb20AYmc&t=18s)
- 流程/步驟：
    1. Miriam Ballard 介紹背景（建築、電影、遊戲）
    2. 團隊組成與職責說明
- 技術重點：
    - Previs 模型（Pre-visualization，預先視覺化）：環境初步探索草圖
    - 3D 為主，2D 為輔
- 挑戰與解決：
    - 跨領域團隊協作
    - 藝術部門主導環境佈局
- 關鍵詞：
    - Previs, 3D, 團隊協作, Rockstar
- 術語標註：
    - Previs（Pre-visualization，預先視覺化模型）

#### 環境設計作為空間電影攝影的核心概念
[00:03:23](https://www.youtube.com/watch?v=L27Qb20AYmc&t=203s)
- 流程/步驟：
    1. 控制 2D 螢幕
    2. 控制移動
    3. 控制時間
- 技術重點：
    - 2D 構圖、三分法則、避免切線、創造深度
    - 顯著性（Saliency）、可供性（Affordances）
- 挑戰與解決：
    - 玩家自由 vs. 開發者引導
    - 空間過渡設計
- 關鍵詞：
    - 2D 構圖, 顯著性, 可供性, 空間過渡
- 術語標註：
    - Saliency（顯著性，吸引玩家注意力的特徵）
    - Affordances（可供性，物體允許的行動）

#### 參考資料
[00:51:54](https://www.youtube.com/watch?v=L27Qb20AYmc&t=3114s)
- 《The Filmmaker's Eye》
- 《Visual Attention in 3D Games》
- 《The Design of Everyday Things》
- 《The Experience of Landscape》
- 《The Image of the City》
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

## 進度條顯示

本工具已內建 tqdm 進度條，SRT 產生時會顯示進度條，Dockerfile 會自動安裝 tqdm，無需手動安裝。

## 安裝與初始化（只需一次）

1. **安裝 Docker Desktop**（如未安裝，請先安裝）
2. **雙擊 `install_video2sum.bat`**
   - 依指示輸入 Gemini API 金鑰
   - 選擇 Gemini 模型（pro/flash/自訂）
   - 自動驗證金鑰與模型
   - 問你是否要 build Docker，建議直接同意
   - 完成後會自動建立 input、Media_Notes 等資料夾
   - **本機執行批次檔時會自動安裝最小依賴（python-dotenv、google-generativeai），如需完整功能請手動執行 `pip install -r requirements.txt`**

## [NEW] Docker 指令與資料夾自動建立

- 所有 Docker 指令建議統一：

```powershell
# 處理影片連結
# <API_KEY>、<影片連結> 請替換

docker run -it --rm \
  -v "${PWD}/input:/input" \
  -v "${PWD}/Media_Notes:/Media_Notes" \
  -v "${PWD}/.env:/app/.env" \
  -e VIDEO2SUM_GEMINI_API_KEY=<API_KEY> \
  -e VIDEO2SUM_GEMINI_MODEL=gemini-2.5-pro \
  video2sum <影片連結>
```
- input、Media_Notes 等資料夾會自動建立，不需手動新增。
- 分類和主題會在執行時互動選擇，不需要在命令列指定。

---

## [NEW] SRT 分析、分類搬移與自動備份

- 分析完 SRT 會自動搬移到 Media_Notes/分類/主題/ 目錄下。
- 若目標已存在同名 SRT，會自動備份舊檔（加上時間戳或 .bak）。

---

## [NEW] 互動式分類與主題輸入

- 不論影片連結或本地檔案，執行時都會互動詢問分類代碼與主題名稱。
- 輸入後會即時顯示「已收到分類代碼，繼續下個階段」等確認訊息。

---

## [NEW] Obsidian Vault 整合建議

- 建議直接把 Media_Notes 設為 Obsidian Vault，所有新產生的 md 檔都會自動被 Obsidian 撈到，不需搬移或同步。

---

## [NEW] 常見問題排查

- **批次檔亂碼/echo 錯誤**：請用記事本另存為 UTF-8 (無 BOM)
- **Docker volume 掛載失敗**：請確認 Docker Desktop 的 File Sharing 有包含你的專案路徑
- **資料夾權限問題**：請用管理員權限執行 Docker 或調整資料夾權限
- **環境變數污染**：本專案只寫入 .env，不會污染全域
- **SRT/影片未自動分類**：請確認有正確輸入分類與主題
- **API 金鑰/模型錯誤**：請重新執行 install_video2sum.bat 設定

---

## [NEW] 完全可攜、彈性設計

- 專案資料夾可任意複製到任何路徑，所有邏輯自動運作
- 不需手動建資料夾，程式會自動建立
- 只要 Docker Desktop File Sharing 設定正確，任何路徑都能用

- 所有自動產生的 md 檔案，會自動移除多餘的 ```（code block 標記），確保內容純淨、易於閱讀。
- Gemini 產生的時間碼（[hh:mm:ss] 或 hh:mm:ss）會自動轉換為 Markdown 超連結，方便直接跳轉影片片段。例如：[00:01:23](影片連結?t=83)
