@echo off
setlocal
cd /d "%~dp0\.."

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "windows-app\main.py"
) else (
    py "windows-app\main.py"
)

