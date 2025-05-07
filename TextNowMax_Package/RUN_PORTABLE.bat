@echo off
echo ============================================================
echo TextNow Max Creator - Portable Edition
echo ============================================================
echo.
echo Starting TextNow Max Creator...
echo.
echo The application will open in your web browser.
echo Press CTRL+C in the command window to stop the application.
echo.

if exist TextNowMaxCreator.exe (
    start TextNowMaxCreator.exe
) else (
    echo ERROR: TextNowMaxCreator.exe not found.
    echo Please make sure you have built the application first.
    echo See BUILD_INSTRUCTIONS.md for details.
    pause
)