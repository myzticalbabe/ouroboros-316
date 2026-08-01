$InputFolder = "$env:USERPROFILE\Desktop\TikTok_Videos"
$OutputFolder = "$env:USERPROFILE\Desktop\TikTok_Videos"
$files = Get-ChildItem $InputFolder -Filter "TikTok_Part_*.mp4" | Where-Object { $_.Name -notmatch "_FIXED" }

Write-Host "Converting $($files.Count) files to TikTok Square (1080x1080)..."
Write-Host ""

foreach ($f in $files) {
    $outName = $f.BaseName + "_FIXED.mp4"
    $outPath = "$OutputFolder\$outName"
    
    Write-Host "Processing: $($f.Name) -> $outName"
    
    ffmpeg -i "$($f.FullName)" `
        -vf "crop=ih:ih:(iw-ih)/2:0,scale=1080:1080,setsar=1" `
        -c:v libx264 -preset ultrafast -crf 28 -c:a aac -b:a 128k `
        -y "$outPath" 2>&1 | Select-Object -Last 2
    
    if ($LASTEXITCODE -eq 0) {
        $size = "{0:N0}MB" -f ((Get-Item $outPath).Length / 1MB)
        Write-Host "  Done: $size"
    } else {
        Write-Host "  ERROR converting $($f.Name)"
    }
}

Write-Host ""
Write-Host "All done. FIXED files in: $OutputFolder"
