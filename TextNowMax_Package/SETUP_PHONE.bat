@echo off
echo ============================================================
echo TextNow Max Creator - Phone Setup Utility
echo ============================================================
echo.
echo This utility will help you set up your BLU G44 phone for IP rotation.
echo.

echo Step 1: Checking if ADB is installed...
where adb >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Android Debug Bridge (ADB) is not installed or not in your PATH.
    echo.
    echo Please download the Android SDK Platform Tools from:
    echo https://developer.android.com/studio/releases/platform-tools
    echo.
    echo Extract the downloaded file and add the folder to your PATH.
    echo.
    pause
    exit /b 1
)

echo ADB found. Checking for connected devices...
adb devices

echo.
echo Step 2: Setting up the phone...
echo.
echo Please make sure your BLU G44 phone is:
echo - Connected to your computer via USB
echo - Has Developer Options enabled (Settings > About Phone > Tap Build Number 7 times)
echo - Has USB Debugging enabled (Settings > System > Developer Options)
echo.
echo Press any key when ready...
pause >nul

echo.
echo Step 3: Testing connection...
adb devices | find "device" >nul
if %errorlevel% neq 0 (
    echo ERROR: No device detected or device is not authorized.
    echo.
    echo Please check that:
    echo - The phone is connected properly
    echo - You have accepted the USB debugging authorization prompt on the phone
    echo - The phone is not in "charging only" mode (change USB mode to file transfer)
    echo.
    pause
    exit /b 1
)

echo Device connected! Testing airplane mode toggling...
echo.
echo Turning airplane mode ON...
adb shell settings put global airplane_mode_on 1
adb shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true
timeout /t 5

echo Turning airplane mode OFF...
adb shell settings put global airplane_mode_on 0
adb shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false
timeout /t 5

echo.
echo Getting current IP address...
adb shell "ip addr show wlan0 | grep 'inet ' | cut -d' ' -f6 | cut -d/ -f1"

echo.
echo ============================================================
echo Phone setup completed successfully!
echo Your phone is now ready to be used with TextNow Max Creator.
echo.
echo When running the app, go to the Device Manager section to connect
echo to your phone and use the IP rotation features.
echo ============================================================
echo.
pause