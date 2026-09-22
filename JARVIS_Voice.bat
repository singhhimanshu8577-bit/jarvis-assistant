@echo off
title JARVIS Voice Assistant - Voice Mode
cd /d "%~dp0"

echo ===================================================
echo   Starting JARVIS AI Voice Assistant (Voice Mode)
echo ===================================================
echo.

if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" main.py --voice
) else (
    python main.py --voice
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo [JARVIS] Assistant terminated with code %ERRORLEVEL%.
    pause
)
