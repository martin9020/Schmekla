@echo off
REM Schmekla Launcher - One-Click Install & Run
REM ==========================================

REM Get the directory where this script is located
cd /d "%~dp0"

echo [Schmekla] Checking environment...

REM Define paths
set "SHARED_VENV=G:\My Drive\Everything-Claude\Schmekla\venv"
set "LOCAL_VENV=venv"

REM 1. Check Shared Venv (User Preference)
if exist "%SHARED_VENV%\Scripts\python.exe" (
    echo [Schmekla] Found shared venv at: %SHARED_VENV%
    set "VENV_DIR=%SHARED_VENV%"
) else (
    REM 2. Check/Create Local Venv (Portability Fallback)
    if not exist "%LOCAL_VENV%\Scripts\python.exe" (
        echo [Schmekla] Shared venv not found.
        echo [Schmekla] Creating local virtual environment for portability...
        
        python -m venv %LOCAL_VENV%
        if errorlevel 1 (
            echo [ERROR] Failed to create virtual environment.
            echo Please ensure Python 3.11+ is installed and in your PATH.
            pause
            exit /b 1
        )
        echo [Schmekla] Local virtual environment created.
    ) else (
        echo [Schmekla] Using existing local virtual environment.
    )
    set "VENV_DIR=%LOCAL_VENV%"
)

REM Install/Update dependencies
echo [Schmekla] Checking dependencies in: %VENV_DIR%
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
"%VENV_DIR%\Scripts\pip.exe" install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

REM Run Schmekla
REM Run Schmekla
echo [Schmekla] Starting application...
echo ------------------------------------------
"%VENV_DIR%\Scripts\python.exe" src/main.py

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo [Schmekla] Application exited with an error.
    pause
)

