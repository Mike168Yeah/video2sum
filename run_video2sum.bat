@echo off
REM ===============================================
REM 建議儲存編碼：UTF-8 (無 BOM) 或 ANSI，避免亂碼與批次檔誤判
REM ===============================================
cd /d "%~dp0"

REM : --- 檢查 Docker 是否已安裝 ---
docker --version >nul 2>&1
if errorlevel 1 (
    echo : 錯誤：找不到 Docker，請先安裝 Docker Desktop。
    pause
    exit /b 1
)

REM : --- 檢查 video2sum 映像檔是否存在 ---
docker images video2sum --format "table {{.Repository}}" | findstr "video2sum" >nul 2>&1
if errorlevel 1 (
    echo : 錯誤：找不到 video2sum 映像檔，請先執行 install_video2sum.bat 建立映像檔。
    pause
    exit /b 1
)

REM : --- 自動偵測 PowerShell，若是則自動用 cmd.exe 重新執行自己 ---
setlocal
set "ps_check=%ComSpec%"
if not "%ps_check%"=="%SystemRoot%\system32\cmd.exe" (
    echo : [防呆] 偵測到非 cmd.exe 環境，將自動切換到命令提示字元...
    cmd.exe /c "%~f0" %*
    exit /b
)
endlocal
chcp 65001 > nul

REM : === 簡化的不可見字元檢查 ===
REM 暫時停用複雜的檢查功能，避免程式卡住

REM : --- 讀取 .env 取得金鑰與模型 ---
setlocal enabledelayedexpansion
set "ENV_FILE=.env"
set "API_KEY="
set "MODEL="
if exist %ENV_FILE% (
    for /f "tokens=1,2 delims==" %%a in (%ENV_FILE%) do (
        if "%%a"=="VIDEO2SUM_GEMINI_API_KEY" set "API_KEY=%%b"
        if "%%a"=="VIDEO2SUM_GEMINI_MODEL" set "MODEL=%%b"
    )
) else (
    echo : 錯誤：找不到 .env 設定檔，請先執行 install_video2sum.bat。
    pause
    exit /b 1
)
if not defined API_KEY (
    echo : 錯誤：.env 未設定 VIDEO2SUM_GEMINI_API_KEY。
    pause
    exit /b 1
)
if not defined MODEL (
    set "MODEL=gemini-2.5-pro"
)
:main_loop
echo : ================================================================
echo :   影片轉摘要工具 (Docker 版)
echo : ================================================================
echo.
echo :   請選擇要處理的來源：
echo :   [1] Local video/SRT file in input folder (enter filename only)
echo :   [2] Video URL
echo :   [Q] Quit
echo : ----------------------------------------------------------------
:input_choice
set /p source_choice=請輸入您的選擇 (1, 2, Q): 
set source_choice=%source_choice: =%
if /i "%source_choice%"=="1" goto process_local_file
if /i "%source_choice%"=="2" goto process_url
if /i "%source_choice%"=="Q" goto the_end
if /i "%source_choice%"=="q" goto the_end
echo : 無效的選擇，請只輸入 1、2 或 Q。
goto input_choice
REM : --- 處理本地檔案 ---
:process_local_file
echo.
set /p file_name=請輸入 input 資料夾內的檔名（不含副檔名）: 
if not defined file_name (
    echo : 檔名不能為空。
    goto process_local_file
)

REM : --- 檢查必要資料夾是否存在 ---
if not exist "input" (
    echo : 警告：input 資料夾不存在，正在建立...
    mkdir "input"
)
if not exist "Media_Notes" (
    echo : 警告：Media_Notes 資料夾不存在，正在建立...
    mkdir "Media_Notes"
)

REM 使用更穩定的路徑變數
set "PROJECT_ROOT=%cd%"
set "DOCKER_INPUT=%PROJECT_ROOT%\input:/input"
set "DOCKER_MEDIA=%PROJECT_ROOT%\Media_Notes:/Media_Notes"
set "DOCKER_ENV=%PROJECT_ROOT%\.env:/app/.env"

docker run -it --rm -v "%DOCKER_INPUT%" -v "%DOCKER_MEDIA%" -v "%DOCKER_ENV%" -e VIDEO2SUM_GEMINI_API_KEY=!API_KEY! -e VIDEO2SUM_GEMINI_MODEL=!MODEL! video2sum "!file_name!"
goto ask_continue
REM : --- 處理影片連結 ---
:process_url
echo.
set /p video_url=請貼上影片連結: 
if not defined video_url (
    echo : 連結不能為空。
    goto process_url
)

REM : --- 檢查必要資料夾是否存在 ---
if not exist "input" (
    echo : 警告：input 資料夾不存在，正在建立...
    mkdir "input"
)
if not exist "Media_Notes" (
    echo : 警告：Media_Notes 資料夾不存在，正在建立...
    mkdir "Media_Notes"
)

REM 使用更穩定的路徑變數
set "PROJECT_ROOT=%cd%"
set "DOCKER_INPUT=%PROJECT_ROOT%\input:/input"
set "DOCKER_MEDIA=%PROJECT_ROOT%\Media_Notes:/Media_Notes"
set "DOCKER_ENV=%PROJECT_ROOT%\.env:/app/.env"

docker run -it --rm -v "%DOCKER_INPUT%" -v "%DOCKER_MEDIA%" -v "%DOCKER_ENV%" -e VIDEO2SUM_GEMINI_API_KEY=!API_KEY! -e VIDEO2SUM_GEMINI_MODEL=!MODEL! video2sum "!video_url!"
goto ask_continue
:ask_continue
echo.
echo : ----------------------------------------
:continue_choice_loop
set /p continue_choice=任務完成。是否要處理下一個影片？ (Y/N): 
set continue_choice=%continue_choice: =%
if /i "%continue_choice%"=="Y" goto main_loop
if /i "%continue_choice%"=="y" goto main_loop
if /i "%continue_choice%"=="N" goto the_end
if /i "%continue_choice%"=="n" goto the_end
echo : 請只輸入 Y 或 N。
goto continue_choice_loop
:the_end
echo.
echo :   感謝使用，掰掰！
pause
exit