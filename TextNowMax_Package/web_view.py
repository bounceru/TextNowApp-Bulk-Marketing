"""
Web viewer for ProgressGhostCreator

This script creates a simple web server to display screenshots of the application
so it can be viewed in Replit's environment.
"""

import os
import time
import threading
import logging
from PIL import ImageGrab
from flask import Flask, render_template, send_from_directory, jsonify
import subprocess
import signal
import atexit
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Create directory for screenshots
if not os.path.exists('static'):
    os.makedirs('static')

# Global variables
app_process = None
latest_screenshot = None
screenshot_interval = 2  # seconds

@app.route('/')
def index():
    """Render the main page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ProgressGhostCreator Preview</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #1E1E1E;
                color: #CCC;
                text-align: center;
                margin: 0;
                padding: 20px;
            }
            h1 {
                color: #FF6600;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
            }
            .screenshot {
                max-width: 100%;
                border: 2px solid #333;
                margin-top: 20px;
            }
            .controls {
                margin: 20px 0;
            }
            .btn {
                background-color: #FF6600;
                color: white;
                border: none;
                padding: 10px 20px;
                margin: 0 10px;
                cursor: pointer;
                font-weight: bold;
            }
            .info {
                background-color: #333;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
                text-align: left;
            }
        </style>
        <script>
            function refreshScreenshot() {
                const img = document.getElementById('screenshot');
                const timestamp = new Date().getTime();
                img.src = '/static/screenshot.png?' + timestamp;
            }
            
            // Refresh screenshot every 2 seconds
            setInterval(refreshScreenshot, 2000);
            
            // Initial load
            window.onload = refreshScreenshot;
        </script>
    </head>
    <body>
        <div class="container">
            <h1>ProgressGhostCreator Preview</h1>
            <div class="info">
                <p>This is a web preview of the ProgressGhostCreator application. The actual application will run as a Windows executable (.exe) file.</p>
                <p>The preview updates automatically every 2 seconds. This is a simulation only - the actual application will be built as an executable file for Windows.</p>
            </div>
            <div class="screenshot-container">
                <img id="screenshot" class="screenshot" src="/static/screenshot.png" alt="Application Screenshot" />
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

def take_screenshot():
    """Take a screenshot of the application window"""
    global latest_screenshot
    
    try:
        # Take a screenshot of the entire screen
        screenshot = ImageGrab.grab()
        
        # Save the screenshot
        screenshot_path = os.path.join('static', 'screenshot.png')
        screenshot.save(screenshot_path)
        latest_screenshot = screenshot_path
        logger.debug(f"Screenshot saved to {screenshot_path}")
    except Exception as e:
        logger.error(f"Failed to take screenshot: {e}")

def screenshot_thread():
    """Thread for taking screenshots periodically"""
    while True:
        take_screenshot()
        time.sleep(screenshot_interval)

def start_app():
    """Start the ProgressGhostCreator application"""
    global app_process
    
    try:
        logger.info("Starting ProgressGhostCreator application...")
        
        # Start the application process
        app_process = subprocess.Popen([sys.executable, 'main.py'], 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE)
        
        logger.info(f"Application started with PID: {app_process.pid}")
        
        # Register cleanup function
        atexit.register(cleanup)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")

def cleanup():
    """Clean up resources on shutdown"""
    global app_process
    
    if app_process:
        logger.info(f"Terminating application process (PID: {app_process.pid})...")
        try:
            os.kill(app_process.pid, signal.SIGTERM)
            app_process.wait(timeout=5)
        except:
            # Force kill if graceful termination fails
            try:
                os.kill(app_process.pid, signal.SIGKILL)
            except:
                pass
        logger.info("Application process terminated.")

if __name__ == '__main__':
    # Start the application
    start_app()
    
    # Start screenshot thread
    threading.Thread(target=screenshot_thread, daemon=True).start()
    
    # Start Flask server
    app.run(host='0.0.0.0', port=5000)