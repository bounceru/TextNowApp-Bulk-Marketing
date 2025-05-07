@echo off
echo =======================================
echo PROGRESS GHOST CREATOR - PHONE TEST GUI
echo =======================================
echo.
echo This will test if we can connect to your BLU G44 phone
echo and control its airplane mode for IP rotation.
echo.
echo Make sure your phone is connected via USB and USB debugging is enabled.
echo.
python adb_phone_test_gui.py
echo.
if %ERRORLEVEL% NEQ 0 (
  echo There was an error running the test. Please check that tkinter is installed.
  echo Falling back to command line version...
  python adb_phone_test.py
)