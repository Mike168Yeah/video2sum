@echo off
chcp 65001 >nul
title Video2Sum - 安裝與驗證工具

echo.
echo ========================================
echo    Video2Sum - 安裝與驗證工具
echo ========================================
echo.
echo 本工具將協助您完成以下步驟:
echo.
echo [步驟 1] 設定 Gemini API 金鑰
echo [步驟 2] 選擇 Gemini 模型(pro/flash/自訂)
echo [步驟 3] 驗證 API 金鑰與模型 
echo [步驟 4] 建立 Docker 映像檔
echo.
echo 執行方式:
echo   1. 按順序執行所有步驟(推薦)
echo   2. 選擇特定步驟執行
echo   3. 退出程式 (不會刪除 .env 檔案)
echo   4. 強制重設金鑰
echo.
set /p execution_mode=請選擇執行方式 (1/2/3/4):

if "%execution_mode%"=="3" (
    echo 已取消安裝。
    pause
    exit /b 0
)

if "%execution_mode%"=="4" goto reset_key

if "%execution_mode%"=="2" goto choose_step

echo.
echo ========================================
echo 開始按順序執行所有步驟...
echo ========================================

REM 步驟 1: 取得 Gemini API Key
:step1
REM ====== 依賴安裝檢查與安裝 ======
echo.
echo [依賴檢查] 檢查 python-dotenv 是否已安裝...
python -m pip show python-dotenv >nul 2>&1
if %errorlevel%==0 (
    echo ✅ 已安裝 python-dotenv，繼續下一步...
) else (
    echo [依賴安裝] 尚未安裝 python-dotenv，正在安裝必要依賴...
    where python
    python --version
    if errorlevel 1 (
        echo ❌ 找不到 python，請先安裝 Python 並設好 PATH！
        pause
        exit /b 1
    )
    python -m pip install --upgrade pip
    python -m pip install python-dotenv google-generativeai
    python -m pip show python-dotenv >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ 依賴安裝失敗，請檢查 Python/pip 是否安裝正確！
        pause
        exit /b 1
    )
    echo ✅ 依賴安裝完成，繼續下一步...
)
echo [提示] 本機端如需完整功能，請手動安裝 requirements.txt 內所有依賴。

REM 依賴安裝檢查與安裝結束

echo.
echo [步驟 1] 設定 Gemini API 金鑰
echo ========================================
REM 檢查 .env 是否已存在且有金鑰
set KEY_EXIST=
if exist .env (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if "%%a"=="VIDEO2SUM_GEMINI_API_KEY" set KEY_EXIST=1
    )
)
if defined KEY_EXIST (
    echo 已偵測到您已設定過 Gemini API 金鑰，將直接使用現有設定。
    pause
    goto step2
)
REM 沒有金鑰才輸入流程
call :input_key
goto step2

:input_key
set /p GEMINI_API_KEY=請輸入 Gemini API 金鑰:
if "%GEMINI_API_KEY%"=="" (
    echo 錯誤：請輸入有效的金鑰
    goto input_key
)
(echo VIDEO2SUM_GEMINI_API_KEY=%GEMINI_API_KEY%> .env)
echo 金鑰已儲存。
pause
exit /b

REM 步驟 2: 選擇 Gemini 模型
:step2
echo.
echo [步驟 2] 選擇 Gemini 模型
echo ========================================
set MODEL_CHOICE=
echo 請選擇要使用的 Gemini 模型:
echo   1. gemini-2.5-pro (預設)
echo   2. gemini-2.5-flash
echo   3. 其他（手動輸入）
set /p MODEL_CHOICE=請輸入選項編號（1/2/3）:
if "%MODEL_CHOICE%"=="2" (
    set VIDEO2SUM_GEMINI_MODEL=gemini-2.5-flash
) else if "%MODEL_CHOICE%"=="3" (
    set /p VIDEO2SUM_GEMINI_MODEL=請輸入自訂模型名稱:
) else (
    set VIDEO2SUM_GEMINI_MODEL=gemini-2.5-pro
)
REM 只覆蓋模型，不覆蓋金鑰，先讀取現有金鑰

set GEMINI_API_KEY=
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="VIDEO2SUM_GEMINI_API_KEY" set GEMINI_API_KEY=%%b
)
(echo VIDEO2SUM_GEMINI_API_KEY=%GEMINI_API_KEY%> .env)
(echo VIDEO2SUM_GEMINI_MODEL=%VIDEO2SUM_GEMINI_MODEL%>> .env)

REM 步驟 3: 驗證金鑰
:step3
echo.
echo [步驟 3] 驗證 API 金鑰與模型
echo ========================================
python verify_gemini.py
if errorlevel 1 (
    echo ❌ 金鑰驗證失敗，請檢查 .env 或金鑰內容。
    pause
    exit /b 1
)
echo ✅ 金鑰驗證成功！
pause
if "%execution_mode%"=="1" (
    goto step4
) else (
    goto the_end
)

:step4
echo.
echo [步驟 4] 建立 Docker 映像檔
echo ========================================
set /p build_docker=是否要開始 build docker? (y/n):
if /i "%build_docker%"=="y" (
    echo 開始 build docker...
    docker build -t video2sum .
    if %errorlevel%==0 (
        echo ✅ Docker build 完成！
        echo.
        echo ========================================
        echo 安裝完成！
        echo Press run_video2sum.bat to start。
        echo ========================================
        pause
        goto the_end
    ) else (
        echo ❌ Docker build 失敗，請檢查錯誤訊息。
        pause
        goto the_end
    )
) else (
    echo 已取消 build docker。
    pause
    goto the_end
)
echo.
pause
goto the_end

the_end:
echo.
echo 所有步驟已結束，請按任意鍵關閉視窗。
pause
exit /b 0

:choose_step
echo.
echo 請選擇要執行的步驟：
echo   1. 設定 Gemini API 金鑰
echo   2. 選擇 Gemini 模型
echo   3. 驗證 API 金鑰與模型 
echo   4. 建立 Docker 映像檔
echo.
set /p step_choice=請輸入步驟編號 (1-4):
if "%step_choice%"=="1" goto step1
if "%step_choice%"=="2" goto step2
if "%step_choice%"=="3" goto step3
if "%step_choice%"=="4" goto step4
echo 無效的選擇，將按順序執行所有步驟。
pause
goto the_end

:reset_key
echo.
echo [強制重設] 將刪除現有 .env 檔案並重新設定金鑰。
del /f /q .env >nul 2>&1
echo .env 檔案已刪除，請重新設定金鑰。
pause
goto step1

echo.
echo [依賴安裝] 正在安裝本機必要 Python 依賴（僅限驗證金鑰與模型）...
where python
python --version
if errorlevel 1 (
    echo ❌ 找不到 python，請先安裝 Python 並設好 PATH！
    pause
    exit /b 1
)
python -m pip install --upgrade pip
python -m pip install python-dotenv google-generativeai
python -m pip show python-dotenv
if %errorlevel% neq 0 (
    echo ❌ 依賴安裝失敗，請檢查 Python/pip 是否安裝正確！
    pause
    exit /b 1
)
echo [提示] 本機端如需完整功能，請手動安裝 requirements.txt 內所有依賴。 