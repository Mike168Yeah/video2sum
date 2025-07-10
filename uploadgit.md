# Git 專案上傳與同步教學（以 video-to-summary 為例）

這份教學適合**初學者**，帶你從零開始把本機專案上傳到 GitHub，並學會日常同步、解決衝突、單檔案操作等常見情境。

---

## 1. 前言與目標
- 讓你學會如何把本機專案完整上傳到 GitHub
- 會教你日常如何同步、上傳、解決衝突、只上傳/下載單一檔案
- 適用於 Windows/Mac/Linux

---

## 2. 必備條件與環境
- 你已經有一個專案資料夾（例如 `video-to-summary`）
- 已安裝好 [Git](https://git-scm.com/)
- 已註冊 GitHub 帳號，並建立好一個空的 repo（例如 `video2sum`）

---

## 3. 第一次上傳專案到 GitHub（初始化流程）

### 步驟一：進入你的專案資料夾
```bash
cd /你的/專案/路徑/video-to-summary
```

### 步驟二：設定 git 身分認證（只需設定一次）
```bash
git config --global user.name "你的名字"
git config --global user.email "你的email@example.com"
```
> 建議 email 用你註冊 GitHub 的 email

### 步驟三：初始化 git
```bash
git init
```

### 步驟四：加入所有檔案並 commit
```bash
git add .
git commit -m "init: first release"
```

### 步驟五：設定遠端 repo
```bash
git remote add origin https://github.com/Mike168Yeah/video2sum.git
```
> 如果已經設定過遠端，這步可以跳過。

### 步驟六：推送到 GitHub
```bash
git branch -M main
git push -u origin main
```
> 如果你的 GitHub repo 預設是 master，請把 `main` 改成 `master`

---

## 4. 之後每次如何同步/上傳（日常開發流程）

### 上傳所有變更（推薦）
1. 先拉下最新遠端內容（避免衝突）：
   ```bash
   git pull --rebase origin main
   ```
2. 加入所有變更：
   ```bash
   git add .
   ```
3. 建立 commit：
   ```bash
   git commit -m "你的更新說明"
   ```
4. 推送到 GitHub：
   ```bash
   git push origin main
   ```

### 只上傳有修改的檔案
1. 只加入你有修改的檔案：
   ```bash
   git add 檔名1 檔名2
   ```
2. 建立 commit 並推送：
   ```bash
   git commit -m "只更新部分檔案"
   git push origin main
   ```

---

## 5. 常見問題與解法

### 5.1 遠端已存在內容導致 push 失敗
如果 push 時出現：
```
error: failed to push some refs to 'https://github.com/xxx/xxx.git'
hint: Updates were rejected because the remote contains work that you do not
hint: have locally. ...
```
請依下列步驟操作：
1. 先拉下遠端內容：
   ```bash
   git pull --rebase origin main
   ```
2. 如果有衝突，手動解決後：
   ```bash
   git add <有衝突的檔案>
   git rebase --continue
   ```
3. 再推送：
   ```bash
   git push origin main
   ```
> 這個流程不會自動刪除你的本機檔案，只有同名檔案內容不同時需要你手動合併，其他檔案都會保留。

### 5.2 強制覆蓋本機內容到 git（**不建議，請小心使用**）
```bash
git push --force origin main
```
> 這會把遠端 main 分支內容全部用你本機的內容取代，遠端原有 commit 會消失，請務必確認沒有人需要遠端的內容！

### 5.3 強制將 git 上的某個檔案覆蓋本機
```bash
git checkout origin/main -- 檔名
```
> 這會用遠端 main 分支的檔案直接覆蓋你本機的檔案。

### 5.4 只下載/同步 git 上的某個檔案（不強制，遇到衝突需手動解決）
```bash
git pull --rebase origin main
```
> 如果有衝突，手動解決後：
```bash
git add <有衝突的檔案>
git rebase --continue
```

### 5.5 git 身分認證錯誤
如果 commit 時出現如下錯誤：
```
Author identity unknown
*** Please tell me who you are.
...
fatal: unable to auto-detect email address
```
請依下列方式設定你的 git 使用者名稱與 email：
```bash
git config --global user.name "你的名字"
git config --global user.email "你的email@example.com"
```

---

## 6. 附錄：.gitignore 範例

請確認專案根目錄有 `.gitignore`，建議內容如下：

```gitignore
# 環境變數檔案（包含 API 金鑰）
.env

# 暫存檔案
temp/
*.tmp
*.temp

# 音訊和影片檔案
*.mp3
*.mp4
*.mkv
*.mov
*.avi
*.webm

# 日誌檔案
*.log
video_to_summary.log

# Python 暫存檔案
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so

# 虛擬環境
.venv/
venv/
env/

# IDE 檔案
.vscode/
.idea/
*.swp
*.swo
.obsidian/

# 作業系統檔案
.DS_Store
Thumbs.db

# Docker 相關
.dockerignore

# 備份檔案
*.bak
*.backup 
*.srt.bak_*

# 專案資料夾（只保留結構）
input/*
!input/.gitkeep
Media_Notes/*
!Media_Notes/.gitkeep
outputs/

# Jupyter
.ipynb_checkpoints/
```

---

有任何 git 操作問題，歡迎隨時提問！ 