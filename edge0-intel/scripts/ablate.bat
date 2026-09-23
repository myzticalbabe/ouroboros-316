@echo off
"C:\Users\clint\AppData\Local\Programs\Python\Python314\python.exe" "C:\Users\clint\edge0-intel\scripts\apply_abliteration.py" --dir "C:\Users\clint\edge0-intel\models\edge0-8b-fp16\refusal_dir.npy" --strength %1 --out "C:\Users\clint\edge0-intel\models\edge0-8b-abl-s%1" >> "C:\Users\clint\edge0-intel\ablate.log" 2>&1
