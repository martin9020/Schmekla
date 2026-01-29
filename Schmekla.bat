@echo off
REM Schmekla Launcher - One-Click Install & Run
REM ==========================================

REM Get the directory where this script is located
cd /d "%~dp0"

echo [Schmekla] Checking environment...

REM Define paths
set "SHARED_VENV=c:\Users\Daradudai\Everything-Claude\Schmekla\venv"
set "LOCAL_VENV=venv"

REM 1. Check Shared Venv (Optional override)
if defined SHARED_VENV_PATH (
    if exist "%SHARED_VENV_PATH%\Scripts\python.exe" (
        echo [Schmekla] Found shared venv at: %SHARED_VENV_PATH%
        set "VENV_DIR=%SHARED_VENV_PATH%"
    )
)

if not defined VENV_DIR (
    REM 2. Check/Create Local Venv (Portability Fallback)
    if not exist "%LOCAL_VENV%\Scripts\python.exe" (
        echo [Schmekla] Local venv not found.
        echo [Schmekla] Creating local virtual environment for portability...
        
        py -3.12 -m venv %LOCAL_VENV%
        if errorlevel 1 (
            echo [ERROR] Failed to create virtual environment.
            echo Please ensure Python 3.12 is installed and available via 'py -3.12'.
            pause
            exit /b 1
        )
        echo [Schmekla] Local virtual environment created.
    ) else (
        echo [Schmekla] Using existing local virtual environment.
    )
    set "VENV_DIR=%LOCAL_VENV%"
)

REM Install/Update dependencies (Stepped installation for better feedback)
echo [Schmekla] Starting dependency check...

echo [Schmekla] [1/4] Installing Core Utilities (numpy, requests, loguru)...
"%VENV_DIR%\Scripts\python.exe" -m pip install numpy requests loguru --constraint requirements.txt
if errorlevel 1 goto :error

echo [Schmekla] [2/4] Installing UI Framework (PySide6, qtpy)...
"%VENV_DIR%\Scripts\python.exe" -m pip install PySide6 QtPy pyvistaqt --constraint requirements.txt
if errorlevel 1 goto :error

echo [Schmekla] [3/4] Installing Geometry Engine (CadQuery, VTK, PyVista)...
"%VENV_DIR%\Scripts\python.exe" -m pip install cadquery vtk pyvista --constraint requirements.txt
if errorlevel 1 goto :error

echo [Schmekla] [4/4] Finalizing and verifying all dependencies...
"%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

goto :run

:error
echo [ERROR] Failed to install dependencies.
pause
exit /b 1

:run
REM Run Schmekla
echo [Schmekla] Starting application...
echo ------------------------------------------
"%VENV_DIR%\Scripts\python.exe" -m src.main

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo [Schmekla] Application exited with an error.
    pause
)

