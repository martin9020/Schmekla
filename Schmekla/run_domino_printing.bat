@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python launch_domino_printing.py
pause
