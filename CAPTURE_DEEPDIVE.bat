@echo off
echo ========================================
echo   DEEP DIVE SCROLL CAPTURE - 2 min MP4
echo ========================================
echo.
echo [1] Opening SCROLL_DEEPDIVE.html in Chrome...
start "" chrome --new-window --window-size=1080,900 --window-position=0,0 "file:///C:/Users/clint/SCROLL_DEEPDIVE.html?nocache=%RANDOM%"

echo [2] Waiting 6 seconds for countdown...
timeout /t 6 /nobreak >nul

echo [3] Recording 130 seconds...
ffmpeg -f gdigrab -framerate 30 -offset_x 0 -offset_y 0 -video_size 1080x900 -i desktop -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -g 60 -an -t 130 -y "%USERPROFILE%\Desktop\TikTok_Videos\DEEPDIVE_SCROLL.mp4"

echo.
echo [4] DONE! File saved to TikTok_Videos\DEEPDIVE_SCROLL.mp4
pause
