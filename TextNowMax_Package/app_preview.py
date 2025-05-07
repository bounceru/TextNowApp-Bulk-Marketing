"""
Preview server for ProgressGhostCreator app

This script creates a simple HTTP server that displays a mockup of the application
to showcase how it will look when running as a Windows executable.
"""

from flask import Flask, render_template_string, send_from_directory, redirect, url_for, request
import os
import json
import datetime
import random
import string

app = Flask(__name__)

# Ensure static folder exists
os.makedirs('static', exist_ok=True)

def get_nav_menu(active_page):
    """Generate consistent navigation menu HTML with active page highlighted"""
    # Standard navigation bar that will be placed at the top of every page
    navigation_html = """
    <style>
        #fixed-nav-bar {
            background-color: #FF6600;
            padding: 10px 20px;
            width: 100%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: fixed;
            top: 0;
            left: 0;
            z-index: 1000;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        #nav-logo {
            max-height: 40px;
        }
        #nav-menu {
            display: flex;
            flex-wrap: wrap;
        }
        .nav-link {
            color: white;
            padding: 8px 15px;
            margin-left: 10px;
            text-decoration: none;
            font-weight: bold;
            border-radius: 3px;
            background-color: #AA4400;
        }
        .nav-link:hover {
            background-color: #CC5500;
        }
        .nav-link.active {
            background-color: #CC5500;
        }
        #content-wrapper {
            margin-top: 60px; /* Space for the fixed navbar */
        }
    </style>
    
    <div id="fixed-nav-bar">
        <img src="/static/progress_logo.png" alt="PB BETTING Logo" id="nav-logo">
        <div id="nav-menu">
    """
    
    # Add each navigation link
    pages = [
        ('/', 'Home'),
        ('/creator', 'Creator'),
        ('/dashboard', 'Dashboard'),
        ('/campaigns', 'Campaigns'),
        ('/manual_messaging', 'Manual Messages'),
        ('/message-dashboard', 'Message Monitor'),
        ('/image-dashboard', 'Image Manager'),
        ('/account-health', 'Account Health'),
        ('/voicemail-manager', 'Voicemail Manager'),
        ('/campaign_schedule', 'Schedule')
    ]
    
    for url, name in pages:
        active_class = ' active' if url == active_page else ''
        navigation_html += f'<a href="{url}" class="nav-link{active_class}">{name}</a>'
    
    # Close the navigation HTML
    navigation_html += """
        </div>
    </div>
    <div id="content-wrapper">
    """
    
    return navigation_html

@app.route('/')
def index():
    """Display the mockup of the ProgressGhostCreator application"""
    process_assets()
    nav_menu = get_nav_menu('/')
    return render_template_string('''
    {{ nav_menu|safe }}
    
    <!DOCTYPE html>
    <html>
    <head>
        <title>ProgressGhostCreator</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-image: url('/static/progress_background.jpg');
                background-size: cover;
                background-position: center;
                color: white;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .app-container {
                width: 1000px;
                height: 700px;
                background-color: rgba(30, 30, 30, 0.95);
                border-radius: 10px;
                box-shadow: 0 0 15px rgba(0,0,0,0.5);
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }
            .app-header {
                background-color: #FF6600;
                padding: 15px;
                text-align: center;
                border-bottom: 1px solid #333;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .nav-menu {
                display: flex;
            }
            .nav-button {
                background-color: #AA4400;
                color: white;
                border: none;
                padding: 8px 15px;
                margin-left: 10px;
                cursor: pointer;
                border-radius: 3px;
                font-weight: bold;
                text-decoration: none;
                font-size: 14px;
            }
            .nav-button:hover {
                background-color: #CC5500;
            }
            .active {
                background-color: #CC5500;
            }
            .welcome-container {
                flex: 1;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                padding: 30px;
                text-align: center;
            }
            .logo {
                max-width: 150px;
                height: auto;
            }
            .welcome-container .logo {
                max-width: 250px;
                margin-bottom: 20px;
            }
            h1 {
                font-size: 30px;
                margin-bottom: 20px;
                color: #FF6600;
            }
            p {
                font-size: 16px;
                margin-bottom: 25px;
                line-height: 1.5;
            }
            .button-container {
                display: flex;
                justify-content: center;
                gap: 20px;
            }
            .button {
                background-color: #FF6600;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                text-decoration: none;
                transition: background-color 0.3s;
            }
            .button:hover {
                background-color: #FF8833;
            }
            .secondary-button {
                background-color: #555;
            }
            .secondary-button:hover {
                background-color: #777;
            }
            .stats {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #555;
                display: flex;
                justify-content: space-around;
            }
            .stat-item {
                text-align: center;
            }
            .stat-value {
                font-size: 24px;
                font-weight: bold;
                color: #FF6600;
                margin-bottom: 5px;
            }
            .stat-label {
                font-size: 14px;
                color: #AAA;
            }
            .version {
                margin-top: 20px;
                font-size: 12px;
                color: #777;
            }
            .app-footer {
                padding: 8px 15px;
                background-color: #252525;
                border-top: 1px solid #444;
                font-size: 12px;
                color: #888;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="app-container">
            <div class="app-header">
                {% if logo_exists %}
                <img src="/static/progress_logo.png" alt="PB BETTING Logo" class="logo">
                {% endif %}
                {{ nav_menu|safe }}
            </div>
            
            <div class="welcome-container">
                <h1>Welcome to ProgressGhostCreator</h1>
                <p>The advanced TextNow account management and automation platform. Create, manage, and utilize ghost accounts with sophisticated distribution, voicemail setup, and messaging capabilities.</p>
                
                <div class="button-container">
                    <a href="/creator" class="button">Create Accounts</a>
                    <a href="/dashboard" class="button">Manage Accounts</a>
                    <a href="/campaigns" class="button">Campaigns</a>
                </div>
            
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value">10,563</div>
                    <div class="stat-label">Ghost Accounts</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">5,219</div>
                    <div class="stat-label">Active Accounts</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">892,145</div>
                    <div class="stat-label">Messages Sent</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">98.7%</div>
                    <div class="stat-label">Success Rate</div>
                </div>
            </div>
            
            <div class="version">ProgressGhostCreator v1.0.0 | © 2024 ProgressBets™ | 5 Accounts Active</div>
            </div>
            
            <div class="app-footer">
                © ProgressBets™ | TextNow v1.0.0 | 5 Accounts Active
            </div>
        </div>
    </body>
    </html>
    ''', logo_exists=os.path.exists("static/progress_logo.png"))

@app.route('/creator')
def creator_page():
    """The main account creator page"""
    process_assets()
    nav_menu = get_nav_menu('/creator')
    return render_template_string('''
    {{ nav_menu|safe }}
    <!DOCTYPE html>
    <html>
    <head>
        <title>ProgressGhostCreator - Account Creator</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-image: url('/static/progress_background.jpg');
                background-size: cover;
                background-position: center;
                color: white;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            
            .app-container {
                width: 1000px;
                height: 700px;
                background-color: rgba(30, 30, 30, 0.95);
                border-radius: 10px;
                box-shadow: 0 0 15px rgba(0,0,0,0.5);
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }
            
            .app-header {
                background-color: #FF6600;
                padding: 15px;
                text-align: center;
                border-bottom: 1px solid #333;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .logo {
                max-width: 150px;
                height: auto;
            }
            
            .nav-menu {
                display: flex;
            }
            
            .nav-button {
                background-color: #AA4400;
                color: white;
                border: none;
                padding: 8px 15px;
                margin-left: 10px;
                cursor: pointer;
                border-radius: 3px;
                font-weight: bold;
                text-decoration: none;
                font-size: 14px;
            }
            
            .nav-button:hover {
                background-color: #CC5500;
            }
            
            .active {
                background-color: #CC5500;
            }
            
            .app-content {
                display: flex;
                flex: 1;
            }
            
            .sidebar {
                width: 300px;
                background-color: #252525;
                border-right: 1px solid #444;
                padding: 20px;
                overflow-y: auto;
            }
            
            .section-title {
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 15px;
                color: #EEE;
                border-bottom: 1px solid #444;
                padding-bottom: 10px;
            }
            
            .form-group {
                margin-bottom: 15px;
            }
            
            .form-label {
                display: block;
                margin-bottom: 5px;
                color: #CCC;
                font-size: 14px;
            }
            
            .form-input {
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 14px;
            }
            
            .form-select {
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 14px;
            }
            
            .form-checkbox-group {
                max-height: 150px;
                overflow-y: auto;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 10px;
                background-color: #333;
            }
            
            .checkbox-item {
                margin-bottom: 8px;
                display: flex;
                align-items: center;
            }
            
            .checkbox-input {
                margin-right: 8px;
            }
            
            .form-button {
                background-color: #FF6600;
                color: white;
                border: none;
                padding: 10px;
                width: 100%;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
                margin-top: 10px;
            }
            
            .form-button:hover {
                background-color: #FF7722;
            }
            
            .secondary-button {
                background-color: #555;
            }
            
            .secondary-button:hover {
                background-color: #666;
            }
            
            .upload-section {
                margin-top: 20px;
                padding-top: 15px;
                border-top: 1px solid #444;
            }
            
            .file-upload {
                margin-bottom: 10px;
            }
            
            .upload-label {
                display: block;
                margin-bottom: 8px;
                color: #CCC;
                font-size: 14px;
            }
            
            .main-area {
                flex: 1;
                padding: 20px;
                display: flex;
                flex-direction: column;
            }
            
            .main-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .main-title {
                font-size: 20px;
                font-weight: bold;
                color: #EEE;
            }
            
            .account-counter {
                font-size: 14px;
                color: #CCC;
            }
            
            .status-area {
                background-color: #252525;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 20px;
                border: 1px solid #444;
            }
            
            .status-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            
            .status-title {
                font-size: 16px;
                font-weight: bold;
                color: #EEE;
            }
            
            .status-actions {
                display: flex;
            }
            
            .status-button {
                padding: 5px 10px;
                background-color: #444;
                color: white;
                border: none;
                border-radius: 3px;
                margin-left: 10px;
                cursor: pointer;
                font-size: 12px;
            }
            
            .progress-container {
                width: 100%;
                height: 20px;
                background-color: #333;
                border-radius: 10px;
                margin-bottom: 10px;
                overflow: hidden;
            }
            
            .progress-bar {
                height: 100%;
                background-color: #FF6600;
                width: 35%;
            }
            
            .progress-stats {
                display: flex;
                justify-content: space-between;
                color: #CCC;
                font-size: 12px;
            }
            
            .logs-area {
                flex: 1;
                background-color: #252525;
                border-radius: 5px;
                border: 1px solid #444;
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }
            
            .logs-header {
                background-color: #333;
                padding: 10px 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #444;
            }
            
            .logs-title {
                font-size: 14px;
                font-weight: bold;
                color: #EEE;
            }
            
            .logs-actions {
                display: flex;
            }
            
            .logs-button {
                padding: 3px 8px;
                background-color: #444;
                color: white;
                border: none;
                border-radius: 3px;
                margin-left: 8px;
                cursor: pointer;
                font-size: 12px;
            }
            
            .logs-content {
                flex: 1;
                padding: 15px;
                overflow-y: auto;
                font-family: monospace;
                font-size: 12px;
                color: #CCC;
                background-color: #1A1A1A;
            }
            
            .log-entry {
                margin-bottom: 5px;
                padding-bottom: 5px;
                border-bottom: 1px solid #333;
            }
            
            .log-time {
                color: #888;
                margin-right: 10px;
            }
            
            .log-success {
                color: #5F5;
            }
            
            .log-error {
                color: #F55;
            }
            
            .log-warning {
                color: #FF5;
            }
            
            .app-footer {
                padding: 8px 15px;
                background-color: #252525;
                border-top: 1px solid #444;
                font-size: 12px;
                color: #888;
                text-align: center;
            }

            .state-filter {
                display: flex;
                margin-top: 15px;
                margin-bottom: 15px;
                align-items: center;
            }
            
            .state-filter-label {
                font-size: 14px;
                color: #CCC;
                margin-right: 10px;
            }
            
            .state-select {
                width: 100%;
                padding: 6px;
            }
            
            .file-input {
                width: 0.1px;
                height: 0.1px;
                opacity: 0;
                overflow: hidden;
                position: absolute;
                z-index: -1;
            }
            
            .file-label {
                display: inline-block;
                padding: 8px 12px;
                background-color: #444;
                color: white;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                margin-bottom: 8px;
            }
            
            .file-label:hover {
                background-color: #555;
            }
            
            .file-name {
                font-size: 12px;
                color: #CCC;
                margin-top: 5px;
                word-break: break-all;
            }
            
            .upload-note {
                font-size: 12px;
                color: #AAA;
                margin-top: 10px;
                line-height: 1.4;
            }
        </style>
    </head>
    <body>
        <div class="app-container">
            <div class="app-header">
                {% if logo_exists %}
                <img src="/static/progress_logo.png" alt="PB BETTING Logo" class="logo">
                {% endif %}
                {{ nav_menu|safe }}
            </div>
            
            <div class="app-content">
                <div class="sidebar">
                    <div class="section-title">Account Creation Settings</div>
                    
                    <div class="form-group">
                        <label class="form-label">Number of Accounts</label>
                        <input type="number" class="form-input" value="100" min="1" max="1000">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Area Code Preferences</label>
                        <div class="form-checkbox-group">
                            <div class="state-filter">
                                <label class="state-filter-label">Filter by State:</label>
                                <select class="form-select state-select">
                                    <option value="">All States</option>
                                    <option value="FL" selected>Florida</option>
                                    <option value="NY">New York</option>
                                    <option value="CA">California</option>
                                    <option value="TX">Texas</option>
                                    <option value="IL">Illinois</option>
                                </select>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" class="checkbox-input" id="area954" checked>
                                <label for="area954" class="checkbox-label">954 - Fort Lauderdale, FL</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" class="checkbox-input" id="area754" checked>
                                <label for="area754" class="checkbox-label">754 - Fort Lauderdale, FL</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" class="checkbox-input" id="area305" checked>
                                <label for="area305" class="checkbox-label">305 - Miami, FL</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" class="checkbox-input" id="area786" checked>
                                <label for="area786" class="checkbox-label">786 - Miami, FL</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" class="checkbox-input" id="area561" checked>
                                <label for="area561" class="checkbox-label">561 - West Palm Beach, FL</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" class="checkbox-input" id="area407">
                                <label for="area407" class="checkbox-label">407 - Orlando, FL</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" class="checkbox-input" id="area321">
                                <label for="area321" class="checkbox-label">321 - Orlando, FL</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" class="checkbox-input" id="area813">
                                <label for="area813" class="checkbox-label">813 - Tampa, FL</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" class="checkbox-input" id="area727">
                                <label for="area727" class="checkbox-label">727 - St. Petersburg, FL</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" class="checkbox-input" id="area239">
                                <label for="area239" class="checkbox-label">239 - Fort Myers, FL</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" class="checkbox-input" id="area904">
                                <label for="area904" class="checkbox-label">904 - Jacksonville, FL</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" class="checkbox-input" id="area850">
                                <label for="area850" class="checkbox-label">850 - Tallahassee, FL</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" class="checkbox-input" id="area386">
                                <label for="area386" class="checkbox-label">386 - Daytona Beach, FL</label>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Creation Method</label>
                        <select class="form-select">
                            <option>Standard (8 per hour)</option>
                            <option>Accelerated (20 per hour)</option>
                            <option selected>Maximum (40 per hour)</option>
                        </select>
                    </div>
                    
                    <div class="upload-section">
                        <div class="section-title">Custom Names & Usernames</div>
                        
                        <div class="file-upload">
                            <label class="upload-label">Names & Usernames File</label>
                            <input type="file" id="names-upload" class="file-input">
                            <label for="names-upload" class="file-label">Choose File</label>
                            <div class="file-name">ghost_names_usernames.csv (150 KB)</div>
                        </div>
                        
                        <div class="upload-note">
                            Upload a CSV, TXT, XLSX, or XLS file with names and usernames. If no file is provided, random names and usernames will be generated.
                        </div>
                    </div>
                    
                    <div class="upload-section">
                        <div class="section-title">Custom Voicemail</div>
                        
                        <div class="file-upload">
                            <label class="upload-label">Voicemail Files</label>
                            <input type="file" id="voicemail-upload" class="file-input" multiple accept="audio/*">
                            <label for="voicemail-upload" class="file-label">Choose Files</label>
                            <div class="file-name">5 files selected (2.3 MB)</div>
                        </div>
                        
                        <div class="upload-note">
                            Upload MP3 audio files for custom voicemail greetings. Multiple files will be randomly assigned to accounts. If no files are provided, default text-to-speech voicemails will be generated.
                        </div>
                    </div>
                    
                    <button class="form-button">Start Account Creation</button>
                    <button class="form-button secondary-button">Reset Settings</button>
                </div>
                
                <div class="main-area">
                    <div class="main-header">
                        <div class="main-title">Account Creation Status</div>
                        <div class="account-counter">5,219 accounts in database</div>
                    </div>
                    
                    <div class="status-area">
                        <div class="status-header">
                            <div class="status-title">Current Progress</div>
                            <div class="status-actions">
                                <button class="status-button">Pause</button>
                                <button class="status-button">Stop</button>
                            </div>
                        </div>
                        
                        <div class="progress-container">
                            <div class="progress-bar"></div>
                        </div>
                        
                        <div class="progress-stats">
                            <div>35 of 100 accounts created</div>
                            <div>ETA: 1h 37m remaining</div>
                            <div>Rate: 8 accounts/hour</div>
                        </div>
                    </div>
                    
                    <div class="logs-area">
                        <div class="logs-header">
                            <div class="logs-title">Creation Logs</div>
                            <div class="logs-actions">
                                <button class="logs-button">Clear</button>
                                <button class="logs-button">Export</button>
                            </div>
                        </div>
                        
                        <div class="logs-content">
                            <div class="log-entry">
                                <span class="log-time">[12:45:23]</span>
                                <span class="log-success">Created account: ghost_user_123 (954-555-1234)</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:45:18]</span>
                                <span>Assigning random voicemail to account</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:45:15]</span>
                                <span>Phone verification completed successfully</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:45:10]</span>
                                <span>Waiting for SMS verification code</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:45:08]</span>
                                <span>Generating new phone number in area code 954</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:45:05]</span>
                                <span>Submitting registration form</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:45:02]</span>
                                <span>Using credentials: ghost_user_123 / ********</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:45:00]</span>
                                <span>Starting account creation process for #35</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:44:03]</span>
                                <span class="log-success">Created account: phantom_754 (754-555-2345)</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:43:58]</span>
                                <span>Assigning random voicemail to account</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:43:55]</span>
                                <span>Phone verification completed successfully</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:43:51]</span>
                                <span class="log-warning">Verification code not received, retrying request</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:43:40]</span>
                                <span>Waiting for SMS verification code</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:43:38]</span>
                                <span>Generating new phone number in area code 754</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:43:35]</span>
                                <span>Submitting registration form</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:43:32]</span>
                                <span>Using credentials: phantom_754 / ********</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:43:30]</span>
                                <span>Starting account creation process for #34</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:42:23]</span>
                                <span class="log-error">Failed to create account: TextNow API error (429 Too Many Requests)</span>
                            </div>
                            <div class="log-entry">
                                <span class="log-time">[12:42:20]</span>
                                <span class="log-warning">Rate limit detected, pausing for 30 seconds</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="app-footer">
                © ProgressBets™ | TextNow v1.0.0 | 5 Accounts Active
            </div>
        </div>
    </body>
    </html>
    ''', logo_exists=os.path.exists("static/progress_logo.png"))

@app.route('/dashboard')
def dashboard_page():
    """The account management dashboard page"""
    process_assets()
    nav_menu = get_nav_menu('/dashboard')
    return render_template_string('''
    {{ nav_menu|safe }}
    <!DOCTYPE html>
    <html>
    <head>
        <title>ProgressGhostCreator - Dashboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-image: url('/static/progress_background.jpg');
                background-size: cover;
                background-position: center;
                color: white;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            
            .app-container {
                width: 1000px;
                height: 700px;
                background-color: rgba(30, 30, 30, 0.95);
                border-radius: 10px;
                box-shadow: 0 0 15px rgba(0,0,0,0.5);
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }
            
            .app-header {
                background-color: #FF6600;
                padding: 15px;
                text-align: center;
                border-bottom: 1px solid #333;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .logo {
                max-width: 150px;
                height: auto;
            }
            
            .nav-menu {
                display: flex;
            }
            
            .nav-button {
                background-color: #AA4400;
                color: white;
                border: none;
                padding: 8px 15px;
                margin-left: 10px;
                cursor: pointer;
                border-radius: 3px;
                font-weight: bold;
                text-decoration: none;
                font-size: 14px;
            }
            
            .nav-button:hover {
                background-color: #CC5500;
            }
            
            .active {
                background-color: #CC5500;
            }
            
            .app-content {
                display: flex;
                flex: 1;
                overflow: hidden;
            }
            
            .accounts-panel {
                width: 250px;
                background-color: #252525;
                border-right: 1px solid #444;
                display: flex;
                flex-direction: column;
            }
            
            .accounts-header {
                padding: 15px;
                border-bottom: 1px solid #444;
                font-weight: bold;
            }
            
            .accounts-search {
                padding: 10px;
                border-bottom: 1px solid #444;
            }
            
            .search-input {
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 12px;
            }
            
            .accounts-list {
                flex: 1;
                overflow-y: auto;
            }
            
            .account-item {
                padding: 12px 15px;
                border-bottom: 1px solid #444;
                cursor: pointer;
                display: flex;
                align-items: center;
            }
            
            .account-item:hover {
                background-color: #333;
            }
            
            .account-item.active {
                background-color: #3A3A3A;
            }
            
            .account-status {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                margin-right: 10px;
            }
            
            .status-active {
                background-color: #5F5;
            }
            
            .status-inactive {
                background-color: #F55;
            }
            
            .status-warning {
                background-color: #FF5;
            }
            
            .account-name {
                font-size: 13px;
                flex: 1;
            }
            
            .account-phone {
                color: #999;
                font-size: 12px;
            }
            
            .account-filters {
                padding: 10px;
                border-bottom: 1px solid #444;
                font-size: 12px;
            }
            
            .filter-group {
                margin-bottom: 8px;
            }
            
            .filter-label {
                display: block;
                margin-bottom: 3px;
                color: #CCC;
            }
            
            .filter-select {
                width: 100%;
                padding: 5px;
                border-radius: 3px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 12px;
            }
            
            .filter-actions {
                display: flex;
                justify-content: space-between;
                margin-top: 10px;
            }
            
            .filter-button {
                padding: 4px 8px;
                border: none;
                border-radius: 3px;
                background-color: #555;
                color: white;
                font-size: 11px;
                cursor: pointer;
            }
            
            .main-panel {
                flex: 1;
                display: flex;
                flex-direction: column;
            }
            
            .tabs {
                display: flex;
                background-color: #2A2A2A;
                border-bottom: 1px solid #444;
            }
            
            .tab {
                padding: 12px 20px;
                cursor: pointer;
                font-size: 14px;
                font-weight: bold;
                color: #CCC;
            }
            
            .tab:hover {
                background-color: #333;
            }
            
            .tab.active {
                background-color: #333;
                color: #FF6600;
                border-bottom: 2px solid #FF6600;
            }
            
            .tab-content {
                flex: 1;
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }
            
            .account-details {
                padding: 20px;
                overflow-y: auto;
            }
            
            .detail-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 20px;
            }
            
            .detail-title {
                font-size: 20px;
                font-weight: bold;
                color: #EEE;
            }
            
            .detail-phone {
                font-size: 16px;
                color: #CCC;
                margin-top: 5px;
            }
            
            .detail-actions {
                display: flex;
            }
            
            .detail-button {
                padding: 8px 12px;
                background-color: #555;
                color: white;
                border: none;
                border-radius: 4px;
                margin-left: 10px;
                cursor: pointer;
                font-size: 12px;
            }
            
            .detail-button.primary {
                background-color: #FF6600;
            }
            
            .detail-button.danger {
                background-color: #C33;
            }
            
            .detail-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }
            
            .detail-section {
                background-color: #333;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 15px;
            }
            
            .section-header {
                font-size: 16px;
                font-weight: bold;
                color: #EEE;
                margin-bottom: 10px;
                border-bottom: 1px solid #444;
                padding-bottom: 8px;
            }
            
            .account-info {
                display: grid;
                grid-template-columns: 120px 1fr;
                row-gap: 10px;
                font-size: 14px;
            }
            
            .info-label {
                color: #999;
            }
            
            .info-value {
                color: #EEE;
            }
            
            .health-info {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 10px;
            }
            
            .health-label {
                font-size: 14px;
                color: #CCC;
            }
            
            .health-bar-container {
                flex: 1;
                height: 12px;
                background-color: #444;
                border-radius: 6px;
                margin: 0 15px;
                overflow: hidden;
            }
            
            .health-bar {
                height: 100%;
                border-radius: 6px;
            }
            
            .health-value {
                font-size: 14px;
                font-weight: bold;
                width: 40px;
                text-align: right;
            }
            
            .health-excellent {
                background-color: #5F5;
                color: #5F5;
            }
            
            .health-good {
                background-color: #AFA;
                color: #AFA;
            }
            
            .health-fair {
                background-color: #FF5;
                color: #FF5;
            }
            
            .health-poor {
                background-color: #F55;
                color: #F55;
            }
            
            .stats-row {
                display: flex;
                justify-content: space-between;
                margin-bottom: 15px;
            }
            
            .stat-box {
                background-color: #2A2A2A;
                border-radius: 5px;
                padding: 15px;
                flex: 1;
                margin: 0 5px;
                text-align: center;
            }
            
            .stat-value {
                font-size: 24px;
                font-weight: bold;
                color: #FF6600;
                margin-bottom: 5px;
            }
            
            .stat-label {
                font-size: 12px;
                color: #AAA;
            }
            
            .quick-send {
                display: grid;
                grid-template-columns: 1fr auto;
                gap: 10px;
                margin-top: 15px;
            }
            
            .quick-send-input {
                padding: 10px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #2A2A2A;
                color: #EEE;
                font-size: 14px;
                resize: none;
            }
            
            .quick-send-button {
                padding: 10px 15px;
                background-color: #FF6600;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
                align-self: flex-end;
            }
            
            .message-history {
                display: flex;
                flex-direction: column;
                padding: 20px;
                flex: 1;
                overflow-y: auto;
            }
            
            .message-date {
                text-align: center;
                color: #999;
                font-size: 12px;
                margin: 15px 0;
                position: relative;
            }
            
            .message-date::before,
            .message-date::after {
                content: "";
                position: absolute;
                height: 1px;
                background-color: #444;
                top: 50%;
                width: 40%;
            }
            
            .message-date::before {
                left: 0;
            }
            
            .message-date::after {
                right: 0;
            }
            
            .message-group {
                margin-bottom: 15px;
            }
            
            .message-bubble {
                max-width: 70%;
                padding: 10px 15px;
                border-radius: 18px;
                margin-bottom: 5px;
                position: relative;
                line-height: 1.4;
            }
            
            .message-incoming {
                align-self: flex-start;
                background-color: #2A2A2A;
                border-bottom-left-radius: 5px;
                margin-right: auto;
            }
            
            .message-outgoing {
                align-self: flex-end;
                background-color: #0B93F6;
                border-bottom-right-radius: 5px;
                margin-left: auto;
            }
            
            .message-time {
                font-size: 11px;
                color: #999;
                margin-top: 5px;
                text-align: right;
            }
            
            .compose-area {
                padding: 15px;
                background-color: #2A2A2A;
                border-top: 1px solid #444;
                display: flex;
                align-items: flex-end;
            }
            
            .compose-input {
                flex: 1;
                padding: 12px;
                border-radius: 20px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 14px;
                resize: none;
                min-height: 20px;
                max-height: 100px;
            }
            
            .compose-button {
                background-color: #FF6600;
                color: white;
                border: none;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                margin-left: 10px;
                cursor: pointer;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 18px;
            }
            
            .account-history {
                padding: 20px;
                overflow-y: auto;
            }
            
            .history-filters {
                display: flex;
                margin-bottom: 20px;
                gap: 15px;
            }
            
            .history-filter {
                padding: 8px 15px;
                background-color: #333;
                border-radius: 20px;
                font-size: 13px;
                cursor: pointer;
            }
            
            .history-filter.active {
                background-color: #FF6600;
                color: white;
            }
            
            .history-item {
                background-color: #2A2A2A;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
            }
            
            .history-icon {
                width: 40px;
                height: 40px;
                background-color: #333;
                border-radius: 50%;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 20px;
                margin-right: 15px;
                flex-shrink: 0;
            }
            
            .history-icon.messages {
                color: #0B93F6;
            }
            
            .history-icon.login {
                color: #5F5;
            }
            
            .history-icon.voicemail {
                color: #F55;
            }
            
            .history-icon.update {
                color: #FF5;
            }
            
            .history-content {
                flex: 1;
            }
            
            .history-title {
                font-size: 14px;
                font-weight: bold;
                color: #EEE;
                margin-bottom: 5px;
            }
            
            .history-details {
                font-size: 13px;
                color: #AAA;
            }
            
            .history-time {
                font-size: 12px;
                color: #777;
                white-space: nowrap;
                margin-left: 15px;
            }
            
            .app-footer {
                padding: 8px 15px;
                background-color: #252525;
                border-top: 1px solid #444;
                font-size: 12px;
                color: #888;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="app-container">
            <div class="app-header">
                {% if logo_exists %}
                <img src="/static/progress_logo.png" alt="PB BETTING Logo" class="logo">
                {% endif %}
                {{ nav_menu|safe }}
            </div>
            
            <div class="app-content">
                <div class="accounts-panel">
                    <div class="accounts-header">
                        Account Manager (5,219)
                    </div>
                    
                    <div class="accounts-filters">
                        <div class="filter-group">
                            <label class="filter-label">Status</label>
                            <select class="filter-select">
                                <option>All Status</option>
                                <option>Active</option>
                                <option>Inactive</option>
                                <option>Warning</option>
                            </select>
                        </div>
                        
                        <div class="filter-group">
                            <label class="filter-label">Area Code</label>
                            <select class="filter-select">
                                <option>All Area Codes</option>
                                <option>954 - Fort Lauderdale</option>
                                <option>754 - Fort Lauderdale</option>
                                <option>305 - Miami</option>
                                <option>786 - Miami</option>
                                <option>561 - West Palm Beach</option>
                            </select>
                        </div>
                        
                        <div class="filter-group">
                            <label class="filter-label">Health Score</label>
                            <select class="filter-select">
                                <option>All Scores</option>
                                <option>Excellent (90-100)</option>
                                <option>Good (70-89)</option>
                                <option>Fair (40-69)</option>
                                <option>Poor (0-39)</option>
                            </select>
                        </div>
                        
                        <div class="filter-actions">
                            <button class="filter-button">Apply</button>
                            <button class="filter-button">Reset</button>
                        </div>
                    </div>
                    
                    <div class="accounts-search">
                        <input type="text" class="search-input" placeholder="Search accounts...">
                    </div>
                    
                    <div class="accounts-list">
                        <div class="account-item active">
                            <div class="account-status status-active"></div>
                            <div class="account-name">ghost_user_123</div>
                            <div class="account-phone">(954) 555-1234</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-active"></div>
                            <div class="account-name">phantom_754</div>
                            <div class="account-phone">(754) 555-2345</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-active"></div>
                            <div class="account-name">shadow_play_305</div>
                            <div class="account-phone">(305) 555-3456</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-warning"></div>
                            <div class="account-name">stealth_786</div>
                            <div class="account-phone">(786) 555-4567</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-active"></div>
                            <div class="account-name">ghost_561</div>
                            <div class="account-phone">(561) 555-5678</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-inactive"></div>
                            <div class="account-name">shadow_904</div>
                            <div class="account-phone">(904) 555-6789</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-active"></div>
                            <div class="account-name">phantom_850</div>
                            <div class="account-phone">(850) 555-7890</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-active"></div>
                            <div class="account-name">ghost_386</div>
                            <div class="account-phone">(386) 555-8901</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-active"></div>
                            <div class="account-name">stealth_user_407</div>
                            <div class="account-phone">(407) 555-9012</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-warning"></div>
                            <div class="account-name">shadow_321</div>
                            <div class="account-phone">(321) 555-0123</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-active"></div>
                            <div class="account-name">ghost_813</div>
                            <div class="account-phone">(813) 555-1234</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-active"></div>
                            <div class="account-name">phantom_727</div>
                            <div class="account-phone">(727) 555-2345</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-inactive"></div>
                            <div class="account-name">shadow_239</div>
                            <div class="account-phone">(239) 555-3456</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-active"></div>
                            <div class="account-name">stealth_username1</div>
                            <div class="account-phone">(954) 555-4567</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-warning"></div>
                            <div class="account-name">ghost_profile2</div>
                            <div class="account-phone">(754) 555-5678</div>
                        </div>
                    </div>
                </div>
                
                <div class="main-panel">
                    <div class="tabs">
                        <div class="tab active">Account Details</div>
                        <div class="tab">Messaging</div>
                        <div class="tab">History</div>
                    </div>
                    
                    <div class="tab-content">
                        <div class="account-details">
                            <div class="detail-header">
                                <div>
                                    <div class="detail-title">ghost_user_123</div>
                                    <div class="detail-phone">(954) 555-1234</div>
                                </div>
                                <div class="detail-actions">
                                    <button class="detail-button">Refresh</button>
                                    <button class="detail-button primary">Login</button>
                                    <button class="detail-button danger">Delete</button>
                                </div>
                            </div>
                            
                            <div class="detail-grid">
                                <div class="detail-section">
                                    <div class="section-header">Account Information</div>
                                    <div class="account-info">
                                        <div class="info-label">Created Date:</div>
                                        <div class="info-value">March 15, 2024</div>
                                        
                                        <div class="info-label">Status:</div>
                                        <div class="info-value">Active</div>
                                        
                                        <div class="info-label">Email:</div>
                                        <div class="info-value">ghost123@mailinator.com</div>
                                        
                                        <div class="info-label">Display Name:</div>
                                        <div class="info-value">Ghost User</div>
                                        
                                        <div class="info-label">Area Code:</div>
                                        <div class="info-value">954 (Fort Lauderdale, FL)</div>
                                        
                                        <div class="info-label">Last Login:</div>
                                        <div class="info-value">Today, 11:23 AM</div>
                                    </div>
                                </div>
                                
                                <div class="detail-section">
                                    <div class="section-header">Account Health</div>
                                    <div class="health-info">
                                        <div class="health-label">Overall Score:</div>
                                        <div class="health-bar-container">
                                            <div class="health-bar health-excellent" style="width: 95%;"></div>
                                        </div>
                                        <div class="health-value health-excellent">95%</div>
                                    </div>
                                    
                                    <div class="health-info">
                                        <div class="health-label">Message Delivery:</div>
                                        <div class="health-bar-container">
                                            <div class="health-bar health-excellent" style="width: 98%;"></div>
                                        </div>
                                        <div class="health-value health-excellent">98%</div>
                                    </div>
                                    
                                    <div class="health-info">
                                        <div class="health-label">Account Activity:</div>
                                        <div class="health-bar-container">
                                            <div class="health-bar health-good" style="width: 85%;"></div>
                                        </div>
                                        <div class="health-value health-good">85%</div>
                                    </div>
                                    
                                    <div class="health-info">
                                        <div class="health-label">API Responses:</div>
                                        <div class="health-bar-container">
                                            <div class="health-bar health-excellent" style="width: 100%;"></div>
                                        </div>
                                        <div class="health-value health-excellent">100%</div>
                                    </div>
                                    
                                    <div class="health-info">
                                        <div class="health-label">Authentication:</div>
                                        <div class="health-bar-container">
                                            <div class="health-bar health-excellent" style="width: 95%;"></div>
                                        </div>
                                        <div class="health-value health-excellent">95%</div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="detail-section">
                                <div class="section-header">Account Statistics</div>
                                <div class="stats-row">
                                    <div class="stat-box">
                                        <div class="stat-value">324</div>
                                        <div class="stat-label">Messages Sent</div>
                                    </div>
                                    <div class="stat-box">
                                        <div class="stat-value">156</div>
                                        <div class="stat-label">Messages Received</div>
                                    </div>
                                    <div class="stat-box">
                                        <div class="stat-value">48</div>
                                        <div class="stat-label">Days Active</div>
                                    </div>
                                    <div class="stat-box">
                                        <div class="stat-value">3</div>
                                        <div class="stat-label">Current Campaigns</div>
                                    </div>
                                </div>
                                
                                <div class="quick-send">
                                    <textarea class="quick-send-input" placeholder="Type a message to send..."></textarea>
                                    <button class="quick-send-button">Send</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="app-footer">
                © ProgressBets™ | TextNow v1.0.0 | 5 Accounts Active
            </div>
        </div>
    </body>
    </html>
    ''', logo_exists=os.path.exists("static/progress_logo.png"))

@app.route('/campaigns')
def campaigns_page():
    """The campaigns management page"""
    process_assets()
    nav_menu = get_nav_menu('/campaigns')
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ProgressGhostCreator - Campaigns</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-image: url('/static/progress_background.jpg');
                background-size: cover;
                background-position: center;
                color: white;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            
            .app-container {
                width: 1000px;
                height: 700px;
                background-color: rgba(30, 30, 30, 0.95);
                border-radius: 10px;
                box-shadow: 0 0 15px rgba(0,0,0,0.5);
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }
            
            .app-header {
                background-color: #FF6600;
                padding: 15px;
                text-align: center;
                border-bottom: 1px solid #333;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .logo {
                max-width: 150px;
                height: auto;
            }
            
            .nav-menu {
                display: flex;
            }
            
            .nav-button {
                background-color: #AA4400;
                color: white;
                border: none;
                padding: 8px 15px;
                margin-left: 10px;
                cursor: pointer;
                border-radius: 3px;
                font-weight: bold;
                text-decoration: none;
                font-size: 14px;
            }
            
            .nav-button:hover {
                background-color: #CC5500;
            }
            
            .active {
                background-color: #CC5500;
            }
            
            .app-content {
                display: flex;
                flex: 1;
                overflow: hidden;
            }
            
            .campaigns-sidebar {
                width: 250px;
                background-color: #252525;
                border-right: 1px solid #444;
                display: flex;
                flex-direction: column;
            }
            
            .sidebar-header {
                padding: 15px;
                border-bottom: 1px solid #444;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .sidebar-title {
                font-weight: bold;
                font-size: 16px;
            }
            
            .add-button {
                background-color: #FF6600;
                color: white;
                border: none;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 20px;
                line-height: 1;
                cursor: pointer;
            }
            
            .campaign-filters {
                padding: 10px;
                border-bottom: 1px solid #444;
            }
            
            .filter-input {
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 12px;
                margin-bottom: 10px;
            }
            
            .filter-select {
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 12px;
            }
            
            .campaign-list {
                flex: 1;
                overflow-y: auto;
            }
            
            .campaign-item {
                padding: 12px 15px;
                border-bottom: 1px solid #444;
                cursor: pointer;
            }
            
            .campaign-item:hover {
                background-color: #333;
            }
            
            .campaign-item.active {
                background-color: #3A3A3A;
            }
            
            .campaign-name {
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .campaign-status {
                display: flex;
                align-items: center;
                font-size: 12px;
                color: #CCC;
            }
            
            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                margin-right: 8px;
            }
            
            .status-active {
                background-color: #5F5;
            }
            
            .status-paused {
                background-color: #FF5;
            }
            
            .status-draft {
                background-color: #AAA;
            }
            
            .status-completed {
                background-color: #55F;
            }
            
            .status-failed {
                background-color: #F55;
            }
            
            .campaign-meta {
                display: flex;
                justify-content: space-between;
                font-size: 11px;
                color: #888;
                margin-top: 5px;
            }
            
            .main-content {
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .content-header {
                padding: 15px 20px;
                border-bottom: 1px solid #444;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .campaign-title {
                font-size: 18px;
                font-weight: bold;
            }
            
            .header-actions {
                display: flex;
            }
            
            .header-button {
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                margin-left: 10px;
                cursor: pointer;
                font-size: 13px;
                display: flex;
                align-items: center;
            }
            
            .header-button svg {
                margin-right: 5px;
            }
            
            .primary-button {
                background-color: #FF6600;
                color: white;
            }
            
            .secondary-button {
                background-color: #555;
                color: white;
            }
            
            .danger-button {
                background-color: #C33;
                color: white;
            }
            
            .tabs-container {
                background-color: #2A2A2A;
                display: flex;
                border-bottom: 1px solid #444;
            }
            
            .tab {
                padding: 12px 20px;
                cursor: pointer;
                font-size: 14px;
                font-weight: bold;
                color: #CCC;
            }
            
            .tab:hover {
                background-color: #333;
            }
            
            .tab.active {
                background-color: #333;
                color: #FF6600;
                border-bottom: 2px solid #FF6600;
            }
            
            .tab-content {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
            }
            
            .overview-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .overview-card {
                background-color: #333;
                border-radius: 5px;
                padding: 15px;
                display: flex;
                flex-direction: column;
            }
            
            .card-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 10px;
            }
            
            .card-title {
                font-size: 14px;
                color: #CCC;
            }
            
            .card-value {
                font-size: 24px;
                font-weight: bold;
                color: #FF6600;
            }
            
            .card-footer {
                font-size: 12px;
                color: #AAA;
                margin-top: auto;
                padding-top: 10px;
            }
            
            .progress-container {
                width: 100%;
                height: 10px;
                background-color: #444;
                border-radius: 5px;
                overflow: hidden;
                margin-top: 5px;
            }
            
            .progress-bar {
                height: 100%;
                background-color: #FF6600;
            }
            
            .stats-container {
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .stats-card {
                background-color: #333;
                border-radius: 5px;
                padding: 15px;
                flex: 1;
            }
            
            .stats-header {
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 15px;
                color: #EEE;
                border-bottom: 1px solid #444;
                padding-bottom: 8px;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
            }
            
            .stat-item {
                display: flex;
                flex-direction: column;
            }
            
            .stat-value {
                font-size: 18px;
                font-weight: bold;
                color: #EEE;
            }
            
            .stat-label {
                font-size: 12px;
                color: #AAA;
                margin-top: 5px;
            }
            
            .conversion-chart {
                background-color: #333;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 20px;
            }
            
            .chart-header {
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 15px;
                color: #EEE;
                border-bottom: 1px solid #444;
                padding-bottom: 8px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .chart-filter {
                font-size: 12px;
                font-weight: normal;
                color: #CCC;
            }
            
            .chart-content {
                height: 200px;
                display: flex;
                align-items: flex-end;
                padding-top: 20px;
                position: relative;
                border-bottom: 1px solid #444;
                margin-bottom: 10px;
            }
            
            .chart-bar {
                flex: 1;
                background-color: #FF6600;
                margin: 0 2px;
                position: relative;
            }
            
            .chart-labels {
                display: flex;
                justify-content: space-between;
                font-size: 11px;
                color: #AAA;
                padding-top: 5px;
            }
            
            .settings-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }
            
            .settings-card {
                background-color: #333;
                border-radius: 5px;
                padding: 15px;
            }
            
            .settings-header {
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 15px;
                color: #EEE;
                border-bottom: 1px solid #444;
                padding-bottom: 8px;
            }
            
            .settings-row {
                margin-bottom: 15px;
            }
            
            .setting-label {
                font-size: 14px;
                color: #CCC;
                margin-bottom: 5px;
                display: block;
            }
            
            .setting-input {
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #222;
                color: #EEE;
                font-size: 14px;
            }
            
            .setting-textarea {
                width: 100%;
                height: 100px;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #222;
                color: #EEE;
                font-size: 14px;
                resize: none;
            }
            
            .setting-select {
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #222;
                color: #EEE;
                font-size: 14px;
            }
            
            .checkbox-group {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 10px;
            }
            
            .checkbox-item {
                display: flex;
                align-items: center;
            }
            
            .checkbox-input {
                margin-right: 5px;
            }
            
            .settings-actions {
                display: flex;
                justify-content: flex-end;
                margin-top: 20px;
            }
            
            .app-footer {
                padding: 8px 15px;
                background-color: #252525;
                border-top: 1px solid #444;
                font-size: 12px;
                color: #888;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="app-container">
            <div class="app-header">
                {% if logo_exists %}
                <img src="/static/progress_logo.png" alt="PB BETTING Logo" class="logo">
                {% endif %}
                {{ nav_menu|safe }}
            </div>
            
            <div class="app-content">
                <div class="campaigns-sidebar">
                    <div class="sidebar-header">
                        <div class="sidebar-title">Campaigns</div>
                        <div class="add-button">+</div>
                    </div>
                    
                    <div class="campaign-filters">
                        <input type="text" class="filter-input" placeholder="Search campaigns...">
                        <select class="filter-select">
                            <option>All Statuses</option>
                            <option>Active</option>
                            <option>Paused</option>
                            <option>Draft</option>
                            <option>Completed</option>
                        </select>
                    </div>
                    
                    <div class="campaign-list">
                        <div class="campaign-item active">
                            <div class="campaign-name">March Madness Promotion</div>
                            <div class="campaign-status">
                                <div class="status-dot status-active"></div>
                                Active
                            </div>
                            <div class="campaign-meta">
                                <div>35% Complete</div>
                                <div>3,500 / 10,000</div>
                            </div>
                        </div>
                        
                        <div class="campaign-item">
                            <div class="campaign-name">Weekly Sports Update</div>
                            <div class="campaign-status">
                                <div class="status-dot status-paused"></div>
                                Paused
                            </div>
                            <div class="campaign-meta">
                                <div>68% Complete</div>
                                <div>6,800 / 10,000</div>
                            </div>
                        </div>
                        
                        <div class="campaign-item">
                            <div class="campaign-name">NBA Finals Promotion</div>
                            <div class="campaign-status">
                                <div class="status-dot status-draft"></div>
                                Draft
                            </div>
                            <div class="campaign-meta">
                                <div>Starting June 1</div>
                                <div>0 / 25,000</div>
                            </div>
                        </div>
                        
                        <div class="campaign-item">
                            <div class="campaign-name">Super Bowl LVIII Campaign</div>
                            <div class="campaign-status">
                                <div class="status-dot status-completed"></div>
                                Completed
                            </div>
                            <div class="campaign-meta">
                                <div>100% Complete</div>
                                <div>15,000 / 15,000</div>
                            </div>
                        </div>
                        
                        <div class="campaign-item">
                            <div class="campaign-name">January Welcome Offer</div>
                            <div class="campaign-status">
                                <div class="status-dot status-completed"></div>
                                Completed
                            </div>
                            <div class="campaign-meta">
                                <div>100% Complete</div>
                                <div>5,000 / 5,000</div>
                            </div>
                        </div>
                        
                        <div class="campaign-item">
                            <div class="campaign-name">Holiday Special 2023</div>
                            <div class="campaign-status">
                                <div class="status-dot status-completed"></div>
                                Completed
                            </div>
                            <div class="campaign-meta">
                                <div>100% Complete</div>
                                <div>12,000 / 12,000</div>
                            </div>
                        </div>
                        
                        <div class="campaign-item">
                            <div class="campaign-name">Black Friday Deals</div>
                            <div class="campaign-status">
                                <div class="status-dot status-completed"></div>
                                Completed
                            </div>
                            <div class="campaign-meta">
                                <div>100% Complete</div>
                                <div>8,500 / 8,500</div>
                            </div>
                        </div>
                        
                        <div class="campaign-item">
                            <div class="campaign-name">Florida Football Season</div>
                            <div class="campaign-status">
                                <div class="status-dot status-failed"></div>
                                Failed
                            </div>
                            <div class="campaign-meta">
                                <div>32% Complete</div>
                                <div>3,200 / 10,000</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="main-content">
                    <div class="content-header">
                        <div class="campaign-title">March Madness Promotion</div>
                        <div class="header-actions">
                            <button class="header-button secondary-button">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                                Edit
                            </button>
                            <button class="header-button secondary-button">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="12" x2="15" y2="12"></line></svg>
                                Pause
                            </button>
                            <a href="/campaign_schedule" class="header-button primary-button">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                                Schedule
                            </a>
                        </div>
                    </div>
                    
                    <div class="tabs-container">
                        <div class="tab active">Overview</div>
                        <div class="tab">Settings</div>
                        <div class="tab">Accounts</div>
                        <div class="tab">Messages</div>
                        <div class="tab">Reports</div>
                    </div>
                    
                    <div class="tab-content">
                        <div class="overview-grid">
                            <div class="overview-card">
                                <div class="card-header">
                                    <div class="card-title">Progress</div>
                                </div>
                                <div class="card-value">35%</div>
                                <div class="progress-container">
                                    <div class="progress-bar" style="width: 35%;"></div>
                                </div>
                                <div class="card-footer">3,500 of 10,000 messages sent</div>
                            </div>
                            
                            <div class="overview-card">
                                <div class="card-header">
                                    <div class="card-title">Delivery Rate</div>
                                </div>
                                <div class="card-value">98.7%</div>
                                <div class="card-footer">3,455 delivered of 3,500 sent</div>
                            </div>
                            
                            <div class="overview-card">
                                <div class="card-header">
                                    <div class="card-title">Response Rate</div>
                                </div>
                                <div class="card-value">12.8%</div>
                                <div class="card-footer">442 responses from 3,455 delivered</div>
                            </div>
                        </div>
                        
                        <div class="stats-container">
                            <div class="stats-card">
                                <div class="stats-header">Campaign Performance</div>
                                <div class="stats-grid">
                                    <div class="stat-item">
                                        <div class="stat-value">10,000</div>
                                        <div class="stat-label">Target Messages</div>
                                    </div>
                                    
                                    <div class="stat-item">
                                        <div class="stat-value">3,500</div>
                                        <div class="stat-label">Messages Sent</div>
                                    </div>
                                    
                                    <div class="stat-item">
                                        <div class="stat-value">32</div>
                                        <div class="stat-label">Accounts Used</div>
                                    </div>
                                    
                                    <div class="stat-item">
                                        <div class="stat-value">109</div>
                                        <div class="stat-label">Avg. Per Account</div>
                                    </div>
                                    
                                    <div class="stat-item">
                                        <div class="stat-value">45</div>
                                        <div class="stat-label">Blocked Messages</div>
                                    </div>
                                    
                                    <div class="stat-item">
                                        <div class="stat-value">23</div>
                                        <div class="stat-label">Opt-Outs</div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="stats-card">
                                <div class="stats-header">Time Metrics</div>
                                <div class="stats-grid">
                                    <div class="stat-item">
                                        <div class="stat-value">Mar 15</div>
                                        <div class="stat-label">Start Date</div>
                                    </div>
                                    
                                    <div class="stat-item">
                                        <div class="stat-value">Mar 31</div>
                                        <div class="stat-label">End Date (Est.)</div>
                                    </div>
                                    
                                    <div class="stat-item">
                                        <div class="stat-value">8am-8pm</div>
                                        <div class="stat-label">Active Hours</div>
                                    </div>
                                    
                                    <div class="stat-item">
                                        <div class="stat-value">All</div>
                                        <div class="stat-label">Active Days</div>
                                    </div>
                                    
                                    <div class="stat-item">
                                        <div class="stat-value">583</div>
                                        <div class="stat-label">Messages/Day</div>
                                    </div>
                                    
                                    <div class="stat-item">
                                        <div class="stat-value">48</div>
                                        <div class="stat-label">Messages/Hour</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="conversion-chart">
                            <div class="chart-header">
                                Message Response Distribution
                                <div class="chart-filter">
                                    <select style="background: transparent; border: none; color: #CCC; font-size: 12px;">
                                        <option>Last 7 Days</option>
                                        <option>Last 30 Days</option>
                                        <option>All Time</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="chart-content">
                                <div class="chart-bar" style="height: 35%;"></div>
                                <div class="chart-bar" style="height: 65%;"></div>
                                <div class="chart-bar" style="height: 45%;"></div>
                                <div class="chart-bar" style="height: 80%;"></div>
                                <div class="chart-bar" style="height: 55%;"></div>
                                <div class="chart-bar" style="height: 40%;"></div>
                                <div class="chart-bar" style="height: 70%;"></div>
                            </div>
                            
                            <div class="chart-labels">
                                <div>Mar 15</div>
                                <div>Mar 16</div>
                                <div>Mar 17</div>
                                <div>Mar 18</div>
                                <div>Mar 19</div>
                                <div>Mar 20</div>
                                <div>Mar 21</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="app-footer">
                © ProgressBets™ | TextNow v1.0.0 | 5 Accounts Active
            </div>
        </div>
    </body>
    </html>
    ''', logo_exists=os.path.exists("static/progress_logo.png"))

@app.route('/message-dashboard')
def message_dashboard_route():
    """The message monitoring dashboard interface"""
    process_assets()
    nav_menu = get_nav_menu('/message-dashboard')
    from message_dashboard import message_dashboard_page
    return message_dashboard_page(logo_exists=os.path.exists("static/progress_logo.png"), nav_menu=nav_menu)

@app.route('/image-dashboard')
def image_dashboard_route():
    """The image management dashboard interface"""
    process_assets()
    nav_menu = get_nav_menu('/image-dashboard')
    return render_template_string(''' HTML template for image dashboard ''', logo_exists=os.path.exists("static/progress_logo.png"), nav_menu=nav_menu)

@app.route('/account-health')
def account_health_route():
    """The account health monitoring dashboard interface"""
    process_assets()
    nav_menu = get_nav_menu('/account-health')
    from account_health_dashboard import account_health_dashboard_page
    return account_health_dashboard_page(logo_exists=os.path.exists("static/progress_logo.png"), nav_menu=nav_menu)

@app.route('/voicemail-manager')
def voicemail_manager_route():
    """The voicemail management interface"""
    process_assets()
    nav_menu = get_nav_menu('/voicemail-manager')
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ProgressGhostCreator - Voicemail Manager</title>
        <style>
            /* CSS styles similar to other pages */
            body {
                font-family: Arial, sans-serif;
                background-image: url('/static/progress_background.jpg');
                background-size: cover;
                background-position: center;
                color: white;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            
            .app-container {
                width: 1000px;
                height: 700px;
                background-color: rgba(30, 30, 30, 0.95);
                border-radius: 10px;
                box-shadow: 0 0 15px rgba(0,0,0,0.5);
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }
            
            .app-header {
                background-color: #FF6600;
                padding: 15px;
                text-align: center;
                border-bottom: 1px solid #333;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .logo {
                max-width: 150px;
                height: auto;
            }
            
            .nav-menu {
                display: flex;
            }
            
            .nav-button {
                background-color: #AA4400;
                color: white;
                border: none;
                padding: 8px 15px;
                margin-left: 10px;
                cursor: pointer;
                border-radius: 3px;
                font-weight: bold;
                text-decoration: none;
                font-size: 14px;
            }
            
            .nav-button:hover {
                background-color: #CC5500;
            }
            
            .active {
                background-color: #CC5500;
            }
            
            .app-content {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
            }
            
            .app-footer {
                padding: 8px 15px;
                background-color: #252525;
                border-top: 1px solid #444;
                font-size: 12px;
                color: #888;
                text-align: center;
            }
            
            .page-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .page-title {
                font-size: 24px;
                font-weight: bold;
                color: #FF6600;
            }
            
            .action-buttons {
                display: flex;
                gap: 10px;
            }
            
            .button {
                background-color: #FF6600;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
                font-size: 14px;
            }
            
            .secondary-button {
                background-color: #555;
            }
            
            .content-area {
                display: flex;
                gap: 20px;
                height: calc(100% - 60px);
            }
            
            .left-panel {
                flex: 1;
                background-color: #252525;
                border-radius: 5px;
                border: 1px solid #444;
                padding: 15px;
                display: flex;
                flex-direction: column;
            }
            
            .right-panel {
                flex: 1;
                background-color: #252525;
                border-radius: 5px;
                border: 1px solid #444;
                padding: 15px;
                display: flex;
                flex-direction: column;
            }
            
            .panel-header {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 1px solid #444;
            }
            
            .voicemail-list {
                flex: 1;
                overflow-y: auto;
            }
            
            .voicemail-item {
                padding: 10px;
                border-bottom: 1px solid #444;
                display: flex;
                align-items: center;
                cursor: pointer;
            }
            
            .voicemail-item:hover {
                background-color: #333;
            }
            
            .voicemail-info {
                flex: 1;
            }
            
            .voicemail-name {
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .voicemail-meta {
                font-size: 12px;
                color: #999;
            }
            
            .voicemail-controls {
                display: flex;
                gap: 5px;
            }
            
            .control-button {
                width: 24px;
                height: 24px;
                background-color: #444;
                border-radius: 50%;
                border: none;
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                cursor: pointer;
                font-size: 12px;
            }
            
            .tts-form {
                margin-top: 15px;
            }
            
            .form-label {
                display: block;
                margin-bottom: 5px;
                color: #CCC;
            }
            
            .form-input {
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                margin-bottom: 10px;
            }
            
            .form-textarea {
                width: 100%;
                height: 100px;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                resize: vertical;
                margin-bottom: 15px;
            }
            
            .form-select {
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                margin-bottom: 15px;
            }
            
            .player-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                flex: 1;
                padding: 20px;
            }
            
            .player-waveform {
                width: 100%;
                height: 100px;
                background-color: #333;
                border-radius: 5px;
                margin-bottom: 20px;
                position: relative;
            }
            
            .player-controls {
                display: flex;
                gap: 10px;
            }
            
            .file-input {
                width: 0.1px;
                height: 0.1px;
                opacity: 0;
                overflow: hidden;
                position: absolute;
                z-index: -1;
            }
            
            .file-label {
                display: inline-block;
                padding: 8px 12px;
                background-color: #444;
                color: white;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                margin-bottom: 15px;
                width: 100%;
                text-align: center;
            }
            
            .file-label:hover {
                background-color: #555;
            }
        </style>
    </head>
    <body>
        <div class="app-container">
            <div class="app-header">
                {% if logo_exists %}
                <img src="/static/progress_logo.png" alt="PB BETTING Logo" class="logo">
                {% endif %}
                {{ nav_menu|safe }}
            </div>
            
            <div class="app-content">
                <div class="page-header">
                    <div class="page-title">Voicemail Manager</div>
                    <div class="action-buttons">
                        <button class="button secondary-button">Import Voicemails</button>
                        <button class="button">Generate New</button>
                    </div>
                </div>
                
                <div class="content-area">
                    <div class="left-panel">
                        <div class="panel-header">Voicemail Library</div>
                        <div class="voicemail-list">
                            <div class="voicemail-item">
                                <div class="voicemail-info">
                                    <div class="voicemail-name">Business Greeting 1</div>
                                    <div class="voicemail-meta">Duration: 0:18 | Used: 12 times</div>
                                </div>
                                <div class="voicemail-controls">
                                    <button class="control-button">▶</button>
                                    <button class="control-button">✓</button>
                                </div>
                            </div>
                            <div class="voicemail-item">
                                <div class="voicemail-info">
                                    <div class="voicemail-name">Professional Female</div>
                                    <div class="voicemail-meta">Duration: 0:22 | Used: 8 times</div>
                                </div>
                                <div class="voicemail-controls">
                                    <button class="control-button">▶</button>
                                    <button class="control-button">✓</button>
                                </div>
                            </div>
                            <div class="voicemail-item">
                                <div class="voicemail-info">
                                    <div class="voicemail-name">Casual Male</div>
                                    <div class="voicemail-meta">Duration: 0:15 | Used: 15 times</div>
                                </div>
                                <div class="voicemail-controls">
                                    <button class="control-button">▶</button>
                                    <button class="control-button">✓</button>
                                </div>
                            </div>
                            <div class="voicemail-item">
                                <div class="voicemail-info">
                                    <div class="voicemail-name">Customer Service</div>
                                    <div class="voicemail-meta">Duration: 0:20 | Used: 5 times</div>
                                </div>
                                <div class="voicemail-controls">
                                    <button class="control-button">▶</button>
                                    <button class="control-button">✓</button>
                                </div>
                            </div>
                            <div class="voicemail-item">
                                <div class="voicemail-info">
                                    <div class="voicemail-name">Friendly Female</div>
                                    <div class="voicemail-meta">Duration: 0:19 | Used: 10 times</div>
                                </div>
                                <div class="voicemail-controls">
                                    <button class="control-button">▶</button>
                                    <button class="control-button">✓</button>
                                </div>
                            </div>
                            <div class="voicemail-item">
                                <div class="voicemail-info">
                                    <div class="voicemail-name">Short Business</div>
                                    <div class="voicemail-meta">Duration: 0:12 | Used: 7 times</div>
                                </div>
                                <div class="voicemail-controls">
                                    <button class="control-button">▶</button>
                                    <button class="control-button">✓</button>
                                </div>
                            </div>
                            <div class="voicemail-item">
                                <div class="voicemail-info">
                                    <div class="voicemail-name">Personal Greeting</div>
                                    <div class="voicemail-meta">Duration: 0:16 | Used: 3 times</div>
                                </div>
                                <div class="voicemail-controls">
                                    <button class="control-button">▶</button>
                                    <button class="control-button">✓</button>
                                </div>
                            </div>
                        </div>
                        
                        <div style="margin-top: 15px;">
                            <label class="file-label" for="upload-voicemail">
                                <span>Upload MP3 Voicemail</span>
                            </label>
                            <input type="file" id="upload-voicemail" class="file-input" accept="audio/mp3">
                        </div>
                    </div>
                    
                    <div class="right-panel">
                        <div class="panel-header">Text-to-Speech Generator</div>
                        
                        <div class="tts-form">
                            <label class="form-label">Voicemail Name</label>
                            <input type="text" class="form-input" placeholder="Enter a name for this voicemail">
                            
                            <label class="form-label">Voicemail Script</label>
                            <textarea class="form-textarea" placeholder="Hi, you've reached [name]. I'm not available right now. Please leave your name, number, and a brief message after the tone, and I'll get back to you as soon as possible. Thanks for calling!"></textarea>
                            
                            <label class="form-label">Voice Type</label>
                            <select class="form-select">
                                <option>Professional Female</option>
                                <option>Professional Male</option>
                                <option>Casual Female</option>
                                <option>Casual Male</option>
                                <option>Young Female</option>
                                <option>Young Male</option>
                                <option>Older Female</option>
                                <option>Older Male</option>
                            </select>
                            
                            <button class="button" style="width: 100%;">Generate Voicemail</button>
                        </div>
                        
                        <div class="player-container">
                            <div class="player-waveform"></div>
                            <div class="player-controls">
                                <button class="button secondary-button">◀◀</button>
                                <button class="button">▶</button>
                                <button class="button secondary-button">▶▶</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="app-footer">
                © ProgressBets™ | TextNow v1.0.0 | 5 Accounts Active
            </div>
        </div>
    </body>
    </html>
    ''', logo_exists=os.path.exists("static/progress_logo.png"), nav_menu=nav_menu)

@app.route('/campaign_schedule')
def campaign_schedule_route():
    """The campaign scheduling interface"""
    process_assets()
    logo_exists = os.path.exists("static/progress_logo.png")
    nav_menu = get_nav_menu('/campaign_schedule')
    from campaign_schedule import campaign_schedule_page
    return campaign_schedule_page(logo_exists=logo_exists, nav_menu=nav_menu)

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

def process_assets():
    """Process and copy assets to static folder"""
    # Check if attached logo exists and copy it to static folder if needed
    attached_logo = "attached_assets/progress_logo.png"
    if os.path.exists(attached_logo) and not os.path.exists("static/progress_logo.png"):
        import shutil
        shutil.copy(attached_logo, "static/progress_logo.png")
    
    # Check if attached background exists and copy it to static folder if needed
    attached_bg = "attached_assets/progress_background.jpg"
    if os.path.exists(attached_bg) and not os.path.exists("static/progress_background.jpg"):
        import shutil
        shutil.copy(attached_bg, "static/progress_background.jpg")

@app.route('/manual_messaging')
def manual_messaging_page():
    """The manual messaging page where you can send messages from a list of numbers"""
    process_assets()
    nav_menu = get_nav_menu('/manual_messaging')
    return render_template_string(''' HTML template for manual messaging page ''', logo_exists=os.path.exists("static/progress_logo.png"), nav_menu=nav_menu)

@app.route('/nav-debug')
def nav_debug():
    """Debug page to examine navigation menu"""
    process_assets()
    nav_menu = get_nav_menu('/nav-debug')
    return f"""
    <html>
    <head>
        <title>Navigation Debug</title>
        <style>
            body {{ font-family: Arial; background: #333; color: white; padding: 20px; }}
            pre {{ background: #222; padding: 10px; border-radius: 5px; overflow: auto; }}
        </style>
    </head>
    <body>
        <h1>Navigation Menu Debug</h1>
        <div>
            <h2>Raw HTML:</h2>
            <pre>{nav_menu}</pre>
        </div>
        <div>
            <h2>Rendered HTML:</h2>
            {nav_menu}
        </div>
        <div>
            <h3>Test other pages:</h3>
            <ul>
                <li><a href="/" style="color: #FF6600;">Home</a></li>
                <li><a href="/dashboard" style="color: #FF6600;">Dashboard</a></li>
                <li><a href="/creator" style="color: #FF6600;">Creator</a></li>
                <li><a href="/campaigns" style="color: #FF6600;">Campaigns</a></li>
            </ul>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    process_assets()
    app.run(host='0.0.0.0', port=5000, debug=True)