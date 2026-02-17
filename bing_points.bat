@echo off
REM This script will set up the virtual environment and run the Bing Points app.
echo Checking for Python virtual environment...

REM Get the directory of the batch file
cd /d "%~dp0"

echo Installing dependencies...
pip install -r req.txt --quiet
if errorlevel 1 (
    echo Dependencies installed successfully.
) else (
    echo Dependencies already installed.
)

echo Launching Bing Points Bot...
python main.py