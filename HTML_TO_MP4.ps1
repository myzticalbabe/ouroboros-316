<# 
  HTML_TO_MP4.ps1 — Capture any HTML file as a smooth-scrolling MP4 video
  Usage: powershell -File HTML_TO_MP4.ps1 [input.html] [output.mp4] [seconds]
#>
param(
  [string]$InputFile = "COMPLAINT_TODO_LIST.html",
  [string]$OutputFile = "SCROLL_VIDEO.mp4",
  [int]$Duration = 300
)

$InputPath = Resolve-Path $InputFile
$OutputPath = "$env:USERPROFILE\Desktop\TikTok_Videos\$OutputFile"

Write-Host "=== HTML TO SCROLLING MP4 ==="
Write-Host "Input:  $InputPath"
Write-Host "Output: $OutputPath"
Write-Host "Duration: $Duration seconds"

# Step 1: Open Chrome with the HTML file
Write-Host "Opening Chrome..."
$chromeUrl = "file:///$($InputPath -replace '\\','/')"
Start-Process "chrome" -ArgumentList "--new-window", "--window-size=1080,1920", "--window-position=0,0", $chromeUrl

Start-Sleep -Seconds 3
Write-Host "Chrome opened. Starting capture in 3 seconds..."
Start-Sleep -Seconds 3

# Step 2: Capture with ffmpeg
Write-Host "Recording..."
ffmpeg -f gdigrab -framerate 30 -offset_x 0 -offset_y 0 -video_size 1080x1920 -i desktop -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -t $Duration -y $OutputPath 2>&1 | Select-Object -Last 3

if (Test-Path $OutputPath) {
  $size = "{0:N0}MB" -f ((Get-Item $OutputPath).Length / 1MB)
  Write-Host "Done: $OutputPath ($size)"
} else {
  Write-Host "ERROR: Output file not created"
}
