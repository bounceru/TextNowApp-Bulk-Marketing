@echo off
REM TextNow Max Bundled Version Creator
echo ===============================================
echo Creating TextNow Max FULL ENTERPRISE Package
echo ===============================================
echo This will create a fully bundled version with Android emulator
echo and everything needed to run the software.
echo.
echo WARNING: The final package will be approximately 1.5-2GB in size.
echo.
echo Press any key to continue...
pause > nul

REM Create directories
echo Creating package directory...
mkdir TextNowMax_FULL 2>nul
mkdir TextNowMax_FULL\android-sdk 2>nul
mkdir TextNowMax_FULL\apk 2>nul
mkdir TextNowMax_FULL\static 2>nul
mkdir TextNowMax_FULL\templates 2>nul
mkdir TextNowMax_FULL\assets 2>nul
mkdir TextNowMax_FULL\logs 2>nul
mkdir TextNowMax_FULL\profiles 2>nul

REM Copy Python files
echo Copying Python files...
copy *.py TextNowMax_FULL\
copy *.md TextNowMax_FULL\
copy *.json TextNowMax_FULL\

REM Copy templates and static files
echo Copying web interface files...
xcopy /E /I /Y static TextNowMax_FULL\static
xcopy /E /I /Y templates TextNowMax_FULL\templates
xcopy /E /I /Y assets TextNowMax_FULL\assets

REM Create empty database
echo Creating empty database...
copy NUL TextNowMax_FULL\ghost_accounts.db

REM Download Android SDK
echo Downloading Android SDK (this may take a while)...
powershell -Command "& {$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://dl.google.com/android/repository/commandlinetools-win-8512546_latest.zip' -OutFile 'temp_sdk.zip'}"

echo Extracting Android SDK...
powershell -Command "& {Expand-Archive -Path 'temp_sdk.zip' -DestinationPath 'TextNowMax_FULL\android-sdk' -Force}"

REM Download Android Platform tools
echo Downloading Android Platform Tools...
powershell -Command "& {$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip' -OutFile 'temp_platform.zip'}"

echo Extracting Platform Tools...
powershell -Command "& {Expand-Archive -Path 'temp_platform.zip' -DestinationPath 'TextNowMax_FULL\android-sdk' -Force}"

REM Download sample TextNow APK placeholder
echo Creating APK placeholder...
echo This is a placeholder file. Please replace with the real TextNow APK. > TextNowMax_FULL\apk\DOWNLOAD_TEXTNOW_APK.txt
echo Recommended source: APKPure.com >> TextNowMax_FULL\apk\DOWNLOAD_TEXTNOW_APK.txt
echo Save the APK as textnow.apk in this folder. >> TextNowMax_FULL\apk\DOWNLOAD_TEXTNOW_APK.txt

REM Create essential batch files
echo Creating scripts...

REM Create All-in-One Setup batch file
echo @echo off > TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo ================================================= >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo TextNow Max - Automatic Setup and Launcher >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo ================================================= >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo This script will: >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo 1. Set up the Android emulator >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo 2. Check for the TextNow APK >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo 3. Start the emulator >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo 4. Launch TextNow Max >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo Press any key to start... >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo pause ^> nul >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo REM Set environment variables >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo set ANDROID_HOME=%%CD%%\android-sdk >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo set PATH=%%PATH%%;%%ANDROID_HOME%%\cmdline-tools\bin;%%ANDROID_HOME%%\platform-tools;%%ANDROID_HOME%%\emulator >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo REM Check Java >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo Checking Java installation... >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo java -version ^> nul 2^>^&1 >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo if %%ERRORLEVEL%% neq 0 ( >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo    echo Java is not installed or not in PATH. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo    echo Please install Java JDK 8 or newer before continuing. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo    echo You can download it from https://adoptopenjdk.net/ >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo    echo. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo    echo Press any key to exit... >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo    pause ^> nul >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo    exit /b 1 >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo ) >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo Java found. Continuing setup... >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo REM Check for TextNow APK >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo if not exist "apk\textnow.apk" ( >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo    echo TextNow APK not found! >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo    echo Please download the TextNow APK and save it as "textnow.apk" in the apk folder. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo    echo. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo    echo Press any key to continue without TextNow APK... >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo    pause ^> nul >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo ) else ( >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo    echo TextNow APK found! >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo ) >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo REM Accept licenses >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo Accepting Android SDK licenses... >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo y | android-sdk\cmdline-tools\bin\sdkmanager.bat --licenses >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo REM Install required SDK components >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo Installing SDK components... >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo This may take some time, please be patient... >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo android-sdk\cmdline-tools\bin\sdkmanager.bat "platform-tools" "platforms;android-30" "system-images;android-30;google_apis;x86_64" "build-tools;30.0.3" "emulator" >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo REM Create AVD >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo Creating Android Virtual Devices... >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo "no" | android-sdk\cmdline-tools\bin\avdmanager.bat create avd -n textnow_emulator_1 -k "system-images;android-30;google_apis;x86_64" -d "pixel_3a" >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo "no" | android-sdk\cmdline-tools\bin\avdmanager.bat create avd -n textnow_emulator_2 -k "system-images;android-30;google_apis;x86_64" -d "pixel_4" >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo REM Start emulator >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo Starting Android Emulator... >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo start android-sdk\emulator\emulator.exe -avd textnow_emulator_1 -no-audio -no-boot-anim >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo Waiting for emulator to boot... >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo timeout /t 30 >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo REM Start TextNow Max >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo Starting TextNow Max... >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo python fixed_clickable_original.py >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo. >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo echo TextNow Max stopped. Press any key to exit... >> TextNowMax_FULL\SETUP_AND_RUN.bat
echo pause ^> nul >> TextNowMax_FULL\SETUP_AND_RUN.bat

REM Create standard run file (no setup)
echo @echo off > TextNowMax_FULL\RUN_TEXTNOW_MAX.bat
echo echo ================================================= >> TextNowMax_FULL\RUN_TEXTNOW_MAX.bat
echo echo TextNow Max >> TextNowMax_FULL\RUN_TEXTNOW_MAX.bat
echo echo ================================================= >> TextNowMax_FULL\RUN_TEXTNOW_MAX.bat
echo echo. >> TextNowMax_FULL\RUN_TEXTNOW_MAX.bat
echo echo Make sure your Proxidize device is connected. >> TextNowMax_FULL\RUN_TEXTNOW_MAX.bat
echo echo Press any key to start... >> TextNowMax_FULL\RUN_TEXTNOW_MAX.bat
echo pause ^> nul >> TextNowMax_FULL\RUN_TEXTNOW_MAX.bat
echo. >> TextNowMax_FULL\RUN_TEXTNOW_MAX.bat
echo echo Starting TextNow Max... >> TextNowMax_FULL\RUN_TEXTNOW_MAX.bat
echo python fixed_clickable_original.py >> TextNowMax_FULL\RUN_TEXTNOW_MAX.bat
echo. >> TextNowMax_FULL\RUN_TEXTNOW_MAX.bat
echo pause >> TextNowMax_FULL\RUN_TEXTNOW_MAX.bat

REM Create emulator start script
echo @echo off > TextNowMax_FULL\START_EMULATOR.bat
echo echo Starting Android Emulator... >> TextNowMax_FULL\START_EMULATOR.bat
echo set ANDROID_HOME=%%CD%%\android-sdk >> TextNowMax_FULL\START_EMULATOR.bat
echo set PATH=%%PATH%%;%%ANDROID_HOME%%\cmdline-tools\bin;%%ANDROID_HOME%%\platform-tools;%%ANDROID_HOME%%\emulator >> TextNowMax_FULL\START_EMULATOR.bat
echo start %%ANDROID_HOME%%\emulator\emulator.exe -avd textnow_emulator_1 -no-audio -no-boot-anim >> TextNowMax_FULL\START_EMULATOR.bat
echo echo. >> TextNowMax_FULL\START_EMULATOR.bat
echo echo Emulator started. Please wait for it to fully boot up. >> TextNowMax_FULL\START_EMULATOR.bat
echo echo This may take a few minutes. >> TextNowMax_FULL\START_EMULATOR.bat
echo echo. >> TextNowMax_FULL\START_EMULATOR.bat
echo echo After the emulator is booted, you can run TextNow Max with RUN_TEXTNOW_MAX.bat >> TextNowMax_FULL\START_EMULATOR.bat
echo pause >> TextNowMax_FULL\START_EMULATOR.bat

REM Create config file for the emulator 
echo {> TextNowMax_FULL\emulator_config.json
echo   "emulator_count": 2,>> TextNowMax_FULL\emulator_config.json
echo   "headless_mode": true,>> TextNowMax_FULL\emulator_config.json
echo   "apk_path": "./apk/textnow.apk",>> TextNowMax_FULL\emulator_config.json
echo   "sdk_path": "./android-sdk",>> TextNowMax_FULL\emulator_config.json
echo   "proxy_per_emulator": true,>> TextNowMax_FULL\emulator_config.json
echo   "reset_after_count": 5>> TextNowMax_FULL\emulator_config.json
echo }>> TextNowMax_FULL\emulator_config.json

REM Create standalone package
echo Creating standalone package ZIP...
powershell -Command "& {Compress-Archive -Path 'TextNowMax_FULL\*' -DestinationPath 'TextNowMax_FULL_ENTERPRISE.zip' -Force}"

echo.
echo ================================================
echo TextNow Max FULL ENTERPRISE package created!
echo ================================================
echo.
echo The package includes:
echo - TextNow Max application
echo - Android SDK and Emulator (bundled)
echo - Easy setup script
echo - All necessary components
echo.
echo NOTE: You still need to provide the TextNow APK.
echo.
echo Download TextNowMax_FULL_ENTERPRISE.zip for the complete package.
echo.
echo ================================================
echo.
echo Press any key to exit...
pause > nul