# ============================================================
# FIX ALL CORRUPTED/WRONG-ASPECT VIDEOS → 1920x1080 16:9
# ============================================================
# Uses blurred-background fill — preserves ALL content
# No cropping, no black bars, no missing information
# ============================================================

$VideosDir = "$env:USERPROFILE\Desktop\TikTok_Videos"
$FixedDir  = "$VideosDir\FIXED_16x9"
if (!(Test-Path $FixedDir)) { New-Item -ItemType Directory -Path $FixedDir -Force | Out-Null }

# Blurred-background filter: fills 1920x1080, content centered, no cropping
$filter = "split[original][copy];[copy]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=20:2[blurred];[original]scale=1920:1080:force_original_aspect_ratio=decrease[scaled];[blurred][scaled]overlay=(W-w)/2:(H-h)/2,setsar=1"

Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  FIXING ASPECT RATIOS → 1920x1080 16:9' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''

$fixed = 0
$skipped = 0
$failed = 0

# ── CATEGORY 1: 1440x900 originals (Parts 001-023, HQ variants) ──
$originals = @(
    'TikTok_Part_001.mp4', 'TikTok_Part_002.mp4', 'TikTok_Part_003.mp4', 'TikTok_Part_004.mp4',
    'TikTok_Part_006.mp4', 'TikTok_Part_007.mp4', 'TikTok_Part_008.mp4', 'TikTok_Part_009.mp4',
    'TikTok_Part_010.mp4', 'TikTok_Part_011.mp4', 'TikTok_Part_012.mp4', 'TikTok_Part_013.mp4',
    'TikTok_Part_014.mp4', 'TikTok_Part_015.mp4', 'TikTok_Part_016.mp4', 'TikTok_Part_017.mp4',
    'TikTok_Part_018.mp4', 'TikTok_Part_019.mp4', 'TikTok_Part_020.mp4', 'TikTok_Part_021.mp4',
    'TikTok_Part_022.mp4', 'TikTok_Part_023.mp4',
    'TikTok_Part_006_HQ.mp4', 'TikTok_Part_007_HQ.mp4', 'TikTok_Part_008_HQ.mp4'
)

foreach ($vid in $originals) {
    $in  = Join-Path $VideosDir $vid
    $out = Join-Path $FixedDir $vid
    if (!(Test-Path $in)) { $skipped++; continue }
    
    Write-Host "  Fixing: $vid" -ForegroundColor Yellow
    ffmpeg -y -i $in -vf $filter -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k -movflags +faststart $out 2>&1 | Select-Object -Last 3
    
    if ($LASTEXITCODE -eq 0 -and (Test-Path $out) -and (Get-Item $out).Length -gt 1000) {
        $fixed++
        Write-Host "    OK" -ForegroundColor Green
    } else {
        $failed++
        Write-Host "    FAILED" -ForegroundColor Red
    }
}

# ── CATEGORY 2: 1080x1080 square FIXED versions → re-fix to 16:9 ──
$squares = @(
    'TikTok_Part_001_FIXED.mp4', 'TikTok_Part_002_FIXED.mp4',
    'TikTok_Part_003_FIXED.mp4', 'TikTok_Part_004_FIXED.mp4'
)

foreach ($vid in $squares) {
    $in  = Join-Path $VideosDir $vid
    $out = Join-Path $FixedDir $vid
    if (!(Test-Path $in)) { $skipped++; continue }
    
    Write-Host "  Re-fixing square: $vid" -ForegroundColor Yellow
    ffmpeg -y -i $in -vf $filter -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k -movflags +faststart $out 2>&1 | Select-Object -Last 3
    
    if ($LASTEXITCODE -eq 0 -and (Test-Path $out) -and (Get-Item $out).Length -gt 1000) {
        $fixed++
        Write-Host "    OK" -ForegroundColor Green
    } else {
        $failed++
        Write-Host "    FAILED" -ForegroundColor Red
    }
}

# ── CATEGORY 3: Odd-resolution scroll captures (1080x900, 1100x900) ──
$scrolls = @(
    'DEEPDIVE_SCROLL.mp4', 'FUNDING_SCROLL.mp4',
    'LETTER_SCROLL.mp4', 'SCROLL_CAPTURE.mp4'
)

foreach ($vid in $scrolls) {
    $in  = Join-Path $VideosDir $vid
    $out = Join-Path $FixedDir $vid
    if (!(Test-Path $in)) { $skipped++; continue }
    
    Write-Host "  Fixing scroll: $vid" -ForegroundColor Yellow
    ffmpeg -y -i $in -vf $filter -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k -movflags +faststart $out 2>&1 | Select-Object -Last 3
    
    if ($LASTEXITCODE -eq 0 -and (Test-Path $out) -and (Get-Item $out).Length -gt 1000) {
        $fixed++
        Write-Host "    OK" -ForegroundColor Green
    } else {
        $failed++
        Write-Host "    FAILED" -ForegroundColor Red
    }
}

# ── CATEGORY 4: Corrupted Part_005 — recovery attempt ──
$corruptIn  = Join-Path $VideosDir 'TikTok_Part_005.mp4'
$corruptOut = Join-Path $FixedDir 'TikTok_Part_005_RECOVERED.mp4'

if (Test-Path $corruptIn) {
    Write-Host '  RECOVERING corrupted Part_005...' -ForegroundColor Magenta
    
    # Try rebuilding moov atom
    ffmpeg -y -i $corruptIn -c copy -movflags faststart $corruptOut 2>&1 | Select-Object -Last 3
    
    if ($LASTEXITCODE -ne 0) {
        # Try re-encoding with genpts to rebuild timestamps
        Write-Host '    Faststart failed, trying re-encode...' -ForegroundColor Yellow
        ffmpeg -y -fflags +genpts -i $corruptIn -vf $filter -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k -movflags +faststart $corruptOut 2>&1 | Select-Object -Last 3
    }
    
    if ($LASTEXITCODE -eq 0 -and (Test-Path $corruptOut) -and (Get-Item $corruptOut).Length -gt 1000) {
        $fixed++
        Write-Host '    RECOVERED!' -ForegroundColor Green
    } else {
        $failed++
        Write-Host '    UNRECOVERABLE' -ForegroundColor Red
    }
}

# ── CLEANUP: Delete the 48-byte trash file ──
$trash = Join-Path $VideosDir '_TEST.mp4'
if ((Test-Path $trash) -and (Get-Item $trash).Length -lt 100) {
    Remove-Item $trash -Force
    Write-Host '  Deleted trash file: _TEST.mp4' -ForegroundColor Gray
}

# ── SUMMARY ──
Write-Host ''
Write-Host '========================================' -ForegroundColor Cyan
Write-Host "  DONE: $fixed fixed, $skipped skipped, $failed failed" -ForegroundColor Cyan
Write-Host "  Output: $FixedDir" -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Cyan
