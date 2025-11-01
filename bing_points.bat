@echo off
REM This script will set up the virtual environment and run the Bing Points app.
echo Checking for Python virtual environment...

REM Get the directory of the batch file
cd /d "%~dp0"

echo Installing dependencies...
pip install -r req.txt

echo Launching Bing Points Bot...
python main.py