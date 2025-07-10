# 專案上傳 GitHub 教學（以 video-to-summary 為例）

這份教學適用於任何本地專案，以下以 `video-to-summary` 專案為例，帶你一步步上傳到 GitHub。

---

## 1. 進入你的專案資料夾

```bash
cd /你的/專案/路徑/video-to-summary
```

---

## 2. 初始化 git（如果還沒 init 過）

```bash
git init
```

---

## 3. 設定 .gitignore（避免敏感檔案被上傳）

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

## 4. 加入所有檔案並 commit

```bash
git add .
git commit -m "init: first release"
```

---

## 5. 設定遠端 repo

```bash
git remote add origin https://github.com/Mike168Yeah/video2sum.git
```
> 如果已經設定過遠端，這步可以跳過。

---

## 6. 推送到 GitHub

```bash
git branch -M main
git push -u origin main
```
> 如果你的 GitHub repo 預設是 master，請把 `main` 改成 `master`

---

## 7. 完成！

你的專案就會出現在 GitHub 上，其他同事可以直接 clone 使用。

---

## 常見問題排查

- **remote already exists**
  > 執行：
  ```bash
  git remote remove origin
  git remote add origin https://github.com/Mike168Yeah/video2sum.git
  ```
- **推送時密碼問題**
  > 請用 GitHub Personal Access Token 當密碼，或設定 SSH 金鑰。
- **大檔案無法推送**
  > 請考慮用 Git LFS 或排除大檔案。

---

有任何 git 操作問題，歡迎隨時提問！ 