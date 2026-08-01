<# 
  RECORD_SCROLL.ps1 — Open SCROLL_RECORD.html in Chrome and capture as MP4
  Usage: powershell -File RECORD_SCROLL.ps1
#>
param(
  [int]$Duration = 310,  # 300s scroll + 10s buffer
  [string]$OutputName = "SCROLL_CAPTURE.mp4"
)

$ErrorActionPreference = "Stop"
$HtmlPath = Resolve-Path "SCROLL_RECORD.html"
$OutputPath = "$env:USERPROFILE\Desktop\TikTok_Videos\$OutputName"
$HtmlUrl = "file:///$($HtmlPath -replace '\\','/' -replace ' ','%20')"

Write-Host "=========================================="
Write-Host "  SCROLL RECORDER"
Write-Host "=========================================="
Write-Host "HTML:   $HtmlPath"
Write-Host "Output: $OutputPath"
Write-Host "Duration: $Duration seconds"
Write-Host ""

# Step 1: Close any existing Chrome windows showing our scroll page
Write-Host "[1/4] Opening Chrome..."
Start-Process "chrome" -ArgumentList `
  "--new-window",
  "--window-size=1100,900",
  "--window-position=0,0",
  "--disable-extensions",
  "--disable-sync",
  $HtmlUrl

# Step 2: Wait for countdown (3s) + buffer (2s)
Write-Host "[2/4] Waiting for 3-2-1 countdown..."
Start-Sleep -Seconds 5

# Step 3: Start ffmpeg capture
Write-Host "[3/4] Recording $Duration seconds..."
$ffmpegArgs = @(
  "-f", "gdigrab",
  "-framerate", "30",
  "-offset_x", "0",
  "-offset_y", "0",
  "-video_size", "1100x900",
  "-i", "desktop",
  "-c:v", "libx264",
  "-preset", "veryfast",
  "-crf", "18",
  "-pix_fmt", "yuv420p",
  "-g", "60",
  "-an",
  "-t", "$Duration",
  "-y",
  $OutputPath
)

& ffmpeg @ffmpegArgs 2>&1 | ForEach-Object {
  if ($_ -match "time=") { Write-Host "`r  $_".Substring(0, [Math]::Min($_.Length, 80)) -NoNewline }
}

Write-Host ""

# Step 4: Verify output
if (Test-Path $OutputPath) {
  $size = "{0:N0} MB" -f ((Get-Item $OutputPath).Length / 1MB)
  Write-Host "[4/4] ✅ DONE: $OutputPath ($size)"
  Write-Host ""
  Write-Host "Opening file..."
  Start-Process $OutputPath
} else {
  Write-Host "[4/4] ❌ ERROR: Output file not created!"
  Write-Host "Path: $OutputPath"
}
