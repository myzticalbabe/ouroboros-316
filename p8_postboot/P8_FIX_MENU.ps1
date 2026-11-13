#Requires -Version 5.1
<#
.SYNOPSIS
  Write the v5 P8 boot menu onto the EFI System Partition and prove it landed.

.DESCRIPTION
  Replaces \EFI\ubuntu\grub.cfg with p8_postboot\grub_menu_v5.cfg, after
  backing up whatever is there. Verifies by hashing the file back off the
  ESP and by re-parsing the bytes it read: the root UUID, the menuentry
  count, and the absence of a top-level `configfile` (the statement that
  replaced the menu in every earlier version).

  Exits 0 written and verified, 1 verification failed, 2 could not run,
  3 the UAC prompt was declined.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File C:\Users\clint\p8_postboot\P8_FIX_MENU.ps1
#>
param([switch]$Elevated)

$ErrorActionPreference = 'Stop'
$ScriptPath = $MyInvocation.MyCommand.Path
$Here       = Split-Path -Parent $ScriptPath
$StubPath   = Join-Path $Here 'grub_menu_v5.cfg'
$LogPath    = Join-Path $Here 'P8_FIX_MENU.log'
$EspVol     = '\\?\Volume{80ce903d-fccd-4004-8f95-f4eb447e5465}\'
$StubRel    = 'EFI\ubuntu\grub.cfg'
$Mount      = 'S:'

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
    if (-not (Test-Path -LiteralPath $StubPath)) {
        Log "FATAL: source stub missing: $StubPath"
        exit 2
    }
    $expectedSha = (Get-FileHash -LiteralPath $StubPath -Algorithm SHA256).Hash.ToLower()
    $stubText = [System.IO.File]::ReadAllText($StubPath)
    # GRUB parses LF. A git checkout can rewrite this file with CRLF, and the ESP
    # must not receive it that way, so normalise before hashing and writing.
    $stubText = $stubText -replace "`r`n", "`n"
    Log ("source {0} bytes sha256={1}" -f $stubText.Length, $expectedSha)

    if (-not (Test-Path -LiteralPath $EspVol)) {
        Log "FATAL: ESP volume not present: $EspVol (the disk layout changed)"
        exit 2
    }

    # Clear a mount leaked by an earlier run before taking the letter.
    try { mountvol $Mount /D 2>$null | Out-Null } catch { }
    if (Get-PSDrive -Name $Mount.TrimEnd(':') -ErrorAction SilentlyContinue) {
        Log "FATAL: $Mount is already in use - a previous run left it mounted (mountvol $Mount /D)"
        exit 2
    }
    mountvol $Mount $EspVol | Out-Null
    $mounted = $true

    $live = Join-Path "$Mount\" $StubRel
    if (-not (Test-Path -LiteralPath $live)) {
        Log "FATAL: $Mount\$StubRel not found - wrong ESP or Ubuntu was reinstalled"
        exit 2
    }

    $before = (Get-FileHash -LiteralPath $live -Algorithm SHA256).Hash.ToLower()
    $backup = "$live.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item -LiteralPath $live -Destination $backup -Force
    if (-not (Test-Path -LiteralPath $backup)) {
        Log "FATAL: backup was not written: $backup"
        exit 2
    }
    Log ("backup {0} sha256={1}" -f $backup, $before)

    [System.IO.File]::WriteAllText($live, $stubText, [System.Text.Encoding]::ASCII)

    # Prove it landed by reading the bytes back off the ESP, not by trusting the write.
    $actualSha = (Get-FileHash -LiteralPath $live -Algorithm SHA256).Hash.ToLower()
    $readBack = [System.IO.File]::ReadAllText($live)

    $errors = @()
    if ($actualSha -ne $expectedSha) {
        $errors += "sha256 mismatch: wrote $expectedSha, read $actualSha"
    }
    if (-not $readBack.Contains('58e46179-d777-4203-a807-8794a3fb2351')) {
        $errors += 'root UUID 58e46179-... is not in the file read back'
    }
    $entries = [regex]::Matches($readBack, '(?m)^menuentry')
    if ($entries.Count -lt 4) {
        $errors += "only $($entries.Count) menuentry lines read back"
    }

    # Order invariant: no configfile may run before the menu is defined.
    $depth = 0; $inEntry = $false; $topLevelConfigfile = @()
    $n = 0
    foreach ($line in ($readBack -split "`r?`n")) {
        $n++
        $code = ($line -split '#', 2)[0]
        if ($code -match '^\s*menuentry\b') { $inEntry = $true }
        if (-not $inEntry -and $code -match '(^|\s)configfile(\s|$)') { $topLevelConfigfile += $n }
        $depth += ([regex]::Matches($code, '\{')).Count - ([regex]::Matches($code, '\}')).Count
        if ($inEntry -and $depth -le 0) { $inEntry = $false; $depth = 0 }
    }
    if ($topLevelConfigfile.Count -gt 0) {
        $errors += "top-level configfile still present at line(s) $($topLevelConfigfile -join ',')"
    }

    $titles = [regex]::Matches($readBack, "(?m)^menuentry '([^']*)'") | ForEach-Object { $_.Groups[1].Value }
    Log ('menu the firmware will show:')
    foreach ($t in $titles) { Log ("  {0}" -f $t) }

    if ($errors.Count -gt 0) {
        Log ('FAIL: ' + ($errors -join ' | '))
        exit 1
    }
    Log ("PASS wrote {0} ({1} bytes, sha256={2}), {3} entries, no top-level configfile" -f `
        $live, $readBack.Length, $actualSha, $entries.Count)
    exit 0
}
catch {
    Log ('FATAL: ' + $_.Exception.Message)
    exit 2
}
finally {
    if ($mounted) { try { mountvol $Mount /D | Out-Null } catch { } }
}
