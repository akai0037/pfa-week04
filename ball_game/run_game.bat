@echo off
cd /d "%~dp0"

if exist "..\.venv\Scripts\python.exe" (
    set PY=..\.venv\Scripts\python.exe
) else (
    if not exist ".venv\Scripts\python.exe" (
        echo Creating virtual environment...
        py -m venv .venv || python -m venv .venv
    )
    set PY=.venv\Scripts\python.exe
)

%PY% -c "import pygame" 2>nul || %PY% -m pip install -r requirements.txt

%PY% main.py
echo.
pause
