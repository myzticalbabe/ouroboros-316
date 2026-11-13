#Requires -Version 5.1
<#
.SYNOPSIS
  Read-only probe of the MELLI first-boot artifacts. Makes zero writes.
  Exits 0 all present, 1 something missing/mismatched, 2 could not run,
  3 UAC declined.
#>
param([switch]$Elevated)

$ErrorActionPreference = 'Stop'
$ScriptPath = $MyInvocation.MyCommand.Path
$Here       = Split-Path -Parent $ScriptPath
$LogPath    = Join-Path $Here 'probe_melli.log'
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
    if ($Elevated) { Log 'FATAL: relaunched elevated but still not administrator'; exit 2 }
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
    $fail = 0

    # 1. P4 identity (no admin needed, but record it here next to the rest)
    $p4 = Get-Partition -DiskNumber 0 -PartitionNumber 4
    Log ("P4 size={0} offset={1} guid={2} type={3}" -f $p4.Size, $p4.Offset, $p4.Guid, $p4.GptType)
    if ($p4.Size -ne 205874266112) { Log 'FAIL: P4 size drifted from 205874266112'; $fail = 1 }
    if (("$($p4.Guid)").Trim('{','}') -ne 'e4ff9384-c2c7-4605-bbe4-361d20f099fe') { Log 'FAIL: P4 PARTUUID drifted'; $fail = 1 }

    # 2. BCD MELLI entry: ABSENT is the correct state (2026-11-13). The old
    # {b7173bfb} entry was type 'Real-mode Boot Sector' pointing at a .efi
    # binary, which can never boot; the MELLI path is firmware -> shim ->
    # GRUB -> chainload, never Windows Boot Manager -> BCD.
    try {
        $bcd = bcdedit /enum '{b7173bfb-dbd1-11f0-8e4f-aa2261939d2d}' 2>&1 | Out-String
        Log ("BCD {b7173bfb}: " + (($bcd -split "`r?`n") -join ' | '))
        if ($bcd -match 'MELLI-OS') { Log 'FAIL: stale bootsector BCD entry is back - delete it, boot path is GRUB'; $fail = 1 }
    } catch { Log ('FAIL: bcdedit could not read {b7173bfb}: ' + $_.Exception.Message); $fail = 1 }

    # 3. ESP contents, read-only (mount, hash, unmount - no writes)
    try { mountvol $Mount /D 2>$null | Out-Null } catch { }
    mountvol $Mount $EspVol | Out-Null
    $mounted = $true
    $vmlinuz = Join-Path "$Mount\" 'EFI\MELLI\vmlinuz.efi'
    $stub = Join-Path "$Mount\" 'EFI\ubuntu\grub.cfg'
    $bm = Join-Path "$Mount\" 'EFI\Microsoft\Boot\bootmgfw.efi'
    foreach ($f in @($vmlinuz, $stub, $bm)) {
        if (Test-Path -LiteralPath $f) {
            $h = (Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash.ToLower()
            $s = (Get-Item -LiteralPath $f).Length
            Log ("ESP {0} bytes={1} sha256={2}" -f $f.Replace("$Mount\", ''), $s, $h)
        } else {
            Log ("FAIL: missing on ESP: {0}" -f $f)
            $fail = 1
        }
    }
    if ((Test-Path -LiteralPath $vmlinuz) -and ((Get-Item -LiteralPath $vmlinuz).Length -ne 14840832)) {
        Log 'FAIL: vmlinuz.efi size drifted from 14840832 (VMD kernel 2026-11-13)'; $fail = 1
    }

    if ($fail -eq 0) { Log 'PROBE-PASS: P4 + BCD + ESP all present, sizes match install-time record' }
    exit $fail
}
catch {
    Log ('FATAL: ' + $_.Exception.Message)
    exit 2
}
finally {
    if ($mounted) { try { mountvol $Mount /D | Out-Null } catch { } }
}
