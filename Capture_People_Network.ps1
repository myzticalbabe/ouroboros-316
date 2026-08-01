$OutputDir = "$env:USERPROFILE\Desktop\TikTok_Videos"
$OutputFile = "$OutputDir\PEOPLE_NETWORK_CARD.mp4"
$HtmlPath = 'C:\Users\clint\PEOPLE_NETWORK_SCROLL.html'

if (!(Test-Path $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null }

Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  PEOPLE NETWORK CARD - Scrolling MP4' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  Output:' $OutputFile -ForegroundColor Green
Write-Host '  Format: 1920x1080 16:9, H.264 30fps' -ForegroundColor Green
Write-Host ''

# Kill any existing Chrome
Get-Process chrome -ErrorAction SilentlyContinue | ForEach-Object { 
    try { $_.CloseMainWindow() } catch {}
}
Start-Sleep -Seconds 2

# Open Chrome in --app mode
Write-Host 'Opening Chrome in --app mode...' -ForegroundColor Yellow
$chromeArgs = @(
    '--app=file:///C:/Users/clint/PEOPLE_NETWORK_SCROLL.html',
    '--window-size=1920,1080',
    '--window-position=0,0'
)
Start-Process 'chrome' -ArgumentList $chromeArgs

# Wait for page load + 3s title pause
Write-Host 'Waiting 10 seconds for page load and title pause...' -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Capture with ffmpeg
Write-Host 'Starting ffmpeg capture - 90 seconds...' -ForegroundColor Green
Write-Host ''

ffmpeg -y -f gdigrab -framerate 30 -offset_x 0 -offset_y 0 -video_size 1920x1080 -draw_mouse 0 -i desktop -t 90 -c:v libx264 -preset ultrafast -crf 23 -pix_fmt yuv420p -movflags +faststart $OutputFile 2>&1

if ($LASTEXITCODE -eq 0 -and (Test-Path $OutputFile)) {
    $size = (Get-Item $OutputFile).Length / 1MB
    Write-Host ''
    Write-Host '========================================' -ForegroundColor Green
    Write-Host '  CAPTURE COMPLETE' -ForegroundColor Green
    Write-Host '  File:' $OutputFile -ForegroundColor Green
    Write-Host '  Size:' ([math]::Round($size, 1)) 'MB' -ForegroundColor Green
    Write-Host '========================================' -ForegroundColor Green
    Copy-Item $OutputFile 'C:\Users\clint\PEOPLE_NETWORK_CARD.mp4' -Force
} else {
    Write-Host 'Capture may have failed. Check output.' -ForegroundColor Red
}
