param(
    [Parameter(Mandatory=$true)]
    [string]$HtmlName
)

$HtmlFile = "C:\Users\clint\$HtmlName"
$BaseName = [System.IO.Path]::GetFileNameWithoutExtension($HtmlName)
$OutputFolder = "$env:USERPROFILE\Desktop\TikTok_Videos"
$OutputFile = "$OutputFolder\$($BaseName)_SCROLL.mp4"

if (-not (Test-Path $OutputFolder)) { 
    New-Item -ItemType Directory -Path $OutputFolder -Force | Out-Null 
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SCROLLING MP4 CAPTURE - 1440x900" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Source: $HtmlFile"
Write-Host "Output: $OutputFile"
Write-Host ""

Write-Host "[1/3] Opening Chrome (1440x900)..." -ForegroundColor Yellow
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chromePath)) {
    $chromePath = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
}
$fileUrl = "file:///$($HtmlFile -replace '\\','/')"
Start-Process -FilePath $chromePath -ArgumentList "--start-fullscreen","--window-size=1920,1080","--window-position=0,0","--disable-infobars","$fileUrl"

Write-Host "[2/3] Waiting for page to load (8s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

Write-Host "[3/3] Recording... 4 min" -ForegroundColor Green
Write-Host "  DO NOT MOVE MOUSE OVER WINDOW" -ForegroundColor Red

$ffmpegArgs = @(
    "-f", "gdigrab",
    "-framerate", "30",
    "-video_size", "1920x1080",
    "-offset_x", "0",
    "-offset_y", "0",
    "-i", "desktop",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-g", "60",
    "-an",
    "-t", "240",
    "-y", $OutputFile
)

& ffmpeg $ffmpegArgs 2>&1 | Select-Object -Last 3

if (Test-Path $OutputFile) {
    $size = "{0:N0} MB" -f ((Get-Item $OutputFile).Length / 1MB)
    Write-Host ""
    Write-Host "DONE: $OutputFile" -ForegroundColor Green
    Write-Host "Size: $size" -ForegroundColor Green
    Start-Process $OutputFile
} else {
    Write-Host "FAILED" -ForegroundColor Red
}
