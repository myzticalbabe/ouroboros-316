@echo off
title LING PER-LAYER SWEEP - DO NOT CLOSE THIS WINDOW
REM Overnight hyper-mutation map: builds + serves + evals one ablation per
REM Ling block on :8091, ledgering every row. ~12 min per layer.
REM Progress prints live here. Window stays open on finish (pause).
REM Usage: RUN_LING_SWEEP.bat [--layers 0-5] [--force]
"C:\Users\clint\AppData\Local\Programs\Python\Python314\python3.14t.exe" -u "C:\Users\clint\edge0-intel\scripts\sweep_ling_layers.py" %*
echo.
echo EXIT=%ERRORLEVEL%
echo.
pause
