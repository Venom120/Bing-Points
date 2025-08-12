@echo off
REM This script is used to run the Bing Points automation script.
REM It checks for an existing virtual environment, creates it if it doesn't exist, activates it, and then runs the script.

REM Get the directory of the batch file
cd /d "%~dp0"

REM Check if the virtual environment exists
if not exist .\.venv (
    echo Creating virtual environment...
    python -m venv .venv
    echo Installing dependencies...
    pip install -r req.txt
)

REM Activate the virtual environment
call .\.venv\Scripts\activate

REM Run the main script
python main.py

REM Deactivate the virtual environment
deactivate