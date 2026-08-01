# ============================================================
# 5-MINUTE RECORDING TIMER — Xbox Game Bar Companion
# ============================================================
# Usage: Right-click → Run with PowerShell
# Starts a 5-minute countdown. Press Ctrl+C to stop early.

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$totalSeconds = 300  # 5 minutes = 300 seconds
$redColor = [System.Drawing.Color]::FromArgb(255, 40, 40, 40)

# Countdown loop with console output and beeps
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  5-MINUTE RECORDING TIMER STARTED" -ForegroundColor Yellow
Write-Host "  Press Win+Alt+R to START recording NOW!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

for ($i = $totalSeconds; $i -ge 0; $i--) {
    $minutes = [math]::Floor($i / 60)
    $seconds = $i % 60
    $timeStr = "{0:D2}:{1:D2}" -f $minutes, $seconds
    
    # Color based on time remaining
    if ($i -le 30) {
        Write-Host "`r  ⏰ TIME: $timeStr — STOP RECORDING! Press Win+Alt+R" -NoNewline -ForegroundColor Red
        if ($i % 5 -eq 0) { [System.Console]::Beep(1000, 200) }
    } elseif ($i -le 60) {
        Write-Host "`r  ⏰ TIME: $timeStr — Almost done..." -NoNewline -ForegroundColor Yellow
        if ($i % 10 -eq 0) { [System.Console]::Beep(800, 100) }
    } else {
        Write-Host "`r  ⏰ TIME: $timeStr" -NoNewline -ForegroundColor Green
    }
    
    Start-Sleep -Seconds 1
}

# Final alert
for ($j = 0; $j -lt 3; $j++) {
    [System.Console]::Beep(1200, 300)
    Start-Sleep -Milliseconds 200
}

Write-Host "`n`n========================================" -ForegroundColor Red
Write-Host "  5 MINUTES COMPLETE — STOP RECORDING NOW!" -ForegroundColor Red
Write-Host "  Press Win+Alt+R to stop" -ForegroundColor Red
Write-Host "========================================`n" -ForegroundColor Red

# Show popup reminder
[System.Windows.Forms.MessageBox]::Show(
    "5 MINUTES COMPLETE!`n`nPress Win+Alt+R to stop recording.`n`nFile saved to: Videos\Captures\",
    "Recording Timer",
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Exclamation
)

Write-Host "Ready for next segment. Run this script again for another 5 minutes." -ForegroundColor Cyan
Read-Host "Press Enter to close"
