@echo off
echo ========================================
echo   Schmekla Installation Script
echo ========================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

echo [1/5] Python found:
python --version
echo.

:: Navigate to script directory
cd /d "%~dp0\.."
echo [2/5] Working directory: %CD%
echo.

:: Remove old venv if exists
if exist venv (
    echo Removing old virtual environment...
    rmdir /s /q venv
)

:: Create new virtual environment
echo [3/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created.
echo.

:: Activate and install dependencies
echo [4/5] Installing dependencies (this may take a few minutes)...
call venv\Scripts\activate.bat

pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed.
echo.

:: Create desktop shortcut
echo [5/5] Creating launcher script...
(
echo @echo off
echo cd /d "%CD%"
echo call venv\Scripts\activate.bat
echo python -m src.main
echo pause
) > run_schmekla.bat

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo To run Schmekla:
echo   1. Double-click "run_schmekla.bat"
echo   OR
echo   2. Open terminal here and run:
echo      venv\Scripts\activate
echo      python -m src.main
echo.
pause
