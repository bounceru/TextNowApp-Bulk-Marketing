@echo off
color 0E
title ProgressGhostCreator - Install Dependencies and Run

echo ============================================================
echo  PROGRESS GHOST CREATOR - DEPENDENCY INSTALLER
echo ============================================================
echo.
echo This script will check for required modules and install them
echo if they're missing.
echo.

:: Check if Python is installed
echo Checking Python installation...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Python is not installed or not in your PATH.
    echo Please install Python 3.8 or newer and try again.
    echo.
    echo Visit: https://www.python.org/downloads/
    echo.
    echo During installation, make sure to check:
    echo "Add Python to PATH" option
    echo.
    echo Press any key to exit...
    pause > nul
    exit /b
)

:: Check if Flask is installed
echo.
echo Checking if Flask is installed...
python -c "import flask" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Flask is not installed. Installing Flask...
    pip install flask
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ERROR: Failed to install Flask.
        echo.
        echo Please try manually with:
        echo pip install flask
        echo.
        echo Press any key to exit...
        pause > nul
        exit /b
    )
    echo Flask installed successfully.
) else (
    echo Flask is already installed.
)

:: Check if Pillow is installed
echo.
echo Checking if Pillow (PIL) is installed...
python -c "import PIL" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Pillow is not installed. Installing Pillow...
    pip install pillow
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ERROR: Failed to install Pillow.
        echo.
        echo Please try manually with:
        echo pip install pillow
        echo.
        echo Press any key to exit...
        pause > nul
        exit /b
    )
    echo Pillow installed successfully.
) else (
    echo Pillow is already installed.
)

echo.
echo All dependencies installed successfully!
echo.
echo Press any key to start ProgressGhostCreator...
pause > nul

color 0A
cls
echo ============================================================
echo  PROGRESS GHOST CREATOR - RUNNING
echo ============================================================
echo.
echo Application is starting...
echo.
echo If the browser doesn't open automatically, go to:
echo http://localhost:5000
echo.
echo Keep this window open while using the application.
echo Press Ctrl+C to stop the server when done.
echo.

:: Start server and open browser
start "" http://localhost:5000
python app_preview_fixed.py

echo.
echo ============================================================
echo Server has stopped.
echo Press any key to exit...
pause > nul