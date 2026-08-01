$OutputFolder = "$env:USERPROFILE\Desktop\TikTok_Videos"
if (-not (Test-Path $OutputFolder)) { New-Item -ItemType Directory -Path $OutputFolder -Force | Out-Null }

Write-Host "RECORDING STARTED"
Write-Host "Output: $OutputFolder"
Write-Host "Press Ctrl+C to stop"
Write-Host ""

$seg = 6
while ($true) {
    $segStr = $seg.ToString("000")
    $outFile = "$OutputFolder\TikTok_Part_${segStr}.mp4"
    Write-Host "Segment $segStr starting..."
    
    & ffmpeg -f gdigrab -framerate 30 -video_size 1440x900 -i desktop -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -g 60 -an -t 300 -y $outFile 2>&1 | Select-Object -Last 1
    
    if (Test-Path $outFile) {
        $size = "{0:N0}MB" -f ((Get-Item $outFile).Length / 1MB)
        Write-Host "Segment $segStr done: $size"
    }
    $seg++
}
