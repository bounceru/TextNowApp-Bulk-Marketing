@echo off
color 0A
title FIXED CLICKABLE VERSION - ProgressGhostCreator

echo ============================================================
echo  PROGRESS GHOST CREATOR - ALL BUTTONS CLICKABLE
echo ============================================================
echo.
echo This version preserves ALL original content but makes all buttons CLICKABLE
echo.

:: Check if Python is installed
python --version
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo.
    echo ERROR: Python is not installed!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    echo Press any key to exit...
    pause > nul
    exit /b
)

:: Install Flask
echo.
echo Installing required packages...
pip install flask pillow
echo.
echo Starting fixed version with CLICKABLE BUTTONS...
echo.
echo If the browser doesn't open automatically, go to:
echo http://localhost:5000
echo.
echo DO NOT CLOSE THIS WINDOW WHILE USING THE APPLICATION
echo.

:: Start the fixed version and open browser
start "" http://localhost:5000
python fixed_clickable_original.py

echo.
echo Application has stopped.
echo Press any key to exit...
pause > nul