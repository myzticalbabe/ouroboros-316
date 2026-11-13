#Requires -Version 5.1
<#
.SYNOPSIS
  Deploy the NVMe-enabled MELLI kernel to the ESP.

.DESCRIPTION
  Root cause (all measured 2026-11-13): Disk0 is an NVMe-only box (WD PC
  SN5000S) but the ESP kernel was built with `# CONFIG_BLK_DEV_NVME is not
  set`, so it VFS-panics on bare metal. The fixed kernel
  (vmlinuz-melli-7.0.14-nvme, built 2026-11-13, CONFIG_BLK_DEV_NVME=y) was
  proven in QEMU: NVMe enumerates, ext4 mounts, /sbin/init runs, rcS prints
  MELLI-OS 1.0 (hyper-edge).

  This script mounts the ESP (Disk0 P1, Volume 80ce903d-...), refuses to
  run if \\EFI\\MELLI\\vmlinuz.efi is absent (never creates new ESP paths),
  backs the live kernel up on the ESP with a timestamp, writes the new
  kernel, and proves it landed by hashing the bytes back off the ESP.
  Re-run prints UNCHANGED and exits 0.

  Exits 0 written/unchanged and verified, 1 verification failed,
  2 could not run, 3 the UAC prompt was declined.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File C:\Users\clint\deploy_melli_kernel.ps1
#>
param([switch]$Elevated)

$ErrorActionPreference = 'Stop'
$ScriptPath = $MyInvocation.MyCommand.Path
$Here       = Split-Path -Parent $ScriptPath
$LogPath    = Join-Path $Here 'deploy_melli_kernel.log'
$EspVol     = '\\?\Volume{80ce903d-fccd-4004-8f95-f4eb447e5465}\'
$KernelRel  = 'EFI\MELLI\vmlinuz.efi'
$Mount      = 'S:'
$Source     = 'C:\LinuxOffload\evac-2026-11-13\melli\vmlinuz-melli-7.0.14-nvme'
$ExpectedSha = '5d75b9a6adca0c15a192d0dda96bde94553ba934f5ee981ae1bcf25c25bc9e20'
$ExpectedSize = 14824448

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
        Log "FATAL: source kernel missing: $Source"
        exit 2
    }
    $sourceSha = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash.ToLower()
    if ($sourceSha -ne $ExpectedSha) {
        Log ("FATAL: source kernel sha mismatch: want {0}, have {1} - refusing to deploy" -f $ExpectedSha, $sourceSha)
        exit 2
    }
    Log ("source OK {0} bytes sha256={1}" -f (Get-Item -LiteralPath $Source).Length, $sourceSha)

    try { mountvol $Mount /D 2>$null | Out-Null } catch { }
    if (Get-PSDrive -Name $Mount.TrimEnd(':') -ErrorAction SilentlyContinue) {
        Log "FATAL: $Mount is already in use - a previous run left it mounted (mountvol $Mount /D)"
        exit 2
    }
    mountvol $Mount $EspVol | Out-Null
    $mounted = $true

    $live = Join-Path "$Mount\" $KernelRel
    if (-not (Test-Path -LiteralPath $live)) {
        Log "FATAL: $Mount\$KernelRel not found - wrong ESP or MELLI was removed (not creating new paths)"
        exit 2
    }

    $before = (Get-FileHash -LiteralPath $live -Algorithm SHA256).Hash.ToLower()
    if ($before -eq $ExpectedSha) {
        Log "UNCHANGED $live sha256=$before already the NVMe kernel"
        exit 0
    }
    Log ("live kernel before deploy: {0} bytes sha256={1}" -f (Get-Item -LiteralPath $live).Length, $before)

    $backup = "$live.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item -LiteralPath $live -Destination $backup -Force
    if (-not (Test-Path -LiteralPath $backup)) {
        Log "FATAL: backup was not written: $backup"
        exit 2
    }
    Log ("backup {0} sha256={1}" -f $backup, $before)

    Copy-Item -LiteralPath $Source -Destination $live -Force

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
    Log ("PASS wrote {0} ({1} bytes, sha256={2}); previous kernel kept at {3}" -f $live, $actualSize, $actualSha, $backup)
    exit 0
}
catch {
    Log ('FATAL: ' + $_.Exception.Message)
    exit 2
}
finally {
    if ($mounted) { try { mountvol $Mount /D | Out-Null } catch { } }
}
