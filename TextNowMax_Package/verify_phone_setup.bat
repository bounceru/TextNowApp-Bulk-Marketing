@echo off
echo =======================================
echo PROGRESS GHOST CREATOR - PHONE SETUP
echo =======================================
echo.
echo This utility will help you verify that your BLU G44 phone
echo can be properly connected and controlled for IP rotation.
echo.
echo The process has two steps:
echo 1. Check and install ADB if needed
echo 2. Test the phone connection and airplane mode control
echo.
echo Press any key to begin...
pause > nul

echo.
echo Step 1: Setting up ADB (Android Debug Bridge)
echo --------------------------------------------
call setup_adb.bat

echo.
echo Step 2: Testing Phone Connection
echo -----------------------------
call test_phone_connection_gui.bat

echo.
echo Setup and testing complete.
echo If all tests passed, your phone is ready for use with ProgressGhostCreator!
echo.
pause