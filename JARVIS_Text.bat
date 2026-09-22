@echo off
title JARVIS Voice Assistant - Interactive Console
cd /d "%~dp0"

echo ===================================================
echo   Starting JARVIS AI Assistant (Interactive Console)
echo ===================================================
echo.

if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" main.py --text
) else (
    python main.py --text
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo [JARVIS] Assistant terminated with code %ERRORLEVEL%.
    pause
)
