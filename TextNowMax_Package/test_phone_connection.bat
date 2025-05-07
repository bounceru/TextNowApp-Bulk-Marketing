@echo off
echo ===================================
echo PROGRESS GHOST CREATOR - PHONE TEST
echo ===================================
echo.
echo This will test if we can connect to your BLU G44 phone
echo and control its airplane mode for IP rotation.
echo.
echo Make sure your phone is connected via USB and USB debugging is enabled.
echo.
python adb_phone_test.py
echo.
echo Test completed. Press any key to exit...
pause > nul