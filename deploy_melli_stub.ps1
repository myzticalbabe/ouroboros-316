#Requires -Version 5.1
<#
.SYNOPSIS
  Deploy the MELLI-first GRUB stub to the ESP for the unattended first boot.

.DESCRIPTION
  The ESP stub (EFI\ubuntu\grub.cfg) currently boots Windows first
  (default=0). This deploys p8_postboot\grub_mellidefault.cfg, whose entries
  are byte-identical except default=1 (MELLI), so a reboot with no one at
  the keyboard boots MELLI-OS after the 10 s menu while Windows stays one
  arrow-key away.

  Same safety shape as deploy_melli_kernel.ps1: refuses to run if the live
  stub is absent, backs it up on the ESP with a timestamp, writes the new
  stub with LF endings (GRUB parses LF), and proves it landed by hashing
  the bytes back off the ESP. Re-run prints UNCHANGED and exits 0.
  After a confirmed MELLI boot, redeploy grub_winfirst.cfg to go
  Windows-first again.

  Exits 0 written/unchanged and verified, 1 verification failed,
  2 could not run, 3 the UAC prompt was declined.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File C:\Users\clint\deploy_melli_stub.ps1
#>
param([switch]$Elevated)

$ErrorActionPreference = 'Stop'
$ScriptPath = $MyInvocation.MyCommand.Path
$Here       = Split-Path -Parent $ScriptPath
$LogPath    = Join-Path $Here 'deploy_melli_stub.log'
$EspVol     = '\\?\Volume{80ce903d-fccd-4004-8f95-f4eb447e5465}\'
$StubRel    = 'EFI\ubuntu\grub.cfg'
$Mount      = 'S:'
$Source     = Join-Path $Here 'p8_postboot\grub_mellidefault.cfg'
$ExpectedSha = '7c0452d15d208076ba9196e8a0ea910542cb8f4c9b5b9c32d8f2a13f4d3b5f05'
$ExpectedSize = 1971

function Log([string]$Message) {
    $line = '{0} {1}' -f (Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'), $Message
    Add-Content -Path $LogPath -Value $line -Encoding UTF8
    Write-Host $line
}

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    if ($Elevated) {
        Log 'FATAL: relaunched elevated but still not administrator - cannot touch the ESP'
        exit 2
    }
    Log 'elevation required - asking Windows for one UAC prompt'
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
    if (-not (Test-Path -LiteralPath $Source)) {
        Log "FATAL: source stub missing: $Source"
        exit 2
    }
    $sourceText = [System.IO.File]::ReadAllText($Source) -replace "`r`n", "`n"
    $sourceBytes = [System.Text.Encoding]::ASCII.GetBytes($sourceText)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $sourceSha = ([BitConverter]::ToString($sha.ComputeHash($sourceBytes)) -replace '-', '').ToLower()
    if ($sourceSha -ne $ExpectedSha) {
        Log ("FATAL: source stub sha mismatch: want {0}, have {1} - refusing to deploy" -f $ExpectedSha, $sourceSha)
        exit 2
    }
    Log ("source OK {0} bytes sha256={1}" -f $sourceBytes.Length, $sourceSha)

    try { mountvol $Mount /D 2>$null | Out-Null } catch { }
    if (Get-PSDrive -Name $Mount.TrimEnd(':') -ErrorAction SilentlyContinue) {
        Log "FATAL: $Mount is already in use - a previous run left it mounted (mountvol $Mount /D)"
        exit 2
    }
    mountvol $Mount $EspVol | Out-Null
    $mounted = $true

    $live = Join-Path "$Mount\" $StubRel
    if (-not (Test-Path -LiteralPath $live)) {
        Log "FATAL: $Mount\$StubRel not found - wrong ESP or Ubuntu was reinstalled (not creating new paths)"
        exit 2
    }

    $before = (Get-FileHash -LiteralPath $live -Algorithm SHA256).Hash.ToLower()
    if ($before -eq $ExpectedSha) {
        Log "UNCHANGED $live sha256=$before already MELLI-first"
        exit 0
    }
    Log ("live stub before deploy: sha256={0}" -f $before)

    $backup = "$live.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item -LiteralPath $live -Destination $backup -Force
    if (-not (Test-Path -LiteralPath $backup)) {
        Log "FATAL: backup was not written: $backup"
        exit 2
    }
    Log ("backup {0} sha256={1}" -f $backup, $before)

    [System.IO.File]::WriteAllText($live, $sourceText, [System.Text.Encoding]::ASCII)

    # Prove it landed by reading the bytes back off the ESP.
    $actualSha = (Get-FileHash -LiteralPath $live -Algorithm SHA256).Hash.ToLower()
    $actualSize = (Get-Item -LiteralPath $live).Length

    $errors = @()
    if ($actualSha -ne $ExpectedSha) {
        $errors += "sha256 mismatch: wrote $ExpectedSha, read $actualSha"
    }
    if ($actualSize -ne $ExpectedSize) {
        $errors += "size mismatch: wrote $ExpectedSize, read $actualSize"
    }
    if ($errors.Count -gt 0) {
        Log ('FAIL: ' + ($errors -join ' | '))
        exit 1
    }
    Log ("PASS wrote {0} ({1} bytes, sha256={2}); previous stub kept at {3}" -f $live, $actualSize, $actualSha, $backup)
    exit 0
}
catch {
    Log ('FATAL: ' + $_.Exception.Message)
    exit 2
}
finally {
    if ($mounted) { try { mountvol $Mount /D | Out-Null } catch { } }
}
