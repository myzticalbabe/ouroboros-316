#Requires -Version 5.1
<#
.SYNOPSIS
  Deploy the VMD-enabled MELLI kernel to the ESP.

.DESCRIPTION
  Root cause (all measured 2026-11-13): the box is Intel RST/VMD
  (VMD Controller 7D0B + Managed 09AB, NVMe WD SN5000S behind it) but the
  live ESP kernel (vmlinuz-melli-7.0.14-nvme, sha 5d75b9a6...) was built with
  `# CONFIG_VMD is not set`, so on bare metal the kernel sees no block
  device and cannot mount root=PARTUUID=e4ff9384-... (QEMU has no VMD, so
  QEMU boots fine - the exact green-QEMU / dead-box split observed).
  This kernel adds CONFIG_VMD=y only (PCI/NVMe/EFI_STUB/EXT4/CMDLINE
  unchanged, verified in .config and in the binary's builtin cmdline).

  Same safety shape as deploy_melli_kernel.ps1: refuses to run if
  \EFI\MELLI\vmlinuz.efi is absent, backs the live kernel up on the ESP
  with a timestamp, writes the new kernel, and proves it landed by hashing
  the bytes back off the ESP. Re-run prints UNCHANGED and exits 0.

  Exits 0 written/unchanged and verified, 1 verification failed,
  2 could not run, 3 the UAC prompt was declined.
#>
param([switch]$Elevated)

$ErrorActionPreference = 'Stop'
$ScriptPath = $MyInvocation.MyCommand.Path
$Here       = Split-Path -Parent $ScriptPath
$LogPath    = Join-Path $Here 'deploy_melli_vmd.log'
$EspVol     = '\\?\Volume{80ce903d-fccd-4004-8f95-f4eb447e5465}\'
$KernelRel  = 'EFI\MELLI\vmlinuz.efi'
$Mount      = 'S:'
$Source     = 'C:\LinuxOffload\evac-2026-11-13\melli\vmlinuz-melli-7.0.14-vmd'
$ExpectedSha = 'd137a2f30d358f1215be17014df6794ba750950402b42e8c7e5385ce7fd973d3'
$ExpectedSize = 14840832

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
        Log "UNCHANGED $live sha256=$before already the VMD kernel"
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
