@echo off
REM TextNow Max Package Creator
echo ===============================================
echo Creating TextNow Max Package
echo ===============================================
echo.

REM Create directory for package
echo Creating package directory...
mkdir TextNowMax_PACKAGE 2>nul

REM Copy essential files
echo Copying files...
copy *.py TextNowMax_PACKAGE\
copy *.bat TextNowMax_PACKAGE\
copy *.md TextNowMax_PACKAGE\
copy *.json TextNowMax_PACKAGE\

REM Create needed directories
echo Creating directories...
mkdir TextNowMax_PACKAGE\static 2>nul
mkdir TextNowMax_PACKAGE\templates 2>nul
mkdir TextNowMax_PACKAGE\assets 2>nul
mkdir TextNowMax_PACKAGE\apk 2>nul
mkdir TextNowMax_PACKAGE\logs 2>nul
mkdir TextNowMax_PACKAGE\profiles 2>nul

REM Copy assets
echo Copying assets...
xcopy /E /I /Y static TextNowMax_PACKAGE\static
xcopy /E /I /Y templates TextNowMax_PACKAGE\templates
xcopy /E /I /Y assets TextNowMax_PACKAGE\assets

REM Create empty database
echo Creating empty database...
copy NUL TextNowMax_PACKAGE\ghost_accounts.db

REM Create RUN_TEXTNOW_MAX.bat
echo Creating run script...
(
echo @echo off
echo echo ===============================================
echo echo Starting TextNow Max
echo echo ===============================================
echo echo.
echo echo Make sure your Proxidize device is connected and configured
echo echo in proxidize_config.json before starting.
echo echo.
echo echo Press any key to start TextNow Max...
echo pause ^> nul
echo.
echo echo Starting TextNow Max...
echo python fixed_clickable_original.py
echo.
echo pause
) > TextNowMax_PACKAGE\RUN_TEXTNOW_MAX.bat

REM Create Zip file
echo Creating ZIP file...
powershell -Command "& {Compress-Archive -Path 'TextNowMax_PACKAGE\*' -DestinationPath 'TextNowMax.zip' -Force}"

echo.
echo ===============================================
echo Package created successfully!
echo ===============================================
echo.
echo The package includes:
echo - TextNow Max application
echo - Android emulator setup script
echo - Documentation and instructions
echo.
echo Download TextNowMax.zip and extract to use.
echo.
echo Press any key to exit...
pause > nul