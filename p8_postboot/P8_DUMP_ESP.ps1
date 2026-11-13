#Requires -Version 5.1
<#
.SYNOPSIS
  Copy the ESP's EFI\ubuntu payload to disk so the GRUB binary can be measured.

.DESCRIPTION
  Read-only. Mounts the ESP, copies grubx64.efi / shimx64.efi / grub.cfg and a
  directory listing into p8_postboot\esp_dump, then unmounts. Answers one
  question with bytes instead of documentation: does this grubx64.efi carry
  /EFI/ubuntu as its prefix (so it reads EFI\ubuntu\grub.cfg), or /boot/grub
  (so the ESP stub is never read and every stub edit was a no-op).

  Exit 0 dumped, 2 could not run, 3 UAC declined.
#>
param([switch]$Elevated)

$ErrorActionPreference = 'Stop'
$ScriptPath = $MyInvocation.MyCommand.Path
$Here       = Split-Path -Parent $ScriptPath
$OutDir     = Join-Path $Here 'esp_dump'
$LogPath    = Join-Path $Here 'P8_DUMP_ESP.log'
$EspVol     = '\\?\Volume{80ce903d-fccd-4004-8f95-f4eb447e5465}\'
$Mount      = 'S:'

function Log([string]$Message) {
    $line = '{0} {1}' -f (Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'), $Message
    Add-Content -Path $LogPath -Value $line -Encoding UTF8
    Write-Host $line
}

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    if ($Elevated) { Log 'FATAL: still not administrator'; exit 2 }
    try {
        $child = Start-Process -FilePath 'powershell.exe' -Verb RunAs -Wait -PassThru -ArgumentList @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$ScriptPath`"", '-Elevated')
        exit $child.ExitCode
    } catch {
        Log ('UAC-DECLINED: ' + $_.Exception.Message)
        exit 3
    }
}

$mounted = $false
try {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
    try { mountvol $Mount /D 2>$null | Out-Null } catch { }
    if (Get-PSDrive -Name $Mount.TrimEnd(':') -ErrorAction SilentlyContinue) {
        Log "FATAL: $Mount already in use"; exit 2
    }
    mountvol $Mount $EspVol | Out-Null
    $mounted = $true

    $src = Join-Path "$Mount\" 'EFI\ubuntu'
    if (-not (Test-Path -LiteralPath $src)) { Log "FATAL: $src missing"; exit 2 }

    Get-ChildItem -LiteralPath $src -Force |
        Select-Object Name, Length, LastWriteTime |
        Format-Table -AutoSize |
        Out-String |
        Set-Content -Path (Join-Path $OutDir 'listing.txt') -Encoding UTF8

    foreach ($f in 'grubx64.efi', 'shimx64.efi', 'grub.cfg') {
        $from = Join-Path $src $f
        if (Test-Path -LiteralPath $from) {
            Copy-Item -LiteralPath $from -Destination (Join-Path $OutDir $f) -Force
            $sha = (Get-FileHash -LiteralPath (Join-Path $OutDir $f) -Algorithm SHA256).Hash.ToLower()
            Log ("copied {0} {1} bytes sha256={2}" -f $f, (Get-Item -LiteralPath $from -Force).Length, $sha)
        } else {
            Log "missing on ESP: $f"
        }
    }
    Log "PASS dump complete: $OutDir"
    exit 0
}
catch {
    Log ('FATAL: ' + $_.Exception.Message)
    exit 2
}
finally {
    if ($mounted) { try { mountvol $Mount /D | Out-Null } catch { } }
}
