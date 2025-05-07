@echo off
echo ============================================================
echo      BUILDING PROGRESS GHOST CREATOR
echo ============================================================
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

:: Check if PyInstaller is installed
echo Checking PyInstaller installation...
python -c "import PyInstaller" > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install PyInstaller.
        echo.
        echo Press any key to exit...
        pause > nul
        exit /b
    )
)

:: Check if other required packages are installed
echo Checking required packages...
python -c "import flask, PIL" > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing required packages...
    pip install flask pillow
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install required packages.
        echo.
        echo Press any key to exit...
        pause > nul
        exit /b
    )
)

:: Make sure assets folder exists
echo Checking folders...
if not exist "assets" (
    echo Creating assets folder...
    mkdir assets
)
if not exist "static" (
    echo Creating static folder...
    mkdir static
)

:: Build the application
echo.
echo Building the application...
echo This may take a few minutes...
echo.

:: Use PyInstaller with the spec file
pyinstaller ProgressGhostCreator.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error during build process.
    echo See error messages above for details.
    echo.
    echo Press any key to exit...
    pause > nul
    exit /b
)

:: Copy the batch files to the dist folder
echo.
echo Copying launcher files...
copy run_with_browser.bat dist\ProgressGhostCreator\run_ProgressGhostCreator.bat > nul
copy README.md dist\ProgressGhostCreator\ > nul

echo.
echo ============================================================
echo BUILD COMPLETE!
echo ============================================================
echo.
echo The executable has been created in:
echo dist\ProgressGhostCreator\ProgressGhostCreator.exe
echo.
echo To run the application:
echo 1. Navigate to dist\ProgressGhostCreator
echo 2. Double-click ProgressGhostCreator.exe
echo    -or-
echo    Double-click run_ProgressGhostCreator.bat
echo.
echo Press any key to exit...
pause > nul