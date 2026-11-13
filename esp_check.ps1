<#
esp_check.ps1 - validate the live ESP GRUB stub whenever it changes.

The ESP is not mounted by default, so this mounts partition 1 (the 260 MB
EFI System Partition), validates U:\EFI\ubuntu\grub.cfg through esp_validate.py,
and unmounts again. esp_validate.py remembers the hash it last approved, so a
repeat run over identical bytes prints UNCHANGED and does nothing.

Exit codes, passed through from the validator:
  0  unchanged, or changed and valid
  1  changed and INVALID -- the ESP holds a stub that will misboot
  2  could not check (no ESP, no stub, no python, no validator)

.WHY ADMIN
Mounting the ESP needs elevation. Without it the mount silently fails and the
check would report "no stub" -- a fake failure. So it stops instead.

.EXAMPLES
  powershell -ExecutionPolicy Bypass -File esp_check.ps1
  powershell -ExecutionPolicy Bypass -File esp_check.ps1 -Force
  powershell -ExecutionPolicy Bypass -File esp_check.ps1 -Watch 300
#>
param(
    [switch]$Force,
    [int]$Watch = 0
)

$ErrorActionPreference = 'Stop'

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Output 'ERROR: mount the ESP requires elevation. Re-run from an elevated shell.'
    exit 2
}

$here = $PSScriptRoot
$validator = Join-Path $here 'esp_validate.py'
if (-not (Test-Path $validator)) {
    Write-Output "ERROR: esp_validate.py not found next to this script: $validator"
    exit 2
}

$python = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $python) {
    Write-Output 'ERROR: python not on PATH'
    exit 2
}

$partition = 1
$mount = 'U:'
$stub = 'U:\EFI\ubuntu\grub.cfg'
$state = Join-Path $here '.esp_state.json'

function Mount-Esp {
    try {
        Get-Partition -DiskNumber 0 -PartitionNumber $partition | Set-Partition -NewDriveLetter ($mount.TrimEnd(':')) -ErrorAction Stop
    } catch {
        Write-Output "ERROR: cannot assign $mount to disk 0 partition $partition : $_"
        return $false
    }
    Start-Sleep -Milliseconds 700
    if (-not (Test-Path 'U:\EFI')) {
        Write-Output "ERROR: $mount mounted but has no EFI directory -- not the ESP"
        return $false
    }
    return $true
}

function Dismount-Esp {
    try {
        Get-Partition -DiskNumber 0 -PartitionNumber $partition |
            Remove-PartitionAccessPath -AccessPath 'U:\' -ErrorAction Stop
    } catch {
        Write-Output "WARN: could not release $mount : $_"
    }
}

if (-not (Mount-Esp)) { exit 2 }

$exitCode = 2
try {
    if ($Watch -gt 0) {
        Write-Output "watching $stub every ${Watch}s (Ctrl-C to stop)"
        while ($true) {
            $argv = @($validator, $stub, '--state', $state)
            if ($Force) { $argv += '--force'; $Force = $false }
            & $python.Source @argv
            $exitCode = $LASTEXITCODE
            Start-Sleep -Seconds $Watch
        }
    } else {
        $argv = @($validator, $stub, '--state', $state)
        if ($Force) { $argv += '--force' }
        & $python.Source @argv
        $exitCode = $LASTEXITCODE
    }
} finally {
    Dismount-Esp
}

Write-Output "esp_check exit=$exitCode"
exit $exitCode
