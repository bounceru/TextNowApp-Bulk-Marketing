@echo off
REM TextNow Max Android Emulator Setup Script
echo ===============================================
echo TextNow Max - Android Emulator Setup
echo ===============================================
echo.
echo This script will download and install the Android SDK and set up
echo emulators for TextNow account creation.
echo.
echo Press any key to continue...
pause > nul

REM Create directories
echo Creating directories...
mkdir android-sdk 2>nul
mkdir apk 2>nul
mkdir temp 2>nul

REM Check if Java is installed
echo Checking Java installation...
java -version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Java is not installed or not in PATH.
    echo Please install Java JDK 8 or newer before continuing.
    echo You can download it from https://adoptopenjdk.net/
    echo.
    echo Press any key to exit...
    pause > nul
    exit /b 1
)

echo Java found. Continuing installation...
echo.

REM Download Android SDK commandline tools
echo Downloading Android SDK tools...
powershell -Command "& {Invoke-WebRequest -Uri 'https://dl.google.com/android/repository/commandlinetools-win-8512546_latest.zip' -OutFile 'temp\sdk-tools.zip'}"

echo Extracting Android SDK tools...
powershell -Command "& {Expand-Archive -Path 'temp\sdk-tools.zip' -DestinationPath 'android-sdk' -Force}"

REM Setup environment variables
echo Setting up environment variables...
set ANDROID_HOME=%CD%\android-sdk
set PATH=%PATH%;%ANDROID_HOME%\cmdline-tools\bin;%ANDROID_HOME%\platform-tools

REM Accept licenses
echo Accepting Android SDK licenses...
echo y | android-sdk\cmdline-tools\bin\sdkmanager.bat --licenses

REM Install required SDK components
echo Installing SDK components...
echo This may take some time, please be patient...
echo.
android-sdk\cmdline-tools\bin\sdkmanager.bat "platform-tools" "platforms;android-30" "system-images;android-30;google_apis;x86_64" "build-tools;30.0.3" "emulator"

REM Install ADB
echo Installing ADB (Android Debug Bridge)...
android-sdk\cmdline-tools\bin\sdkmanager.bat "platform-tools"

REM Create AVD (Android Virtual Device)
echo Creating Android Virtual Devices...
echo "no" | android-sdk\cmdline-tools\bin\avdmanager.bat create avd -n textnow_emulator_1 -k "system-images;android-30;google_apis;x86_64" -d "pixel_3a"
echo "no" | android-sdk\cmdline-tools\bin\avdmanager.bat create avd -n textnow_emulator_2 -k "system-images;android-30;google_apis;x86_64" -d "pixel_4"
echo "no" | android-sdk\cmdline-tools\bin\avdmanager.bat create avd -n textnow_emulator_3 -k "system-images;android-30;google_apis;x86_64" -d "Nexus 5"

REM Download TextNow APK
echo Downloading TextNow APK...
echo Note: You may need to manually download the TextNow APK
echo and place it in the 'apk' folder as 'textnow.apk'.
echo.
echo You can get the APK from legitimate APK libraries
echo such as APKPure or APKMirror.
echo.

REM Create helper scripts
echo Creating helper scripts...

REM Create start script
echo @echo off > START_EMULATOR.bat
echo echo Starting Android Emulator... >> START_EMULATOR.bat
echo set ANDROID_HOME=%CD%\android-sdk >> START_EMULATOR.bat
echo set PATH=%%PATH%%;%%ANDROID_HOME%%\cmdline-tools\bin;%%ANDROID_HOME%%\platform-tools;%%ANDROID_HOME%%\emulator >> START_EMULATOR.bat
echo start %%ANDROID_HOME%%\emulator\emulator.exe -avd textnow_emulator_1 -no-audio -no-boot-anim >> START_EMULATOR.bat
echo echo. >> START_EMULATOR.bat
echo echo Emulator started. Please wait for it to fully boot up. >> START_EMULATOR.bat
echo echo This may take a few minutes. >> START_EMULATOR.bat
echo echo. >> START_EMULATOR.bat
echo echo After the emulator is booted, you can create accounts through TextNow Max. >> START_EMULATOR.bat
echo pause >> START_EMULATOR.bat

REM Create config file for the emulator 
echo {> emulator_config.json
echo   "emulator_count": 2,>> emulator_config.json
echo   "headless_mode": true,>> emulator_config.json
echo   "apk_path": "./apk/textnow.apk",>> emulator_config.json
echo   "sdk_path": "./android-sdk",>> emulator_config.json
echo   "proxy_per_emulator": true,>> emulator_config.json
echo   "reset_after_count": 5>> emulator_config.json
echo }>> emulator_config.json

REM Setup complete
echo.
echo ================================================
echo Setup Complete!
echo ================================================
echo.
echo To use the Android emulator with TextNow Max:
echo.
echo 1. Make sure to add a TextNow APK file named "textnow.apk" 
echo    to the "apk" folder.
echo.
echo 2. Run START_EMULATOR.bat before running TextNow Max
echo.
echo 3. The emulator will run in the background and TextNow Max will
echo    connect to it automatically.
echo.
echo Note: The emulator requires significant system resources.
echo       Make sure your PC has at least 8GB of RAM and a decent CPU.
echo.
echo Press any key to exit...
pause > nul