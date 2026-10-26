# RECORD_BOTH_30S.ps1 - working screen-recorder protocol (verified 2026-10-26).
#
# Problem it solves: gdigrab captures only what is on screen. Kilo's window
# kept missing from clips because it was minimized/behind. This script finds
# BOTH agent windows by title, snaps them side-by-side, verifies with a
# screenshot, then records 2x30s clips at proper MP4 spec.
#
# Spec (do not weaken): H.264, preset medium, CRF 23, yuv420p, 30fps.
# Full virtual-primary screen scaled to 1920x1200 so both halves stay legible.
# Usage: powershell -ExecutionPolicy Bypass -File RECORD_BOTH_30S.ps1
#    or: RECORD_BOTH_30S.bat

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

Add-Type @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public class WR {
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc p, IntPtr l);
  public delegate bool EnumWindowsProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr o, int x, int y, int cx, int cy, uint f);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
}
'@

function Find-Window($substr) {
  Get-Process | Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like "*$substr*" } |
    Select-Object @{N='H';E={$_.MainWindowHandle}}, @{N='T';E={$_.MainWindowTitle}}
}

$free = Find-Window 'Freebuff' | Select-Object -First 1
$kilo = Find-Window 'Kilo' | Select-Object -First 1
if (-not $free) { throw 'FreeBuff window not found (title must contain "Freebuff")' }
if (-not $kilo) { throw 'Kilo window not found (title must contain "Kilo")' }
Write-Host ("FreeBuff: {0} [{1}]" -f $free.H, $free.T)
Write-Host ("Kilo:     {0} [{1}]" -f $kilo.H, $kilo.T)

$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$hw = [int]($b.Width / 2)
Write-Host ("Screen: {0}x{1}, halves {2}px" -f $b.Width, $b.Height, $hw)

# Restore (9) in case minimized, then snap: FreeBuff left, Kilo right
[void][WR]::ShowWindow($free.H, 9)
[void][WR]::ShowWindow($kilo.H, 9)
Start-Sleep -Milliseconds 400
[void][WR]::SetWindowPos($free.H, [IntPtr]::Zero, 0, 0, $hw, $b.Height, 0x0040)
[void][WR]::SetWindowPos($kilo.H, [IntPtr]::Zero, $hw, 0, $hw, $b.Height, 0x0040)
Start-Sleep -Milliseconds 800

$outDir = Join-Path ([Environment]::GetFolderPath('Desktop')) 'HTML_MP4'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# Verify arrangement with one screenshot before burning 60s of video
$check = Join-Path $outDir 'arrange_check.png'
& ffmpeg -y -v error -f gdigrab -framerate 1 -i desktop -frames:v 1 `
  -vf 'scale=1440:900' $check
Write-Host "Arrangement check: $check - inspect before clips run."

for ($i = 1; $i -le 2; $i++) {
  $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
  $out = Join-Path $outDir ("LIVE_30s_{0}_both_p{1}.mp4" -f $ts, $i)
  Write-Host ("Clip {0}/2 -> {1}" -f $i, $out)
  & ffmpeg -y -f gdigrab -framerate 30 -i desktop `
    -vf 'scale=1920:1200' -c:v libx264 -preset medium -crf 23 `
    -pix_fmt yuv420p -r 30 -an -t 30 $out
  & ffprobe -v error -show_entries format=duration `
    -of default=noprint_wrappers=1 $out
}
Write-Host 'Done - 2 clips in HTML_MP4.'
