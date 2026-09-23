@echo off
title GEMMA SURGERY - DO NOT CLOSE THIS WINDOW
REM STRATUM Gemma surgery — double-click to run. Output stays visible here.
REM 3.14t free-threaded + 16 workers. Done when you see: edited=84
del "C:\Users\clint\edge0-intel\models\gemma-4-e4b-abl-s10.gguf" 2>nul
"C:\Users\clint\AppData\Local\Programs\Python\Python314\python3.14t.exe" -u "C:\Users\clint\edge0-intel\scripts\gguf_abliterate.py" --src "C:\Users\clint\.lmstudio\models\lmstudio-community\gemma-4-E4B-it-GGUF\gemma-4-E4B-it-Q4_K_M.gguf" --dst "C:\Users\clint\edge0-intel\models\gemma-4-e4b-abl-s10.gguf" --dir "C:\Users\clint\edge0-intel\models\gemma-4-e4b-abliterated\refusal_dir.npy" --strength 1.0 --targets attn_output.weight,ffn_down.weight
echo.
echo EXIT=%ERRORLEVEL%
echo.
pause
