@echo off
echo Starting ProgressGhostCreator application...
echo.
echo This will open a web browser to the application interface.
echo.
echo Make sure you have installed the required packages:
echo pip install flask pillow
echo.
echo Press any key to start the application...
pause
echo.
echo Running application... DO NOT CLOSE THIS WINDOW!
echo The application is running at http://localhost:5000
echo.
python app_preview_fixed.py
echo.
echo Application has stopped. Press any key to exit...
pause