@echo off
echo ============================================================
echo      PROGRESS GHOST CREATOR LAUNCHER
echo ============================================================
echo.
echo This will start the ProgressGhostCreator application and open
echo it in your default web browser.
echo.
echo Requirements:
echo  - Python 3.8 or newer
echo  - Flask and Pillow packages
echo.
echo First time setup? Run this command first:
echo pip install flask pillow
echo.
echo Press any key to continue...
pause > nul
echo.

:: Check if Python is installed
echo Checking Python installation...
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in your PATH.
    echo Please install Python 3.8 or newer and try again.
    echo.
    echo Visit: https://www.python.org/downloads/
    echo.
    echo Press any key to exit...
    pause > nul
    exit /b
)

:: Check if Flask is installed
echo Checking required packages...
python -c "import flask" > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Flask is not installed.
    echo.
    echo Running: pip install flask pillow
    pip install flask pillow
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install required packages.
        echo Please run: pip install flask pillow
        echo.
        echo Press any key to exit...
        pause > nul
        exit /b
    )
)

:: Start server in a new CMD window that stays open
echo.
echo Starting ProgressGhostCreator server...
start cmd /k "title ProgressGhostCreator Server && color 0A && python app_preview_fixed.py"

:: Wait for server to start
echo.
echo Waiting for server to start up...
:: Try a few times to connect to localhost:5000
for /l %%x in (1, 1, 10) do (
    ping -n 2 127.0.0.1 > nul
    curl -s http://localhost:5000 > nul 2>&1
    if %ERRORLEVEL% EQU 0 goto server_started
    echo ...
)

:server_started
:: Sleep for 2 seconds to ensure server is fully ready
ping -n 3 127.0.0.1 > nul

:: Open the browser
echo.
echo Opening browser to http://localhost:5000...
start http://localhost:5000

echo.
echo ============================================================
echo PROGRESS GHOST CREATOR IS RUNNING
echo ============================================================
echo.
echo The application should now be open in your web browser.
echo.
echo If the browser didn't open automatically, go to: 
echo http://localhost:5000
echo.
echo IMPORTANT: Keep the server window open (black command window)
echo           while using the application.
echo.
echo To close the application, close the server window.
echo.
echo Press any key to exit this launcher...
pause > nul