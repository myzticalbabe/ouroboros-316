@echo off
:: ============================================================
:: TIKTOK RECORDING LAUNCHER
:: ============================================================
:: MODE 1 (default): Opens teleprompter + timer for Xbox Game Bar
:: MODE 2: Continuous 5-min auto-splitting via FFmpeg
:: ============================================================

echo ========================================
echo   TIKTOK RECORDING LAUNCHER
echo ========================================
echo.
echo   1 - Single Episode (Xbox Game Bar + Timer)
echo   2 - CONTINUOUS Recording (auto-split 5min)
echo.
set /p choice="   Choose mode (1 or 2): "

if "%choice%"=="2" goto continuous
if "%choice%"=="1" goto single

echo Invalid choice. Defaulting to single episode mode.
goto single

:single
echo.
echo [1/3] Opening complaint document as teleprompter...
start "" "COMPLAINT_TODO_LIST.html"
echo [2/3] Opening video script...
start "" "TIKTOK_VIDEO_SCRIPT.html"
echo [3/3] Starting 5-minute timer...
echo.
echo ========================================
echo   Press Win+Alt+R to start recording
echo   Timer alerts at 5 minutes
echo   Press Win+Alt+R to stop
echo   Video saves to: Videos\Captures\
echo ========================================
echo.
powershell -ExecutionPolicy Bypass -File "Record_5min_Timer.ps1"
goto done

:continuous
echo.
echo Starting CONTINUOUS recording mode...
echo Screen + mic will record in 5-minute segments
echo Files auto-save to: Desktop\TikTok_Videos\
echo Press Ctrl+C to stop
echo.
start "" "COMPLAINT_TODO_LIST.html"
start "" "TIKTOK_VIDEO_SCRIPT.html"
powershell -ExecutionPolicy Bypass -File "Record_Continuous.ps1"

:done
echo.
echo Recording session complete!
pause
