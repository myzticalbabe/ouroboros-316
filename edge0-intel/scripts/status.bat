@echo off
echo ============ OXFORD SHARDFOUNDRY STATUS ============
echo --- RAM/DISK ---
powershell -NoProfile -Command "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB; Get-PSDrive C | Select-Object -ExpandProperty Free"
echo --- PYTHON (top by RAM) ---
powershell -NoProfile -Command "Get-Process | Where-Object { $_.Name -match '^python' } | Sort-Object WorkingSet64 -Descending | Select-Object -First 4 Id, @{N='MB';E={[math]::Round($_.WorkingSet64/1MB,0)}}, StartTime | Format-Table -AutoSize | Out-String"
echo --- SERVERS ---
powershell -NoProfile -Command "foreach ($p in 8089,8090,8091,8092) { try { Invoke-RestMethod -Uri \"http://127.0.0.1:$p/health\" -TimeoutSec 3 | Out-Null; echo \"${p}: UP\" } catch { echo \"${p}: DOWN\" } }"
echo --- SWEEP ---
powershell -NoProfile -Command "Get-Content 'C:\Users\clint\edge0-intel\sweep_status.json' -ErrorAction SilentlyContinue | Select-Object -Last 12"
echo --- CANARY ---
powershell -NoProfile -Command "Get-Content 'C:\Users\clint\edge0-intel\canary.log' -ErrorAction SilentlyContinue | Select-Object -Last 1"
echo --- TASKS ---
schtasks /query | findstr "edge-"
echo --- LOGS (tail) ---
powershell -NoProfile -Command "foreach ($f in 'collect_gemma.log','tryfp16.log','evalfull.log','dequant.log','ablate.log','dlgemma.log') { $p=\"C:\Users\clint\edge0-intel\$f\"; if (Test-Path $p) { echo \"-- $f\"; Get-Content $p | Select-Object -Last 2 } }"
echo --- LEDGER (last) ---
powershell -NoProfile -Command "Get-Content 'C:\Users\clint\edge0-intel\evolve_log.jsonl' -ErrorAction SilentlyContinue | Select-Object -Last 1"
echo ============ END ============
