@echo off
echo ========================================
echo   SCROLL CAPTURE - 3.5 min MP4
echo ========================================
echo.
echo [1] Opening SCROLL_RECORD.html in Chrome...
start "" chrome --new-window --window-size=1100,900 --window-position=0,0 "file:///C:/Users/clint/SCROLL_RECORD.html?nocache=%RANDOM%"

echo [2] Waiting 6 seconds for countdown...
timeout /t 6 /nobreak >nul

echo [3] Recording 310 seconds...
ffmpeg -f gdigrab -framerate 30 -offset_x 0 -offset_y 0 -video_size 1100x900 -i desktop -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -g 60 -an -t 220 -y "%USERPROFILE%\Desktop\TikTok_Videos\SCROLL_CAPTURE.mp4"

echo.
echo [4] DONE! File saved to TikTok_Videos\SCROLL_CAPTURE.mp4
pause
