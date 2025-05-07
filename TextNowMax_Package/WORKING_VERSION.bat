@echo off
color 0A
title WORKING VERSION - ProgressGhostCreator

echo ============================================================
echo  PROGRESS GHOST CREATOR - WORKING VERSION
echo ============================================================
echo.
echo This is the FIXED VERSION that ensures all buttons are clickable
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
echo Starting fixed version with clickable buttons...
echo.
echo If the browser doesn't open automatically, go to:
echo http://localhost:5000
echo.
echo DO NOT CLOSE THIS WINDOW WHILE USING THE APPLICATION
echo.

:: Start the fixed version and open browser
start "" http://localhost:5000
python clickable_app.py

echo.
echo Application has stopped.
echo Press any key to exit...
pause > nul