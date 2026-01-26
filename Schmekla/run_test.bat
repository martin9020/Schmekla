@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python test_model.py > test_output.txt 2>&1
type test_output.txt
