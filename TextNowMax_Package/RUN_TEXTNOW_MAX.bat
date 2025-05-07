@echo off
echo ============================================================
echo TextNow Max Creator - Startup Script
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in your PATH.
    echo Please install Python 3.8 or higher and try again.
    echo.
    pause
    exit /b 1
)

REM Check for required dependencies
echo Checking for required dependencies...
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Flask...
    pip install flask
)

python -c "import playwright" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Playwright...
    pip install playwright
    python -m playwright install
)

REM Check for the main script
if not exist fixed_clickable_original.py (
    echo Error: Could not find the main application script.
    echo Please make sure you are running this batch file from the correct directory.
    echo.
    pause
    exit /b 1
)

REM Create necessary directories
if not exist static mkdir static
if not exist logs mkdir logs
if not exist assets mkdir assets

REM Process assets
echo Looking for assets...
if exist attached_assets\progress_logo.png (
    echo Found logo at attached_assets\progress_logo.png
    copy attached_assets\progress_logo.png static\progress_logo.png >nul
)

if exist attached_assets\progress_background.jpg (
    echo Found background at attached_assets\progress_background.jpg
    copy attached_assets\progress_background.jpg static\progress_background.jpg >nul
)

echo.
echo ============================================================
echo Starting TextNow Max Creator...
echo ============================================================
echo.
echo The application will open in your web browser.
echo Press CTRL+C to stop the application.
echo.

REM Run the application
python fixed_clickable_original.py

echo.
echo TextNow Max Creator has been closed.
echo.
pause