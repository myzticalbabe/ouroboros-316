@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
cl /nologo /I "C:\Users\clint\AppData\Local\Programs\Python\Python314\include" ouroboros_host.c /link /LIBPATH:"C:\Users\clint\AppData\Local\Programs\Python\Python314\libs" python314.lib /OUT:ouroboros_host.exe
echo EXIT=%ERRORLEVEL%