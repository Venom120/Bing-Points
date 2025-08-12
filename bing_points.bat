@echo off
REM This script is used to run the Bing Points automation script.

REM Get the directory of the batch file
cd /d "%~dp0"

REM Install Python dependencies
pip show selenium >nul 2>&1
if errorlevel 1 (
    pip install selenium
)

pip show webdriver-manager >nul 2>&1
if errorlevel 1 (
    pip install webdriver-manager
)

REM Run the main script
python main.py