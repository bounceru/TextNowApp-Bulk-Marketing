"""
Preview server for ProgressGhostCreator app

This script creates a simple HTTP server that displays a mockup of the application
to showcase how it will look when running as a Windows executable.
"""

from flask import Flask, render_template_string, send_from_directory, redirect, url_for, request
import os
import json
import random
from datetime import datetime, timedelta

from voicemail_manager import voicemail_manager_page
from message_dashboard import message_dashboard_page
from image_dashboard import image_dashboard_page
from account_health_dashboard import account_health_dashboard_page

# Helper function for consistent navigation
def get_nav_menu(active_page):
    """Generate consistent navigation menu HTML with active page highlighted"""
    menu_items = [
        {"url": "/creator", "name": "Creator"},
        {"url": "/dashboard", "name": "Dashboard"},
        {"url": "/message-dashboard", "name": "Messages"},
        {"url": "/campaigns", "name": "Campaigns"},
        {"url": "/image-dashboard", "name": "Images"},
        {"url": "/voicemail-manager", "name": "Voicemails"},
        {"url": "/account-health", "name": "Health"},
        {"url": "/manual_messaging", "name": "Manual Messages"},
        {"url": "/campaign-schedule", "name": "Schedule"}
    ]
    
    nav_html = '<div class="nav-menu">'
    for item in menu_items:
        active_class = " active" if item["url"] == active_page else ""
        nav_html += f'<a href="{item["url"]}" class="nav-button{active_class}">{item["name"]}</a>'
    nav_html += '</div>'
    
    return nav_html

app = Flask(__name__)

# Create static directory for image assets if it doesn't exist
os.makedirs('static', exist_ok=True)

# Sample data for the dashboard
sample_accounts = [
    {"id": 1, "phone_number": "(555) 123-4567", "username": "ghost_user_456", "email": "ghost456@progressmail.com", "active": True, "flagged": False, "health_score": 98.5, "created_at": (datetime.now() - timedelta(days=15)).isoformat(), "message_count": 345, "conversation_count": 42, "area_code": "555", "ip_used": "192.168.1.123"},
    {"id": 2, "phone_number": "(555) 234-5678", "username": "phantom_bet_789", "email": "phantom789@progressmail.com", "active": True, "flagged": False, "health_score": 92.0, "created_at": (datetime.now() - timedelta(days=12)).isoformat(), "message_count": 278, "conversation_count": 37, "area_code": "555", "ip_used": "192.168.1.124"},
    {"id": 3, "phone_number": "(555) 345-6789", "username": "shadow_play_123", "email": "shadow123@progressmail.com", "active": True, "flagged": False, "health_score": 85.5, "created_at": (datetime.now() - timedelta(days=8)).isoformat(), "message_count": 192, "conversation_count": 25, "area_code": "555", "ip_used": "192.168.1.125"},
    {"id": 4, "phone_number": "(555) 456-7890", "username": "invisible_win_234", "email": "invisible234@progressmail.com", "active": False, "flagged": True, "health_score": 45.0, "created_at": (datetime.now() - timedelta(days=5)).isoformat(), "message_count": 87, "conversation_count": 12, "area_code": "555", "ip_used": "192.168.1.126"},
    {"id": 5, "phone_number": "(555) 567-8901", "username": "stealth_bet_567", "email": "stealth567@progressmail.com", "active": True, "flagged": False, "health_score": 94.5, "created_at": (datetime.now() - timedelta(days=3)).isoformat(), "message_count": 42, "conversation_count": 8, "area_code": "555", "ip_used": "192.168.1.127"}
]

sample_campaigns = [
    {"id": 1, "name": "March Madness Promotion", "status": "active", "target_count": 10000, "completed_count": 3500, "created_at": (datetime.now() - timedelta(days=5)).isoformat(), "description": "Promotion for college basketball tournament"},
    {"id": 2, "name": "NFL Week 1 Special", "status": "draft", "target_count": 5000, "completed_count": 0, "created_at": (datetime.now() - timedelta(days=2)).isoformat(), "description": "Special odds for NFL opening week"},
    {"id": 3, "name": "Welcome Bonus Campaign", "status": "completed", "target_count": 2000, "completed_count": 2000, "created_at": (datetime.now() - timedelta(days=10)).isoformat(), "description": "New user signup bonus promotion"}
]

sample_conversations = [
    {"id": 1, "contact_number": "(444) 123-4567", "started_at": (datetime.now() - timedelta(hours=5)).isoformat(), "last_message_at": (datetime.now() - timedelta(minutes=30)).isoformat(), "message_count": 6, "status": "active"},
    {"id": 2, "contact_number": "(444) 234-5678", "started_at": (datetime.now() - timedelta(days=1)).isoformat(), "last_message_at": (datetime.now() - timedelta(hours=2)).isoformat(), "message_count": 4, "status": "active"},
    {"id": 3, "contact_number": "(444) 345-6789", "started_at": (datetime.now() - timedelta(days=2)).isoformat(), "last_message_at": (datetime.now() - timedelta(days=1)).isoformat(), "message_count": 8, "status": "inactive"}
]

sample_messages = {
    "(444) 123-4567": [
        {"direction": "outbound", "message": "Hi there! Looking for the best odds on basketball games? Check out PB Betting! We have great bonuses for new members.", "timestamp": (datetime.now() - timedelta(hours=5)).isoformat()},
        {"direction": "inbound", "message": "What kind of bonuses do you offer?", "timestamp": (datetime.now() - timedelta(hours=4, minutes=45)).isoformat()},
        {"direction": "outbound", "message": "We're offering a 100% match on your first deposit up to $500, plus free bets for March Madness!", "timestamp": (datetime.now() - timedelta(hours=4, minutes=30)).isoformat()},
        {"direction": "inbound", "message": "That sounds good. How do I sign up?", "timestamp": (datetime.now() - timedelta(hours=4)).isoformat()},
        {"direction": "outbound", "message": "Just visit our website at pbbetting.com and create an account. Use code MADNESS100 for an extra $50 bonus!", "timestamp": (datetime.now() - timedelta(hours=3, minutes=50)).isoformat()},
        {"direction": "inbound", "message": "Thanks, I'll check it out!", "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat()}
    ],
    "(444) 234-5678": [
        {"direction": "outbound", "message": "Exclusive offer today only! Deposit $50, get a $100 betting credit for the SuperBowl. Reply YES for details.", "timestamp": (datetime.now() - timedelta(days=1)).isoformat()},
        {"direction": "inbound", "message": "YES", "timestamp": (datetime.now() - timedelta(hours=20)).isoformat()},
        {"direction": "outbound", "message": "Great! Visit pbbetting.com/bonus and use code SUPER100 during signup. Offer valid until midnight!", "timestamp": (datetime.now() - timedelta(hours=19)).isoformat()},
        {"direction": "inbound", "message": "Is this available for existing customers too?", "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()}
    ],
    "(444) 345-6789": [
        {"direction": "outbound", "message": "Hey John, just checking if you had a chance to look at our betting options. Any questions I can help with?", "timestamp": (datetime.now() - timedelta(days=2)).isoformat()},
        {"direction": "inbound", "message": "Not interested. Please stop messaging me.", "timestamp": (datetime.now() - timedelta(days=2, hours=1)).isoformat()},
        {"direction": "outbound", "message": "I apologize for the inconvenience. You've been unsubscribed from our messages. Reply START to opt back in.", "timestamp": (datetime.now() - timedelta(days=2, hours=1, minutes=1)).isoformat()}
    ]
}

@app.route('/')
def index():
    """Display the mockup of the ProgressGhostCreator application"""
    process_assets()
    return creator_page()

@app.route('/creator')
def creator_page():
    """The main account creator page"""
    process_assets()
    nav_menu = get_nav_menu('/creator')
    return render_template_string('''
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
                width: 800px;
                height: 600px;
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
            
            .app-content {
                display: flex;
                flex-direction: column;
                flex: 1;
                padding: 20px;
            }
            
            .control-panel {
                display: flex;
                margin-bottom: 20px;
                align-items: center;
            }
            
            .input-group {
                display: flex;
                align-items: center;
                margin-right: 20px;
            }
            
            .input-label {
                margin-right: 10px;
                color: #CCC;
            }
            
            .input-field {
                width: 80px;
                padding: 5px;
                background-color: #2D2D2D;
                border: 1px solid #555;
                color: #EEE;
                border-radius: 3px;
            }
            
            .btn {
                background-color: #FF6600;
                color: white;
                border: none;
                padding: 8px 15px;
                margin-right: 10px;
                cursor: pointer;
                border-radius: 3px;
                font-weight: bold;
            }
            
            .btn:disabled {
                background-color: #884400;
                opacity: 0.7;
                cursor: not-allowed;
            }
            
            .btn-pause {
                background-color: #666600;
            }
            
            .btn-stop {
                background-color: #990000;
            }
            
            .status-container {
                flex: 1;
                display: flex;
                flex-direction: column;
                background-color: #2D2D2D;
                border-radius: 5px;
                overflow: hidden;
                border: 1px solid #444;
            }
            
            .status-header {
                background-color: #FF6600;
                padding: 8px 15px;
                font-size: 14px;
                font-weight: bold;
                color: white;
            }
            
            .status-log {
                flex: 1;
                background-color: #1A1A1A;
                font-family: monospace;
                padding: 10px;
                overflow-y: auto;
                font-size: 12px;
                color: #CCC;
            }
            
            .log-entry {
                margin-bottom: 4px;
                line-height: 1.4;
            }
            
            .timestamp {
                color: #888;
            }
            
            .info {
                color: #CCC;
            }
            
            .success {
                color: #55FF55;
            }
            
            .error {
                color: #FF5555;
            }
            
            .warning {
                color: #FFFF55;
            }
            
            .progress-container {
                margin-top: 15px;
            }
            
            .progress-bar {
                height: 20px;
                background-color: #333;
                border-radius: 10px;
                overflow: hidden;
                margin-bottom: 5px;
                border: 1px solid #444;
            }
            
            .progress-fill {
                height: 100%;
                background-color: #FF6600;
                width: 35%;
            }
            
            .progress-stats {
                display: flex;
                justify-content: space-between;
                font-size: 12px;
                color: #AAA;
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
                <div class="control-panel">
                    <div class="input-group">
                        <label class="input-label">Accounts:</label>
                        <input type="number" class="input-field" value="100" min="1" max="10000">
                    </div>
                    <div class="input-group" style="flex-direction: column; align-items: flex-start;">
                        <label class="input-label">Area Code:</label>
                        <div style="display: flex; align-items: center; margin-top: 5px;">
                            <input type="text" class="input-field" placeholder="404,910,487" style="width:150px; margin-right: 10px;">
                            <button class="btn" style="padding: 4px 8px; font-size: 12px; margin: 0;">Add</button>
                        </div>
                        <div style="margin-top: 3px; font-size: 11px; color: #AAA;">
                            Separate multiple area codes with commas (e.g., 404,910,487)
                        </div>
                        <div style="margin-top: 5px; width: 100%;">
                            <select class="input-field" style="width:150px;">
                                <option>Selected Area Codes</option>
                                <option>954 (FL)</option>
                                <option>754 (FL)</option>
                                <option>305 (FL)</option>
                                <option>786 (FL)</option>
                                <option>561 (FL)</option>
                            </select>
                            <button class="btn" style="padding: 4px 8px; font-size: 12px; margin-left: 5px;">Remove</button>
                        </div>
                    </div>
                    <div class="input-group">
                        <label class="input-label">Creation Rate:</label>
                        <select class="input-field" style="width:150px;">
                            <option>Random (30-90s)</option>
                            <option>Fast (15-30s)</option>
                            <option>Normal (60-120s)</option>
                            <option>Slow (120-240s)</option>
                            <option>Custom...</option>
                        </select>
                    </div>
                    <div class="input-group">
                        <label class="input-label">Distribution:</label>
                        <select class="input-field" style="width:150px;">
                            <option>No Distribution</option>
                            <option>1 Hour</option>
                            <option>2 Hours</option>
                            <option>4 Hours</option>
                            <option>6 Hours</option>
                            <option>12 Hours</option>
                            <option>24 Hours</option>
                            <option>Custom...</option>
                        </select>
                    </div>
                    <button class="btn" id="start-btn">Create Accounts</button>
                    <button class="btn btn-pause" id="pause-btn" disabled>Pause</button>
                    <button class="btn btn-stop" id="stop-btn" disabled>Stop</button>
                </div>
                
                <div style="display: flex; margin-bottom: 15px;">
                    <div style="flex: 1; background: #2D2D2D; border-radius: 5px; padding: 15px; border: 1px solid #444; margin-right: 15px;">
                        <div style="font-weight: bold; font-size: 14px; color: #FF6600; margin-bottom: 10px; border-bottom: 1px solid #444; padding-bottom: 8px;">
                            Import Registration Data
                        </div>
                        <div style="margin-bottom: 15px; color: #CCC; font-size: 12px;">
                            Upload a CSV, TXT, or Excel file with registration details such as names, usernames, emails, etc.
                            <div style="margin-top: 5px; font-style: italic;">If no file is uploaded, the system will use randomly generated names and details.</div>
                        </div>
                        <div style="display: flex; margin-bottom: 10px;">
                            <div style="flex: 1;">
                                <input type="file" id="import-file" accept=".csv,.txt,.xlsx,.xls" style="display: none;">
                                <div style="display: flex; align-items: center;">
                                    <button onclick="document.getElementById('import-file').click();" class="btn" style="margin-right: 10px;">Choose File</button>
                                    <span id="file-name" style="color: #AAA; font-size: 13px;">No file selected</span>
                                </div>
                            </div>
                        </div>
                        <div style="margin-top: 10px; display: flex; justify-content: space-between; align-items: center;">
                            <div style="display: flex; align-items: center;">
                                <input type="checkbox" id="use-imported-data" style="margin-right: 5px;">
                                <label for="use-imported-data" style="color: #DDD; font-size: 13px;">Use imported data for account creation</label>
                            </div>
                            <button id="import-btn" class="btn" disabled>Import Data</button>
                        </div>
                        <div id="import-status" style="margin-top: 10px; font-size: 13px; color: #AAA;"></div>
                    </div>
                    
                    <div style="flex: 1; background: #2D2D2D; border-radius: 5px; padding: 15px; border: 1px solid #444;">
                        <div style="font-weight: bold; font-size: 14px; color: #FF6600; margin-bottom: 10px; border-bottom: 1px solid #444; padding-bottom: 8px;">
                            File Format Example
                        </div>
                        <div style="font-family: monospace; background: #222; padding: 10px; border-radius: 3px; color: #CCC; font-size: 12px; overflow: auto; max-height: 120px;">
first_name,last_name,username,email<br>
John,Smith,jsmith45,jsmith45@example.com<br>
Sarah,Johnson,sarahj22,sarahj22@example.com<br>
Michael,Williams,mwill98,mwill98@example.com
                        </div>
                        <div style="margin-top: 10px; color: #AAA; font-size: 12px;">
                            <div style="margin-bottom: 5px;"><strong>Required columns:</strong> first_name, last_name, username, email</div>
                            <div style="margin-bottom: 5px;"><strong>Optional columns:</strong> phone, area_code, password</div>
                            <div>If file is not uploaded or if optional fields are missing, the system will use randomly generated information based on your settings.</div>
                        </div>
                    </div>
                </div>
                
                <div class="status-container">
                    <div class="status-header">Creation Status</div>
                    <div class="status-log">
                        <div class="log-entry">
                            <span class="timestamp">[11:32:45]</span>
                            <span class="info">Initializing account creation process...</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:32:46]</span>
                            <span class="info">Loading name and username database...</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:32:47]</span>
                            <span class="success">Successfully loaded 5,000 name combinations</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:32:48]</span>
                            <span class="info">Connecting to mobile device for IP rotation...</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:32:50]</span>
                            <span class="success">Successfully connected to BLU G44 device</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:32:51]</span>
                            <span class="info">Current IP address: 192.168.1.123</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:32:52]</span>
                            <span class="info">Starting account creation sequence for 100 accounts</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:32:55]</span>
                            <span class="success">Created account #1: ghost_user_456 | (555) 123-4567</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:33:10]</span>
                            <span class="success">Created account #2: phantom_bet_789 | (555) 234-5678</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:33:12]</span>
                            <span class="info">Rotating IP address...</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:33:15]</span>
                            <span class="info">New IP address: 192.168.1.124</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:33:30]</span>
                            <span class="success">Created account #3: shadow_play_123 | (555) 345-6789</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:33:45]</span>
                            <span class="success">Created account #4: invisible_win_234 | (555) 456-7890</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:33:47]</span>
                            <span class="info">Rotating IP address...</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:33:50]</span>
                            <span class="info">New IP address: 192.168.1.125</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:34:05]</span>
                            <span class="warning">SMS verification required for account #5</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:34:10]</span>
                            <span class="info">Using SMS verification service...</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:34:20]</span>
                            <span class="success">SMS verified for account #5</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:34:25]</span>
                            <span class="success">Created account #5: stealth_bet_567 | (555) 567-8901</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:34:27]</span>
                            <span class="info">Creating custom voicemail greeting for account #5...</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:34:30]</span>
                            <span class="success">Voicemail greeting created and uploaded</span>
                        </div>
                        <div class="log-entry">
                            <span class="timestamp">[11:34:31]</span>
                            <span class="info">Processing continues... (35 accounts created)</span>
                        </div>
                    </div>
                </div>
                
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                    <div class="progress-stats">
                        <div>Progress: 35/100 accounts created</div>
                        <div>Estimated time remaining: 12 minutes</div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // File upload handling
            document.getElementById('import-file').addEventListener('change', function() {
                const fileInput = document.getElementById('import-file');
                const fileNameElement = document.getElementById('file-name');
                const importBtn = document.getElementById('import-btn');
                
                if (fileInput.files.length > 0) {
                    const fileName = fileInput.files[0].name;
                    fileNameElement.textContent = fileName;
                    importBtn.disabled = false;
                    
                    // Check file extension
                    const extension = fileName.split('.').pop().toLowerCase();
                    if (['csv', 'txt', 'xlsx', 'xls'].indexOf(extension) === -1) {
                        document.getElementById('import-status').textContent = 'Error: Unsupported file format. Please use CSV, TXT, or Excel files.';
                        document.getElementById('import-status').style.color = '#FF5555';
                        importBtn.disabled = true;
                    }
                } else {
                    fileNameElement.textContent = 'No file selected';
                    importBtn.disabled = true;
                }
            });
            
            // Import button click handler
            document.getElementById('import-btn').addEventListener('click', function() {
                const importStatus = document.getElementById('import-status');
                importStatus.textContent = 'Importing data...';
                importStatus.style.color = '#FF6600';
                
                // Simulate import process
                setTimeout(() => {
                    importStatus.textContent = 'Success! Imported 35 registration records.';
                    importStatus.style.color = '#66FF66';
                    
                    // Add sample log entry
                    const logElement = document.querySelector('.status-log');
                    const currentTime = new Date();
                    const timeStr = [currentTime.getHours(), currentTime.getMinutes(), currentTime.getSeconds()]
                        .map(x => x < 10 ? '0' + x : x).join(':');
                    
                    const logEntry = document.createElement('div');
                    logEntry.className = 'log-entry';
                    logEntry.innerHTML = `
                        <span class="timestamp">[${timeStr}]</span>
                        <span class="success">Imported 35 registration records from file</span>
                    `;
                    logElement.prepend(logEntry);
                }, 1500);
            });
            
            // Start button click handler
            document.getElementById('start-btn').addEventListener('click', function() {
                this.disabled = true;
                document.getElementById('pause-btn').disabled = false;
                document.getElementById('stop-btn').disabled = false;
                
                const useImportedData = document.getElementById('use-imported-data').checked;
                const message = useImportedData ? 
                    'Account creation process started using imported registration data!' : 
                    'Account creation process started with randomly generated data!';
                
                // This would actually start the account creation process
                // For the demo, we'll just show an alert
                alert(message);
            });
            
            // Pause and Stop button handlers
            document.getElementById('pause-btn').addEventListener('click', function() {
                this.disabled = true;
                document.getElementById('start-btn').disabled = false;
                document.getElementById('start-btn').textContent = 'Resume';
                alert('Account creation process paused!');
            });
            
            document.getElementById('stop-btn').addEventListener('click', function() {
                this.disabled = true;
                document.getElementById('pause-btn').disabled = true;
                document.getElementById('start-btn').disabled = false;
                document.getElementById('start-btn').textContent = 'Create Accounts';
                alert('Account creation process stopped!');
            });
        </script>
    </body>
    </html>
    ''', logo_exists=os.path.exists("static/progress_logo.png"))

@app.route('/dashboard')
def dashboard_page():
    """The account management dashboard page"""
    process_assets()
    nav_menu = get_nav_menu('/dashboard')
    return render_template_string('''
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
                width: 1200px;
                height: 800px;
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
            
            .nav-button:hover, .nav-button.active {
                background-color: #CC5500;
            }
            
            .app-content {
                display: flex;
                flex: 1;
                overflow: hidden;
            }
            
            .left-panel {
                width: 350px;
                background-color: #2A2A2A;
                border-right: 1px solid #444;
                display: flex;
                flex-direction: column;
            }
            
            .search-bar {
                padding: 15px;
                border-bottom: 1px solid #444;
            }
            
            .search-input {
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 14px;
            }
            
            .filters {
                padding: 15px;
                border-bottom: 1px solid #444;
            }
            
            .filter-title {
                font-size: 14px;
                font-weight: bold;
                color: #CCC;
                margin-bottom: 10px;
            }
            
            .filter-group {
                margin-bottom: 15px;
            }
            
            .filter-label {
                display: block;
                font-size: 13px;
                color: #AAA;
                margin-bottom: 5px;
            }
            
            .filter-select {
                width: 100%;
                padding: 6px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 13px;
            }
            
            .filter-options {
                display: flex;
                flex-wrap: wrap;
            }
            
            .filter-checkbox {
                display: flex;
                align-items: center;
                margin-right: 10px;
                margin-bottom: 5px;
            }
            
            .filter-checkbox input {
                margin-right: 5px;
            }
            
            .filter-checkbox label {
                font-size: 13px;
                color: #AAA;
            }
            
            .accounts-list {
                flex: 1;
                overflow-y: auto;
                padding: 0;
            }
            
            .accounts-header {
                position: sticky;
                top: 0;
                background-color: #333;
                border-bottom: 1px solid #444;
                padding: 10px 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .accounts-title {
                font-size: 14px;
                font-weight: bold;
                color: #CCC;
            }
            
            .account-count {
                font-size: 13px;
                color: #AAA;
            }
            
            .account-item {
                padding: 12px 15px;
                border-bottom: 1px solid #3A3A3A;
                cursor: pointer;
            }
            
            .account-item:hover {
                background-color: #333;
            }
            
            .account-item.selected {
                background-color: #404040;
            }
            
            .account-primary {
                font-size: 14px;
                color: #DDD;
                margin-bottom: 5px;
            }
            
            .account-secondary {
                font-size: 12px;
                color: #AAA;
                display: flex;
                justify-content: space-between;
            }
            
            .account-active {
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background-color: #5F5;
                margin-right: 6px;
            }
            
            .account-inactive {
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background-color: #AAA;
                margin-right: 6px;
            }
            
            .account-flagged {
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background-color: #F55;
                margin-right: 6px;
            }
            
            .account-status {
                display: flex;
                align-items: center;
                font-size: 12px;
                color: #888;
            }
            
            .account-stat {
                margin-right: 10px;
            }
            
            .right-panel {
                flex: 1;
                display: flex;
                flex-direction: column;
            }
            
            .right-header {
                padding: 15px;
                background-color: #333;
                border-bottom: 1px solid #444;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .account-menu {
                display: flex;
            }
            
            .account-menu-button {
                background-color: #555;
                color: white;
                border: none;
                padding: 6px 12px;
                margin-left: 8px;
                cursor: pointer;
                border-radius: 3px;
                font-size: 13px;
            }
            
            .account-menu-button:hover {
                background-color: #666;
            }
            
            .danger-button {
                background-color: #922;
            }
            
            .danger-button:hover {
                background-color: #B33;
            }
            
            .tabs {
                display: flex;
                background-color: #333;
                border-bottom: 1px solid #444;
            }
            
            .tab {
                padding: 10px 20px;
                color: #AAA;
                cursor: pointer;
                font-size: 14px;
                border-bottom: 2px solid transparent;
            }
            
            .tab:hover {
                color: #DDD;
                background-color: #3A3A3A;
            }
            
            .tab.active {
                color: #FF6600;
                border-bottom: 2px solid #FF6600;
            }
            
            .tab-content {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
            }
            
            /* Tab panel functionality */
            .tab-panel {
                display: none;
            }
            
            .tab-panel.active {
                display: block;
            }
            
            /* Conversation styling */
            .conversation-item {
                transition: background-color 0.2s;
            }
            
            .conversation-item:hover {
                background-color: #3A3A3A !important;
            }
            
            .account-details {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
            }
            
            .detail-card {
                background-color: #333;
                border-radius: 5px;
                padding: 15px;
                display: flex;
                flex-direction: column;
            }
            
            .detail-header {
                font-size: 14px;
                font-weight: bold;
                color: #CCC;
                margin-bottom: 15px;
                border-bottom: 1px solid #444;
                padding-bottom: 10px;
            }
            
            .detail-row {
                display: flex;
                margin-bottom: 8px;
            }
            
            .detail-label {
                width: 140px;
                color: #AAA;
                font-size: 13px;
            }
            
            .detail-value {
                flex: 1;
                color: #DDD;
                font-size: 13px;
            }
            
            .password-field {
                display: flex;
                align-items: center;
            }
            
            .password-value {
                flex: 1;
                font-family: monospace;
            }
            
            .password-toggle {
                background: none;
                border: none;
                color: #888;
                cursor: pointer;
                padding: 0 5px;
                font-size: 12px;
            }
            
            .password-toggle:hover {
                color: #CCC;
            }
            
            .health-score {
                height: 8px;
                background-color: #444;
                border-radius: 4px;
                margin-top: 5px;
                overflow: hidden;
            }
            
            .health-fill {
                height: 100%;
                background-color: #5F5;
            }
            
            .health-fair {
                background-color: #FF5;
            }
            
            .health-poor {
                background-color: #F55;
            }
            
            .stats-row {
                display: flex;
                margin-top: 15px;
                justify-content: space-between;
            }
            
            .stat-box {
                background-color: #3A3A3A;
                border-radius: 4px;
                padding: 10px;
                text-align: center;
                width: 30%;
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
            
            .notes-area {
                width: 100%;
                height: 100px;
                background-color: #2A2A2A;
                border: 1px solid #444;
                border-radius: 4px;
                color: #DDD;
                padding: 10px;
                font-size: 13px;
                resize: none;
                margin-top: 10px;
            }
            
            .conversations {
                display: flex;
                flex: 1;
                border: 1px solid #444;
                border-radius: 5px;
                overflow: hidden;
            }
            
            .conversations-list {
                width: 250px;
                background-color: #2A2A2A;
                border-right: 1px solid #444;
                overflow-y: auto;
            }
            
            .conversation-header {
                padding: 12px;
                background-color: #333;
                border-bottom: 1px solid #444;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .conversation-title {
                font-size: 14px;
                color: #CCC;
                font-weight: bold;
            }
            
            .conversation-button {
                background-color: #555;
                color: white;
                border: none;
                padding: 5px 10px;
                cursor: pointer;
                border-radius: 3px;
                font-size: 12px;
            }
            
            .conversation-button:hover {
                background-color: #666;
            }
            
            .conversation-item {
                padding: 12px;
                border-bottom: 1px solid #3A3A3A;
                cursor: pointer;
            }
            
            .conversation-item:hover {
                background-color: #333;
            }
            
            .conversation-item.active {
                background-color: #404040;
            }
            
            .conversation-contact {
                font-size: 14px;
                color: #DDD;
                margin-bottom: 5px;
            }
            
            .conversation-time {
                font-size: 12px;
                color: #888;
            }
            
            .conversation-detail {
                flex: 1;
                display: flex;
                flex-direction: column;
            }
            
            .message-container {
                flex: 1;
                padding: 15px;
                overflow-y: auto;
                background-color: #2A2A2A;
            }
            
            .message {
                max-width: 80%;
                margin-bottom: 15px;
                padding: 10px 15px;
                border-radius: 18px;
                font-size: 14px;
                position: relative;
            }
            
            .message-inbound {
                background-color: #333;
                color: #DDD;
                align-self: flex-start;
                border-bottom-left-radius: 5px;
                margin-right: auto;
            }
            
            .message-outbound {
                background-color: #FF6600;
                color: white;
                align-self: flex-end;
                border-bottom-right-radius: 5px;
                margin-left: auto;
            }
            
            .message-time {
                font-size: 11px;
                color: #888;
                margin-top: 5px;
                text-align: right;
            }
            
            .message-input-container {
                padding: 15px;
                background-color: #333;
                border-top: 1px solid #444;
                display: flex;
                align-items: center;
            }
            
            .message-input {
                flex: 1;
                padding: 10px;
                border-radius: 20px;
                border: 1px solid #555;
                background-color: #2A2A2A;
                color: #DDD;
                font-size: 14px;
            }
            
            .send-button {
                background-color: #FF6600;
                color: white;
                border: none;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                margin-left: 10px;
                cursor: pointer;
                font-size: 16px;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            .send-button:hover {
                background-color: #FF7722;
            }
            
            .message-templates {
                padding: 15px;
                background-color: #333;
                border-top: 1px solid #444;
            }
            
            .templates-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            
            .templates-title {
                font-size: 14px;
                color: #CCC;
                font-weight: bold;
            }
            
            .templates-list {
                display: flex;
                flex-wrap: wrap;
            }
            
            .template-item {
                background-color: #2A2A2A;
                border: 1px solid #444;
                border-radius: 15px;
                padding: 6px 12px;
                margin-right: 8px;
                margin-bottom: 8px;
                font-size: 13px;
                color: #CCC;
                cursor: pointer;
            }
            
            .template-item:hover {
                background-color: #3A3A3A;
                border-color: #555;
            }
            
            .app-footer {
                padding: 8px;
                text-align: center;
                background-color: #333;
                color: #AAA;
                font-size: 11px;
                border-top: 1px solid #444;
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
                <div class="left-panel">
                    <div class="search-bar">
                        <input type="text" class="search-input" placeholder="Search accounts...">
                    </div>
                    
                    <div class="filters">
                        <div class="filter-title">Filters</div>
                        <div class="filter-group">
                            <label class="filter-label">Area Code</label>
                            <select class="filter-select">
                                <option value="all">All Area Codes</option>
                                <option value="555">555 (5 accounts)</option>
                                <option value="444">444 (3 accounts)</option>
                                <option value="333">333 (2 accounts)</option>
                            </select>
                        </div>
                        
                        <div class="filter-group">
                            <label class="filter-label">Status</label>
                            <div class="filter-options">
                                <div class="filter-checkbox">
                                    <input type="checkbox" id="active" checked>
                                    <label for="active">Active</label>
                                </div>
                                <div class="filter-checkbox">
                                    <input type="checkbox" id="inactive">
                                    <label for="inactive">Inactive</label>
                                </div>
                                <div class="filter-checkbox">
                                    <input type="checkbox" id="flagged">
                                    <label for="flagged">Flagged</label>
                                </div>
                            </div>
                        </div>
                        
                        <div class="filter-group">
                            <label class="filter-label">IP Family</label>
                            <select class="filter-select">
                                <option value="all">All IP Families</option>
                                <option value="192.168.1">192.168.1.x (5 accounts)</option>
                                <option value="10.0.0">10.0.0.x (3 accounts)</option>
                                <option value="172.16.0">172.16.0.x (2 accounts)</option>
                            </select>
                        </div>
                        
                        <div class="filter-group">
                            <label class="filter-label">Health Score</label>
                            <select class="filter-select">
                                <option value="all">All Health Scores</option>
                                <option value="good">Good (90-100)</option>
                                <option value="fair">Fair (70-89)</option>
                                <option value="poor">Poor (0-69)</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="accounts-list">
                        <div class="accounts-header">
                            <div class="accounts-title">Accounts</div>
                            <div class="account-count">Showing 5 of 5</div>
                        </div>
                        
                        <div class="account-item selected">
                            <div class="account-primary">
                                <span class="account-active"></span>
                                (555) 123-4567
                            </div>
                            <div class="account-secondary">
                                <div>ghost_user_456</div>
                                <div class="account-status">
                                    <div class="account-stat">15d</div>
                                    <div class="account-stat">345 msgs</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="account-item">
                            <div class="account-primary">
                                <span class="account-active"></span>
                                (555) 234-5678
                            </div>
                            <div class="account-secondary">
                                <div>phantom_bet_789</div>
                                <div class="account-status">
                                    <div class="account-stat">12d</div>
                                    <div class="account-stat">278 msgs</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="account-item">
                            <div class="account-primary">
                                <span class="account-active"></span>
                                (555) 345-6789
                            </div>
                            <div class="account-secondary">
                                <div>shadow_play_123</div>
                                <div class="account-status">
                                    <div class="account-stat">8d</div>
                                    <div class="account-stat">192 msgs</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="account-item">
                            <div class="account-primary">
                                <span class="account-flagged"></span>
                                (555) 456-7890
                            </div>
                            <div class="account-secondary">
                                <div>invisible_win_234</div>
                                <div class="account-status">
                                    <div class="account-stat">5d</div>
                                    <div class="account-stat">87 msgs</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="account-item">
                            <div class="account-primary">
                                <span class="account-active"></span>
                                (555) 567-8901
                            </div>
                            <div class="account-secondary">
                                <div>stealth_bet_567</div>
                                <div class="account-status">
                                    <div class="account-stat">3d</div>
                                    <div class="account-stat">42 msgs</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="right-panel">
                    <div class="right-header">
                        <h2 style="margin: 0; font-size: 18px; color: #EEE;">(555) 123-4567 - ghost_user_456</h2>
                        <div class="account-menu">
                            <button class="account-menu-button" id="toggle-active">Deactivate</button>
                            <button class="account-menu-button danger-button" id="delete-account">Delete Account</button>
                        </div>
                    </div>
                    
                    <div class="tabs">
                        <div class="tab active">Account Details</div>
                        <div class="tab">Messaging</div>
                        <div class="tab">History</div>
                    </div>
                    
                    <div class="tab-content">
                        <div class="account-details tab-panel" style="display: block;">
                        
                            <div class="detail-card">
                                <div class="detail-header">Account Information</div>
                                <div class="detail-row">
                                    <div class="detail-label">Phone Number:</div>
                                    <div class="detail-value">(555) 123-4567</div>
                                </div>
                                <div class="detail-row">
                                    <div class="detail-label">Username:</div>
                                    <div class="detail-value">ghost_user_456</div>
                                </div>
                                <div class="detail-row">
                                    <div class="detail-label">Email:</div>
                                    <div class="detail-value">ghost456@progressmail.com</div>
                                </div>
                                <div class="detail-row">
                                    <div class="detail-label">Password:</div>
                                    <div class="detail-value password-field">
                                        <div class="password-value">••••••••••••</div>
                                        <button class="password-toggle">Show</button>
                                    </div>
                                </div>
                                <div class="detail-row">
                                    <div class="detail-label">Created:</div>
                                    <div class="detail-value">15 days ago</div>
                                </div>
                                <div class="detail-row">
                                    <div class="detail-label">Status:</div>
                                    <div class="detail-value">Active</div>
                                </div>
                                <div class="detail-row">
                                    <div class="detail-label">Health Score:</div>
                                    <div class="detail-value">
                                        98.5/100
                                        <div class="health-score">
                                            <div class="health-fill" style="width: 98.5%"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="detail-card">
                                <div class="detail-header">Technical Information</div>
                                <div class="detail-row">
                                    <div class="detail-label">Area Code:</div>
                                    <div class="detail-value">555</div>
                                </div>
                                <div class="detail-row">
                                    <div class="detail-label">Current IP:</div>
                                    <div class="detail-value">192.168.1.123</div>
                                </div>
                                <div class="detail-row">
                                    <div class="detail-label">IP Family:</div>
                                    <div class="detail-value">192.168.1.x</div>
                                </div>
                                <div class="detail-row">
                                    <div class="detail-label">Device ID:</div>
                                    <div class="detail-value">XG7845-BLU-G44</div>
                                </div>
                                <div class="detail-row">
                                    <div class="detail-label">Fingerprint ID:</div>
                                    <div class="detail-value">FP-12345</div>
                                </div>
                                <div class="detail-row">
                                    <div class="detail-label">Voicemail:</div>
                                    <div class="detail-value">
                                        <button class="account-menu-button" style="margin: 0; padding: 3px 8px; font-size: 12px;">Play</button>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="detail-card">
                                <div class="detail-header">Activity Statistics</div>
                                <div class="stats-row">
                                    <div class="stat-box">
                                        <div class="stat-value">345</div>
                                        <div class="stat-label">Messages Sent</div>
                                    </div>
                                    <div class="stat-box">
                                        <div class="stat-value">42</div>
                                        <div class="stat-label">Conversations</div>
                                    </div>
                                    <div class="stat-box">
                                        <div class="stat-value">27%</div>
                                        <div class="stat-label">Response Rate</div>
                                    </div>
                                </div>
                                <div class="detail-row" style="margin-top: 20px;">
                                    <div class="detail-label">Last Activity:</div>
                                    <div class="detail-value">Today, 11:34 AM</div>
                                </div>
                                <div class="detail-row">
                                    <div class="detail-label">Last IP Change:</div>
                                    <div class="detail-value">Yesterday, 3:22 PM</div>
                                </div>
                                <div class="detail-row">
                                    <div class="detail-label">Daily Avg. Messages:</div>
                                    <div class="detail-value">23</div>
                                </div>
                                <div class="detail-row">
                                    <div class="detail-label">Peak Hours:</div>
                                    <div class="detail-value">10am - 2pm, 6pm - 8pm</div>
                                </div>
                            </div>
                            
                            <div class="detail-card">
                                <div class="detail-header">Quick Message Sender</div>
                                <div style="padding: 15px;">
                                    <div style="margin-bottom: 15px;">
                                        <label style="display: block; margin-bottom: 5px; color: #CCC;">To Phone Number:</label>
                                        <input type="text" placeholder="(555) 123-4567" 
                                              style="width: 100%; padding: 8px; background-color: #222; border: 1px solid #444; border-radius: 3px; color: #EEE;">
                                    </div>
                                    
                                    <div style="margin-bottom: 15px;">
                                        <label style="display: block; margin-bottom: 5px; color: #CCC;">Message:</label>
                                        <textarea rows="4" placeholder="Type your message here..." 
                                               style="width: 100%; padding: 8px; background-color: #222; border: 1px solid #444; border-radius: 3px; color: #EEE; resize: vertical;"></textarea>
                                    </div>
                                    
                                    <div style="margin-bottom: 15px;">
                                        <label style="display: block; margin-bottom: 5px; color: #CCC;">Attach Image:</label>
                                        <div style="display: flex; align-items: center;">
                                            <div style="width: 100px; height: 100px; background-color: #222; border: 1px solid #444; 
                                                      border-radius: 3px; display: flex; flex-direction: column; justify-content: center; 
                                                      align-items: center; margin-right: 15px; cursor: pointer;">
                                                <div style="font-size: 24px; margin-bottom: 5px;">📷</div>
                                                <div style="font-size: 12px; color: #AAA;">Select Image</div>
                                            </div>
                                            <div style="display: flex; flex-direction: column; gap: 5px;">
                                                <button style="background-color: #444; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Browse...</button>
                                                <button style="background-color: #444; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">From Library</button>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <button id="send-msg-btn" style="background-color: #FF6600; color: white; border: none; padding: 8px 15px; 
                                                border-radius: 3px; cursor: pointer; font-weight: bold;">Send Message</button>
                                        <div id="msg-status"></div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="detail-card">
                                <div class="detail-header">Notes</div>
                                <textarea class="notes-area" placeholder="Add notes about this account...">This account has been performing exceptionally well in the March Madness campaign. Receiving good engagement with basketball betting promotions.</textarea>
                                <div style="text-align: right; margin-top: 10px;">
                                    <button class="account-menu-button" style="margin: 0; background-color: #FF6600;">Save Notes</button>
                                </div>
                            </div>
                        </div>
                        
                        <div class="messaging-tab tab-panel" style="display: none;">
                            <div style="display: flex; height: 100%;">
                                <div style="width: 250px; border-right: 1px solid #444; height: 100%; overflow-y: auto;">
                                    <div style="padding: 15px;">
                                        <input type="text" placeholder="Search conversations..." 
                                               style="width: 100%; padding: 8px; background-color: #222; border: 1px solid #444; border-radius: 3px; color: #EEE; margin-bottom: 15px;">
                                        
                                        <div class="conversation-list">
                                            <div class="conversation-item selected" style="padding: 10px; border-radius: 5px; background-color: #444; margin-bottom: 8px; cursor: pointer;">
                                                <div style="font-weight: bold; color: #EEE; margin-bottom: 3px;">(786) 555-9012</div>
                                                <div style="color: #AAA; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                                    You: Let me know if you have any questions about the offer
                                                </div>
                                                <div style="color: #888; font-size: 11px; margin-top: 5px;">Today, 10:23 AM</div>
                                            </div>
                                            
                                            <div class="conversation-item" style="padding: 10px; border-radius: 5px; background-color: #333; margin-bottom: 8px; cursor: pointer;">
                                                <div style="font-weight: bold; color: #EEE; margin-bottom: 3px;">(305) 555-3478</div>
                                                <div style="color: #AAA; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                                    Is this still available? I'm interested...
                                                </div>
                                                <div style="color: #888; font-size: 11px; margin-top: 5px;">Today, 9:45 AM</div>
                                            </div>
                                            
                                            <div class="conversation-item" style="padding: 10px; border-radius: 5px; background-color: #333; margin-bottom: 8px; cursor: pointer;">
                                                <div style="font-weight: bold; color: #EEE; margin-bottom: 3px;">(954) 555-7890</div>
                                                <div style="color: #AAA; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                                    You: Thank you for your interest in our promotion
                                                </div>
                                                <div style="color: #888; font-size: 11px; margin-top: 5px;">Yesterday, 4:17 PM</div>
                                            </div>
                                            
                                            <div class="conversation-item" style="padding: 10px; border-radius: 5px; background-color: #333; margin-bottom: 8px; cursor: pointer;">
                                                <div style="font-weight: bold; color: #EEE; margin-bottom: 3px;">(561) 555-2345</div>
                                                <div style="color: #AAA; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                                    You: Would you like more information about our NBA specials?
                                                </div>
                                                <div style="color: #888; font-size: 11px; margin-top: 5px;">Yesterday, 11:05 AM</div>
                                            </div>
                                            
                                            <div class="conversation-item" style="padding: 10px; border-radius: 5px; background-color: #333; margin-bottom: 8px; cursor: pointer;">
                                                <div style="font-weight: bold; color: #EEE; margin-bottom: 3px;">(754) 555-6789</div>
                                                <div style="color: #AAA; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                                    Please remove me from your list.
                                                </div>
                                                <div style="color: #888; font-size: 11px; margin-top: 5px;">Apr 23, 8:30 PM</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="flex: 1; display: flex; flex-direction: column; height: 100%;">
                                    <div style="padding: 15px; border-bottom: 1px solid #444; display: flex; justify-content: space-between; align-items: center;">
                                        <div>
                                            <div style="font-weight: bold; color: #EEE;">(786) 555-9012</div>
                                            <div style="color: #888; font-size: 12px;">First contact: Apr 20, 2025</div>
                                        </div>
                                        <div>
                                            <button style="background-color: #555; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-left: 5px;">Block</button>
                                            <button style="background-color: #555; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-left: 5px;">Opt Out</button>
                                            <button style="background-color: #555; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-left: 5px;">Call</button>
                                        </div>
                                    </div>
                                    
                                    <div style="flex: 1; overflow-y: auto; padding: 15px;">
                                        <div class="message-history">
                                            <!-- Date separator -->
                                            <div style="text-align: center; margin: 20px 0; color: #888; font-size: 12px; position: relative;">
                                                <span style="background-color: #2A2A2A; padding: 0 10px; position: relative; z-index: 1;">April 20, 2025</span>
                                                <div style="position: absolute; top: 50%; left: 0; right: 0; height: 1px; background-color: #444; z-index: 0;"></div>
                                            </div>
                                            
                                            <!-- Outgoing message -->
                                            <div style="display: flex; flex-direction: column; align-items: flex-end; margin-bottom: 15px;">
                                                <div style="background-color: #FF6600; color: white; padding: 10px 15px; border-radius: 15px; border-bottom-right-radius: 5px; max-width: 80%;">
                                                    Hello! I'm reaching out to offer you an exclusive betting promotion for the upcoming NBA playoffs.
                                                </div>
                                                <div style="color: #888; font-size: 11px; margin-top: 5px;">9:45 AM</div>
                                            </div>
                                            
                                            <!-- Incoming message -->
                                            <div style="display: flex; flex-direction: column; align-items: flex-start; margin-bottom: 15px;">
                                                <div style="background-color: #444; color: white; padding: 10px 15px; border-radius: 15px; border-bottom-left-radius: 5px; max-width: 80%;">
                                                    Hi, what kind of promotion is it?
                                                </div>
                                                <div style="color: #888; font-size: 11px; margin-top: 5px;">10:12 AM</div>
                                            </div>
                                            
                                            <!-- Date separator -->
                                            <div style="text-align: center; margin: 20px 0; color: #888; font-size: 12px; position: relative;">
                                                <span style="background-color: #2A2A2A; padding: 0 10px; position: relative; z-index: 1;">Today</span>
                                                <div style="position: absolute; top: 50%; left: 0; right: 0; height: 1px; background-color: #444; z-index: 0;"></div>
                                            </div>
                                            
                                            <!-- Outgoing message with image -->
                                            <div style="display: flex; flex-direction: column; align-items: flex-end; margin-bottom: 15px;">
                                                <div style="background-color: #FF6600; color: white; padding: 10px 15px; border-radius: 15px; border-bottom-right-radius: 5px; max-width: 80%;">
                                                    We're offering 100% match on your first deposit up to $500 for NBA playoff betting. Here's the details:
                                                    <div style="margin-top: 10px; background-color: rgba(0,0,0,0.2); border-radius: 5px; overflow: hidden;">
                                                        <div style="height: 150px; background-color: #333; display: flex; justify-content: center; align-items: center; font-size: 24px;">🏀</div>
                                                        <div style="padding: 8px; font-size: 12px;">NBA_Playoffs_Promo.jpg</div>
                                                    </div>
                                                </div>
                                                <div style="color: #888; font-size: 11px; margin-top: 5px;">10:23 AM</div>
                                            </div>
                                            
                                            <!-- Incoming message -->
                                            <div style="display: flex; flex-direction: column; align-items: flex-start; margin-bottom: 15px;">
                                                <div style="background-color: #444; color: white; padding: 10px 15px; border-radius: 15px; border-bottom-left-radius: 5px; max-width: 80%;">
                                                    This looks interesting. Let me check it out and get back to you.
                                                </div>
                                                <div style="color: #888; font-size: 11px; margin-top: 5px;">10:45 AM</div>
                                            </div>
                                            
                                            <!-- System message -->
                                            <div style="text-align: center; margin: 15px 0; color: #888; font-size: 12px;">
                                                Message delivered ✓
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div style="padding: 15px; border-top: 1px solid #444;">
                                        <div style="position: relative; margin-bottom: 15px;">
                                            <textarea rows="3" placeholder="Type your message here..." 
                                                      style="width: 100%; padding: 10px; background-color: #222; border: 1px solid #444; border-radius: 3px; color: #EEE; resize: none;"></textarea>
                                            <div style="position: absolute; bottom: 10px; right: 10px; display: flex; gap: 10px;">
                                                <span style="cursor: pointer; color: #AAA; font-size: 18px;">📷</span>
                                                <span style="cursor: pointer; color: #AAA; font-size: 18px;">📑</span>
                                                <span style="cursor: pointer; color: #AAA; font-size: 18px;">😊</span>
                                            </div>
                                        </div>
                                        <div style="display: flex; justify-content: space-between;">
                                            <div>
                                                <button style="background-color: #555; color: white; border: none; padding: 8px 15px; border-radius: 3px; cursor: pointer;">Use Template</button>
                                            </div>
                                            <button id="send-message-btn" style="background-color: #FF6600; color: white; border: none; padding: 8px 20px; border-radius: 3px; cursor: pointer; font-weight: bold;">Send</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="history-tab tab-panel" style="display: none;">
                            <div class="detail-card" style="margin-top: 15px;">
                                <div class="detail-header">Account Activity Log</div>
                                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                                    <thead>
                                        <tr style="border-bottom: 1px solid #444; color: #CCC;">
                                            <th style="text-align: left; padding: 8px;">Date/Time</th>
                                            <th style="text-align: left; padding: 8px;">Activity</th>
                                            <th style="text-align: left; padding: 8px;">Details</th>
                                            <th style="text-align: left; padding: 8px;">IP Address</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr style="border-bottom: 1px solid #333;">
                                            <td style="padding: 8px; color: #AAA;">Today, 11:34 AM</td>
                                            <td style="padding: 8px; color: #EEE;">Message Sent</td>
                                            <td style="padding: 8px; color: #AAA;">To: (786) 555-9012</td>
                                            <td style="padding: 8px; color: #AAA;">192.168.1.123</td>
                                        </tr>
                                        <tr style="border-bottom: 1px solid #333;">
                                            <td style="padding: 8px; color: #AAA;">Today, 10:23 AM</td>
                                            <td style="padding: 8px; color: #EEE;">Message Sent</td>
                                            <td style="padding: 8px; color: #AAA;">To: (786) 555-9012</td>
                                            <td style="padding: 8px; color: #AAA;">192.168.1.123</td>
                                        </tr>
                                        <tr style="border-bottom: 1px solid #333;">
                                            <td style="padding: 8px; color: #AAA;">Today, 9:45 AM</td>
                                            <td style="padding: 8px; color: #EEE;">IP Changed</td>
                                            <td style="padding: 8px; color: #AAA;">Old: 192.168.1.100 → New: 192.168.1.123</td>
                                            <td style="padding: 8px; color: #AAA;">192.168.1.123</td>
                                        </tr>
                                        <tr style="border-bottom: 1px solid #333;">
                                            <td style="padding: 8px; color: #AAA;">Yesterday, 4:17 PM</td>
                                            <td style="padding: 8px; color: #EEE;">Message Sent</td>
                                            <td style="padding: 8px; color: #AAA;">To: (954) 555-7890</td>
                                            <td style="padding: 8px; color: #AAA;">192.168.1.100</td>
                                        </tr>
                                        <tr style="border-bottom: 1px solid #333;">
                                            <td style="padding: 8px; color: #AAA;">Yesterday, 11:05 AM</td>
                                            <td style="padding: 8px; color: #EEE;">Message Sent</td>
                                            <td style="padding: 8px; color: #AAA;">To: (561) 555-2345</td>
                                            <td style="padding: 8px; color: #AAA;">192.168.1.100</td>
                                        </tr>
                                        <tr style="border-bottom: 1px solid #333;">
                                            <td style="padding: 8px; color: #AAA;">Apr 23, 8:30 PM</td>
                                            <td style="padding: 8px; color: #EEE;">Message Received</td>
                                            <td style="padding: 8px; color: #AAA;">From: (754) 555-6789</td>
                                            <td style="padding: 8px; color: #AAA;">192.168.1.100</td>
                                        </tr>
                                        <tr style="border-bottom: 1px solid #333;">
                                            <td style="padding: 8px; color: #AAA;">Apr 23, 3:22 PM</td>
                                            <td style="padding: 8px; color: #EEE;">Voicemail Changed</td>
                                            <td style="padding: 8px; color: #AAA;">Set to: Custom Greeting (20s)</td>
                                            <td style="padding: 8px; color: #AAA;">192.168.1.100</td>
                                        </tr>
                                        <tr style="border-bottom: 1px solid #333;">
                                            <td style="padding: 8px; color: #AAA;">Apr 20, 9:45 AM</td>
                                            <td style="padding: 8px; color: #EEE;">Message Sent</td>
                                            <td style="padding: 8px; color: #AAA;">To: (786) 555-9012</td>
                                            <td style="padding: 8px; color: #AAA;">192.168.1.100</td>
                                        </tr>
                                        <tr style="border-bottom: 1px solid #333;">
                                            <td style="padding: 8px; color: #AAA;">Apr 18, 2:15 PM</td>
                                            <td style="padding: 8px; color: #EEE;">Profile Updated</td>
                                            <td style="padding: 8px; color: #AAA;">Username changed</td>
                                            <td style="padding: 8px; color: #AAA;">192.168.1.100</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px; color: #AAA;">Apr 10, 11:30 AM</td>
                                            <td style="padding: 8px; color: #EEE;">Account Created</td>
                                            <td style="padding: 8px; color: #AAA;">Initial setup completed</td>
                                            <td style="padding: 8px; color: #AAA;">192.168.1.100</td>
                                        </tr>
                                    </tbody>
                                </table>
                                <div style="text-align: center; margin-top: 15px;">
                                    <button style="background-color: #555; color: white; border: none; padding: 8px 15px; border-radius: 3px; cursor: pointer;">Load More</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="app-footer">
                © PB BETTING™ | ProgressGhostCreator v1.0.0 | 5 Accounts Active
            </div>
        </div>
        
        <script>
            // Quick Message Sender functionality
            if (document.getElementById('send-msg-btn')) {
                document.getElementById('send-msg-btn').addEventListener('click', function() {
                    const msgStatus = document.getElementById('msg-status');
                    msgStatus.innerHTML = '<span style="color: #FFAA00;">Sending message...</span>';
                    
                    // Simulate sending a message with a delay
                    setTimeout(function() {
                        msgStatus.innerHTML = '<span style="color: #55FF55;">Message sent successfully!</span>';
                        
                        // Clear the status after a few seconds
                        setTimeout(function() {
                            msgStatus.innerHTML = '';
                        }, 3000);
                    }, 1500);
                });
            }
            
            // Tab switching functionality
            document.querySelectorAll('.tab').forEach(function(tab, index) {
                tab.addEventListener('click', function() {
                    // Change active tab
                    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                    this.classList.add('active');
                    
                    // Change active panel - show only the selected one
                    const panels = document.querySelectorAll('.tab-panel');
                    panels.forEach(p => p.style.display = 'none');
                    if (panels[index]) {
                        panels[index].style.display = 'block';
                    }
                });
            });
            
            // Conversation item selection
            document.querySelectorAll('.conversation-item').forEach(function(item) {
                item.addEventListener('click', function() {
                    document.querySelectorAll('.conversation-item').forEach(i => i.classList.remove('selected'));
                    this.classList.add('selected');
                });
            });

            // Message sending in conversation view
            if (document.getElementById('send-message-btn')) {
                document.getElementById('send-message-btn').addEventListener('click', function() {
                    const textArea = this.closest('div').previousElementSibling.querySelector('textarea');
                    if (textArea && textArea.value.trim()) {
                        const messageHistory = document.querySelector('.message-history');
                        const now = new Date();
                        const time = now.getHours() + ':' + (now.getMinutes() < 10 ? '0' : '') + now.getMinutes();
                        
                        // Create new message element
                        const newMessage = document.createElement('div');
                        newMessage.style.display = 'flex';
                        newMessage.style.flexDirection = 'column';
                        newMessage.style.alignItems = 'flex-end';
                        newMessage.style.marginBottom = '15px';
                        
                        newMessage.innerHTML = `
                            <div style="background-color: #FF6600; color: white; padding: 10px 15px; border-radius: 15px; border-bottom-right-radius: 5px; max-width: 80%;">
                                ${textArea.value}
                            </div>
                            <div style="color: #888; font-size: 11px; margin-top: 5px;">${time} AM</div>
                        `;
                        
                        // Add to history
                        messageHistory.appendChild(newMessage);
                        
                        // Add delivered message
                        const deliveredMsg = document.createElement('div');
                        deliveredMsg.style.textAlign = 'center';
                        deliveredMsg.style.margin = '15px 0';
                        deliveredMsg.style.color = '#888';
                        deliveredMsg.style.fontSize = '12px';
                        deliveredMsg.textContent = 'Message delivered ✓';
                        
                        setTimeout(() => {
                            messageHistory.appendChild(deliveredMsg);
                            messageHistory.scrollTop = messageHistory.scrollHeight;
                        }, 1000);
                        
                        // Clear input
                        textArea.value = '';
                        
                        // Scroll to bottom
                        messageHistory.scrollTop = messageHistory.scrollHeight;
                    }
                });
            }
        </script>
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
            
            .nav-button:hover, .nav-button.active {
                background-color: #CC5500;
            }
            
            .app-content {
                display: flex;
                flex: 1;
                overflow: hidden;
            }
            
            .campaigns-left {
                width: 250px;
                background-color: #252525;
                border-right: 1px solid #444;
                padding: 20px;
            }
            
            .campaigns-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .campaigns-title {
                font-size: 18px;
                font-weight: bold;
                color: #EEE;
            }
            
            .new-campaign-btn {
                background-color: #FF6600;
                color: white;
                border: none;
                padding: 6px 12px;
                cursor: pointer;
                border-radius: 3px;
                font-size: 13px;
            }
            
            .new-campaign-btn:hover {
                background-color: #FF7722;
            }
            
            .campaign-filters {
                margin-bottom: 20px;
            }
            
            .filter-label {
                display: block;
                font-size: 13px;
                color: #AAA;
                margin-bottom: 5px;
            }
            
            .filter-select {
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 13px;
                margin-bottom: 10px;
            }
            
            .filter-options {
                display: flex;
                flex-wrap: wrap;
            }
            
            .filter-checkbox {
                display: flex;
                align-items: center;
                margin-right: 10px;
                margin-bottom: 5px;
            }
            
            .filter-checkbox input {
                margin-right: 5px;
            }
            
            .filter-checkbox label {
                font-size: 13px;
                color: #AAA;
            }
            
            .campaigns-right {
                flex: 1;
                display: flex;
                flex-direction: column;
                padding: 20px;
                overflow-y: auto;
            }
            
            .campaigns-search {
                display: flex;
                margin-bottom: 20px;
            }
            
            .search-input {
                flex: 1;
                padding: 10px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 14px;
            }
            
            .search-button {
                background-color: #555;
                color: white;
                border: none;
                padding: 0 15px;
                margin-left: 10px;
                cursor: pointer;
                border-radius: 4px;
                font-size: 14px;
            }
            
            .campaign-list {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            
            .campaign-item {
                background-color: #333;
                border-radius: 5px;
                border: 1px solid #444;
                padding: 15px;
            }
            
            .campaign-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            
            .campaign-name {
                font-size: 18px;
                font-weight: bold;
                color: #EEE;
            }
            
            .campaign-status {
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
                text-transform: uppercase;
            }
            
            .status-active {
                background-color: #2A2;
                color: white;
            }
            
            .status-draft {
                background-color: #AAA;
                color: #333;
            }
            
            .status-completed {
                background-color: #55C;
                color: white;
            }
            
            .campaign-details {
                color: #CCC;
                font-size: 14px;
                margin-bottom: 10px;
            }
            
            .campaign-progress-container {
                height: 8px;
                background-color: #444;
                border-radius: 4px;
                overflow: hidden;
                margin-bottom: 5px;
            }
            
            .campaign-progress-fill {
                height: 100%;
                background-color: #FF6600;
            }
            
            .campaign-stats {
                display: flex;
                justify-content: space-between;
                font-size: 13px;
                color: #AAA;
            }
            
            .campaign-actions {
                margin-top: 15px;
                display: flex;
                justify-content: flex-end;
            }
            
            .campaign-button {
                background-color: #555;
                color: white;
                border: none;
                padding: 6px 12px;
                margin-left: 8px;
                cursor: pointer;
                border-radius: 3px;
                font-size: 13px;
                text-decoration: none;
            }
            
            .campaign-button:hover {
                background-color: #666;
            }
            
            .btn-primary {
                background-color: #FF6600;
            }
            
            .btn-primary:hover {
                background-color: #FF7722;
            }
            
            .app-footer {
                padding: 8px;
                text-align: center;
                background-color: #333;
                color: #AAA;
                font-size: 11px;
                border-top: 1px solid #444;
            }
        </style>
    </head>
    <body>
        <div class="app-container">
            <div class="app-header">
                {% if logo_exists %}
                <img src="/static/progress_logo.png" alt="PB BETTING Logo" class="logo">
                {% endif %}
                <div class="nav-menu">
                    <a href="/creator" class="nav-button">Creator</a>
                    <a href="/dashboard" class="nav-button">Dashboard</a>
                    <a href="/campaigns" class="nav-button active">Campaigns</a>
                </div>
            </div>
            
            <div class="app-content">
                <div class="campaigns-left">
                    <div class="campaigns-header">
                        <div class="campaigns-title">Campaigns</div>
                        <button class="new-campaign-btn" id="new-campaign-btn">+ New</button>
                    </div>
                    
                    <!-- Campaign Creation Modal -->
                    <div id="campaign-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; justify-content: center; align-items: center;">
                        <div style="background: #2A2A2A; width: 800px; max-height: 90vh; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.5); overflow-y: auto; padding: 20px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                                <h2 style="margin: 0; color: #FFF; font-size: 20px;">Create New Campaign</h2>
                                <span id="close-modal" style="cursor: pointer; font-size: 24px; color: #AAA;">&times;</span>
                            </div>
                            
                            <div style="margin-bottom: 20px;">
                                <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Campaign Name</label>
                                <input type="text" placeholder="Enter campaign name" style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF;">
                            </div>
                            
                            <div style="margin-bottom: 20px;">
                                <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Description</label>
                                <textarea placeholder="Enter campaign description" style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF; height: 70px; resize: none;"></textarea>
                            </div>
                            
                            <div style="margin-bottom: 20px;">
                                <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Target Number</label>
                                <input type="number" placeholder="How many messages to send" style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF;">
                            </div>
                            
                            <!-- Phone Numbers Upload Section -->
                            <div style="margin-bottom: 20px; border: 1px solid #444; border-radius: 5px; padding: 15px;">
                                <h3 style="margin-top: 0; color: #FF6600; font-size: 16px;">Target Phone Numbers</h3>
                                <p style="color: #AAA; font-size: 13px; margin-bottom: 15px;">Upload a file containing the phone numbers you want to message.</p>
                                
                                <div style="display: flex; margin-bottom: 15px;">
                                    <div style="flex: 1; margin-right: 15px;">
                                        <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Numbers File</label>
                                        <div style="position: relative;">
                                            <input type="file" id="numbers-file" accept=".txt,.csv,.xlsx,.xls" style="display: none;">
                                            <div style="display: flex;">
                                                <input type="text" id="numbers-file-display" placeholder="Choose a file..." readonly style="flex: 1; padding: 10px; border-radius: 5px 0 0 5px; border: 1px solid #444; background: #222; color: #CCC; cursor: default;">
                                                <button onclick="document.getElementById('numbers-file').click()" style="white-space: nowrap; background: #555; color: white; border: none; padding: 10px 15px; border-radius: 0 5px 5px 0; cursor: pointer;">Browse</button>
                                            </div>
                                        </div>
                                        <div style="color: #AAA; font-size: 12px; margin-top: 5px;">Supported formats: TXT, CSV, Excel (.xlsx, .xls)</div>
                                    </div>
                                    
                                    <div style="width: 180px;">
                                        <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Selection Mode</label>
                                        <select id="numbers-selection-mode" style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF;">
                                            <option value="all">All Numbers</option>
                                            <option value="random">Random Selection</option>
                                            <option value="percentage">Percentage</option>
                                            <option value="count">Specific Count</option>
                                        </select>
                                    </div>
                                </div>
                                
                                <!-- Selection Options (initially hidden) -->
                                <div id="random-selection-options" style="margin-top: 15px; padding: 12px; background: #222; border-radius: 5px; display: none;">
                                    <div id="count-selector" style="display: none;">
                                        <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Number of Recipients</label>
                                        <div style="display: flex; align-items: center;">
                                            <input type="number" min="1" value="1000" style="width: 120px; padding: 8px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF;">
                                            <span style="margin-left: 10px; color: #AAA; font-size: 13px;">recipients from the list</span>
                                        </div>
                                    </div>
                                    
                                    <div id="percentage-selector" style="display: none;">
                                        <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Percentage of List</label>
                                        <div style="display: flex; align-items: center;">
                                            <input type="number" min="1" max="100" value="50" style="width: 80px; padding: 8px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF;">
                                            <span style="margin-left: 10px; color: #AAA; font-size: 13px;">% of numbers from the list</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                                    <div style="color: #AAA; font-size: 13px;">One number per line or column. International format preferred.</div>
                                    <div id="numbers-count" style="font-weight: bold; color: #FFF; background: #444; padding: 5px 10px; border-radius: 3px;">0 numbers found</div>
                                </div>
                            </div>
                            
                            <!-- Message Content Section -->
                            <div style="margin-bottom: 20px; border: 1px solid #444; border-radius: 5px; padding: 15px;">
                                <h3 style="margin-top: 0; color: #FF6600; font-size: 16px;">Message Content</h3>
                                
                                <div style="display: flex; margin-bottom: 15px;">
                                    <div style="flex: 1; margin-right: 10px;">
                                        <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Message Type</label>
                                        <select id="message-source-select" style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF;">
                                            <option value="single">Single Message</option>
                                            <option value="variations">Message Variations</option>
                                            <option value="csv">Import from CSV</option>
                                        </select>
                                    </div>
                                    <div style="flex: 1;">
                                        <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Include MMS</label>
                                        <div style="display: flex; align-items: center; height: 42px;">
                                            <input type="checkbox" id="include-mms" style="margin-right: 5px;">
                                            <label for="include-mms" style="color: #DDD;">Include images with messages</label>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Single Message Input -->
                                <div id="single-message-input" style="margin-bottom: 15px;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Message Template</label>
                                    <textarea placeholder="Enter your message. Use {name} for recipient name, {team} for local team, etc." style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF; height: 100px; resize: none;"></textarea>
                                </div>
                                
                                <!-- Message Variations Input -->
                                <div id="variations-message-input" style="margin-bottom: 15px; display: none;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Message Variations</label>
                                    <p style="color: #AAA; font-size: 13px; margin-bottom: 10px;">Enter multiple message templates. One will be randomly selected for each recipient.</p>
                                    <textarea placeholder="Enter variation 1" style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF; height: 70px; resize: none; margin-bottom: 10px;"></textarea>
                                    <textarea placeholder="Enter variation 2" style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF; height: 70px; resize: none; margin-bottom: 10px;"></textarea>
                                    <button style="background: #444; color: #DDD; border: none; padding: 5px 15px; border-radius: 3px; cursor: pointer;">+ Add Another Variation</button>
                                </div>
                                
                                <!-- CSV Import Input -->
                                <div id="csv-message-input" style="margin-bottom: 15px; display: none;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Import Messages from CSV</label>
                                    <p style="color: #AAA; font-size: 13px; margin-bottom: 10px;">Upload a CSV file with message templates. Format: One message per row, with optional variables.</p>
                                    <div style="display: flex; align-items: center;">
                                        <input type="file" id="csv-file-input" accept=".csv,.txt,.xlsx,.xls" style="display: none;">
                                        <button onclick="document.getElementById('csv-file-input').click()" style="background: #555; color: white; border: none; padding: 8px 15px; border-radius: 3px; cursor: pointer; margin-right: 10px;">Choose File</button>
                                        <span id="csv-filename" style="color: #AAA; font-size: 13px;">No file chosen</span>
                                    </div>
                                    <div style="margin-top: 10px; padding: 10px; border: 1px dashed #444; border-radius: 5px; background: #222; color: #AAA; font-size: 12px;">
                                        <div style="margin-bottom: 5px; font-weight: bold;">Sample CSV Format:</div>
                                        "Hey {name}! Check out our latest promo on {team} games!"<br>
                                        "Don't miss our special offers for {event} this weekend!"<br>
                                        "Get exclusive odds for the {team} vs {opponent} game this Sunday."
                                    </div>
                                </div>
                                
                                <!-- MMS Upload Section -->
                                <div id="mms-upload-section" style="margin-top: 20px; border-top: 1px solid #444; padding-top: 15px; display: none;">
                                    <label style="display: block; margin-bottom: 10px; font-weight: bold; color: #DDD;">MMS Image Pool Configuration</label>
                                    <p style="color: #AAA; font-size: 13px; margin-bottom: 15px;">Configure image pools for your messages. The system will randomly select images from these pools for each message sent.</p>
                                    
                                    <div style="margin-bottom: 20px; border: 1px solid #444; border-radius: 5px; padding: 15px; background-color: #2A2A2A;">
                                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                            <h3 style="margin: 0; color: #FF6600; font-size: 16px;">Image Pool Source</h3>
                                            <div>
                                                <select id="mms-source-type" style="padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE;">
                                                    <option value="folder">Image Folder</option>
                                                    <option value="individual">Individual Images</option>
                                                    <option value="categories">Category Folders</option>
                                                </select>
                                            </div>
                                        </div>
                                        
                                        <!-- Folder Selection -->
                                        <div id="folder-selection" style="margin-bottom: 15px;">
                                            <div style="display: flex; margin-bottom: 10px;">
                                                <input type="text" placeholder="C:\Images\Marketing" style="flex: 1; padding: 10px; border-radius: 5px 0 0 5px; border: 1px solid #444; background: #333; color: #FFF;">
                                                <button style="background: #555; color: white; border: none; padding: 10px 15px; border-radius: 0 5px 5px 0; cursor: pointer;">Browse</button>
                                            </div>
                                            <div style="display: flex; align-items: center; margin-top: 10px;">
                                                <input type="checkbox" id="include-subfolders" checked style="margin-right: 10px;">
                                                <label for="include-subfolders" style="color: #DDD; font-size: 14px;">Include subfolders</label>
                                            </div>
                                            <div style="margin-top: 15px; color: #AAA; font-size: 13px;">
                                                <div style="margin-bottom: 5px;">Status: 10,562 images found in selected folder</div>
                                                <div style="display: flex; gap: 20px;">
                                                    <div>JPG: 8,741</div>
                                                    <div>PNG: 1,546</div>
                                                    <div>GIF: 275</div>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <!-- Individual Upload (Hidden by default) -->
                                        <div id="individual-upload" style="display: none;">
                                            <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 15px;">
                                                <div style="width: 120px; height: 120px; background: #333; border: 1px dashed #666; border-radius: 5px; display: flex; justify-content: center; align-items: center; cursor: pointer;" onclick="document.getElementById('mms-file-input').click()">
                                                    <span style="font-size: 36px; color: #666;">+</span>
                                                </div>
                                                <div style="width: 120px; height: 120px; background: #333; border-radius: 5px; position: relative; overflow: hidden; display: none;" id="mms-preview-1">
                                                    <div style="position: absolute; top: 5px; right: 5px; background: rgba(0,0,0,0.5); width: 24px; height: 24px; border-radius: 50%; display: flex; justify-content: center; align-items: center; cursor: pointer;">
                                                        <span style="color: #FFF; font-size: 16px;">×</span>
                                                    </div>
                                                    <div style="width: 100%; height: 100%; display: flex; justify-content: center; align-items: center;">
                                                        <img src="" style="max-width: 100%; max-height: 100%;" id="mms-preview-img-1">
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            <input type="file" id="mms-file-input" accept="image/*,.csv,.txt,.xlsx,.xls" style="display: none;" multiple>
                                            <div style="margin-top: 10px;">
                                                <button onclick="document.getElementById('mms-file-input').click()" style="background: #555; color: white; border: none; padding: 8px 15px; border-radius: 3px; cursor: pointer; margin-right: 10px;">Upload Images</button>
                                                <span style="color: #AAA; font-size: 13px;">3 images selected</span>
                                            </div>
                                        </div>
                                        
                                        <!-- Category Folders (Hidden by default) -->
                                        <div id="category-folders" style="display: none;">
                                            <div style="margin-bottom: 15px; color: #DDD; font-size: 14px;">
                                                Configure category folders to use different image types for different messages.
                                            </div>
                                            
                                            <div style="max-height: 300px; overflow-y: auto;">
                                                <div style="border: 1px solid #444; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                                        <div style="font-weight: bold; color: #DDD;">Sports Images</div>
                                                        <div>
                                                            <button style="background: #555; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-size: 12px;">Remove</button>
                                                        </div>
                                                    </div>
                                                    <div style="display: flex;">
                                                        <input type="text" value="C:\Images\Sports" style="flex: 1; padding: 8px; border-radius: 5px 0 0 5px; border: 1px solid #444; background: #333; color: #FFF; font-size: 13px;">
                                                        <button style="background: #555; color: white; border: none; padding: 8px 12px; border-radius: 0 5px 5px 0; cursor: pointer; font-size: 13px;">Browse</button>
                                                    </div>
                                                    <div style="color: #AAA; font-size: 12px; margin-top: 5px;">3,251 images</div>
                                                </div>
                                                
                                                <div style="border: 1px solid #444; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                                        <div style="font-weight: bold; color: #DDD;">Betting Slips</div>
                                                        <div>
                                                            <button style="background: #555; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-size: 12px;">Remove</button>
                                                        </div>
                                                    </div>
                                                    <div style="display: flex;">
                                                        <input type="text" value="C:\Images\Slips" style="flex: 1; padding: 8px; border-radius: 5px 0 0 5px; border: 1px solid #444; background: #333; color: #FFF; font-size: 13px;">
                                                        <button style="background: #555; color: white; border: none; padding: 8px 12px; border-radius: 0 5px 5px 0; cursor: pointer; font-size: 13px;">Browse</button>
                                                    </div>
                                                    <div style="color: #AAA; font-size: 12px; margin-top: 5px;">1,874 images</div>
                                                </div>
                                                
                                                <div style="border: 1px solid #444; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                                        <div style="font-weight: bold; color: #DDD;">Promotional</div>
                                                        <div>
                                                            <button style="background: #555; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-size: 12px;">Remove</button>
                                                        </div>
                                                    </div>
                                                    <div style="display: flex;">
                                                        <input type="text" value="C:\Images\Promo" style="flex: 1; padding: 8px; border-radius: 5px 0 0 5px; border: 1px solid #444; background: #333; color: #FFF; font-size: 13px;">
                                                        <button style="background: #555; color: white; border: none; padding: 8px 12px; border-radius: 0 5px 5px 0; cursor: pointer; font-size: 13px;">Browse</button>
                                                    </div>
                                                    <div style="color: #AAA; font-size: 12px; margin-top: 5px;">5,437 images</div>
                                                </div>
                                            </div>
                                            
                                            <button style="background: #FF6600; color: white; border: none; padding: 8px 15px; border-radius: 3px; cursor: pointer; margin-top: 10px; font-weight: bold;">+ Add Category</button>
                                        </div>
                                    </div>
                                    
                                    <div style="margin-top: 15px;">
                                        <div style="color: #DDD; font-weight: bold; margin-bottom: 5px;">Image Usage Settings</div>
                                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                                            <input type="checkbox" id="random-image-selection" checked style="margin-right: 10px;">
                                            <label for="random-image-selection" style="color: #DDD; font-size: 14px;">Randomly select images from pool</label>
                                        </div>
                                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                                            <input type="checkbox" id="prevent-image-reuse" checked style="margin-right: 10px;">
                                            <label for="prevent-image-reuse" style="color: #DDD; font-size: 14px;">Prevent reusing same image within campaign</label>
                                        </div>
                                        <div style="display: flex; align-items: center;">
                                            <input type="checkbox" id="match-messages-to-categories" style="margin-right: 10px;">
                                            <label for="match-messages-to-categories" style="color: #DDD; font-size: 14px;">Match message keywords to image categories when possible</label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Throttling Settings Section -->
                            <div style="margin-bottom: 20px; border: 1px solid #444; border-radius: 5px; padding: 15px;">
                                <h3 style="margin-top: 0; color: #FF6600; font-size: 16px;">Throttling Settings</h3>
                                
                                <div style="display: flex; margin-bottom: 15px;">
                                    <div style="flex: 1; margin-right: 15px;">
                                        <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Messages per Account per Day</label>
                                        <input type="number" min="1" max="1000" value="100" style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF;">
                                    </div>
                                    <div style="flex: 1;">
                                        <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Messages per Account per Hour</label>
                                        <input type="number" min="1" max="100" value="15" style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF;">
                                    </div>
                                </div>
                                
                                <div style="display: flex; margin-bottom: 15px;">
                                    <div style="flex: 1; margin-right: 15px;">
                                        <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Min Delay Between Messages (seconds)</label>
                                        <input type="number" min="1" max="300" value="10" style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF;">
                                    </div>
                                    <div style="flex: 1;">
                                        <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Max Delay Between Messages (seconds)</label>
                                        <input type="number" min="1" max="600" value="60" style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF;">
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Distribution Pattern</label>
                                    <select style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF;">
                                        <option value="even">Even Distribution (Default)</option>
                                        <option value="random">Random Distribution</option>
                                        <option value="peak">Peak Hours Weighted</option>
                                        <option value="graduated">Gradually Increasing</option>
                                    </select>
                                </div>
                                
                                <div style="margin-bottom: 5px;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Active Hours</label>
                                    <div style="display: flex; align-items: center;">
                                        <input type="text" value="08:00" style="width: 80px; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF; text-align: center;">
                                        <span style="margin: 0 10px; color: #AAA;">to</span>
                                        <input type="text" value="20:00" style="width: 80px; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF; text-align: center;">
                                    </div>
                                </div>
                                
                                <div style="margin-top: 15px;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Active Days</label>
                                    <div style="display: flex; flex-wrap: wrap;">
                                        <div style="margin-right: 15px; margin-bottom: 10px; display: flex; align-items: center;">
                                            <input type="checkbox" id="day-mon" checked style="margin-right: 5px;">
                                            <label for="day-mon" style="color: #DDD; font-size: 14px;">Monday</label>
                                        </div>
                                        <div style="margin-right: 15px; margin-bottom: 10px; display: flex; align-items: center;">
                                            <input type="checkbox" id="day-tue" checked style="margin-right: 5px;">
                                            <label for="day-tue" style="color: #DDD; font-size: 14px;">Tuesday</label>
                                        </div>
                                        <div style="margin-right: 15px; margin-bottom: 10px; display: flex; align-items: center;">
                                            <input type="checkbox" id="day-wed" checked style="margin-right: 5px;">
                                            <label for="day-wed" style="color: #DDD; font-size: 14px;">Wednesday</label>
                                        </div>
                                        <div style="margin-right: 15px; margin-bottom: 10px; display: flex; align-items: center;">
                                            <input type="checkbox" id="day-thu" checked style="margin-right: 5px;">
                                            <label for="day-thu" style="color: #DDD; font-size: 14px;">Thursday</label>
                                        </div>
                                        <div style="margin-right: 15px; margin-bottom: 10px; display: flex; align-items: center;">
                                            <input type="checkbox" id="day-fri" checked style="margin-right: 5px;">
                                            <label for="day-fri" style="color: #DDD; font-size: 14px;">Friday</label>
                                        </div>
                                        <div style="margin-right: 15px; margin-bottom: 10px; display: flex; align-items: center;">
                                            <input type="checkbox" id="day-sat" checked style="margin-right: 5px;">
                                            <label for="day-sat" style="color: #DDD; font-size: 14px;">Saturday</label>
                                        </div>
                                        <div style="margin-bottom: 10px; display: flex; align-items: center;">
                                            <input type="checkbox" id="day-sun" checked style="margin-right: 5px;">
                                            <label for="day-sun" style="color: #DDD; font-size: 14px;">Sunday</label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Sender Account Selection -->
                            <div style="margin-bottom: 20px; border: 1px solid #444; border-radius: 5px; padding: 15px;">
                                <h3 style="margin-top: 0; color: #FF6600; font-size: 16px;">Sender Account Selection</h3>
                                <p style="color: #AAA; font-size: 13px; margin-bottom: 15px;">Choose which accounts to use for sending messages in this campaign.</p>
                                
                                <div style="margin-bottom: 15px;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Selection Method</label>
                                    <select id="sender-selection-method" style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF;">
                                        <option value="all">All Available Accounts</option>
                                        <option value="area-codes">Specific Area Codes</option>
                                        <option value="account-age">Account Age</option>
                                        <option value="health-score">Health Score</option>
                                        <option value="custom">Custom Selection</option>
                                    </select>
                                </div>
                                
                                <!-- Area Code Selection (initially hidden) -->
                                <div id="area-code-selection" style="display: block; margin-top: 15px;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Area Codes</label>
                                    <p style="color: #AAA; font-size: 13px; margin-bottom: 10px;">Select which area codes to use for sending messages.</p>
                                    
                                    <!-- Search box for area codes -->
                                    <div style="margin-bottom: 15px; position: relative;">
                                        <input type="text" placeholder="Search area codes..." id="area-code-search" style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #333; color: #FFF; padding-left: 35px;">
                                        <div style="position: absolute; left: 10px; top: 10px; color: #AAA;">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                                <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
                                            </svg>
                                        </div>
                                    </div>
                                    
                                    <!-- Area codes list with scrollable container -->
                                    <div style="max-height: 250px; overflow-y: auto; border: 1px solid #444; border-radius: 5px; padding: 10px; background: #222; margin-bottom: 15px;">
                                        <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                                            <!-- Florida area codes (prioritized) -->
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-954" checked style="margin-right: 8px;">
                                                <label for="area-954" style="color: #DDD; font-size: 14px;">954 (Florida)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">2,471</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-754" checked style="margin-right: 8px;">
                                                <label for="area-754" style="color: #DDD; font-size: 14px;">754 (Florida)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">1,853</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-305" checked style="margin-right: 8px;">
                                                <label for="area-305" style="color: #DDD; font-size: 14px;">305 (Florida)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">1,762</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-786" checked style="margin-right: 8px;">
                                                <label for="area-786" style="color: #DDD; font-size: 14px;">786 (Florida)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">1,289</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-561" checked style="margin-right: 8px;">
                                                <label for="area-561" style="color: #DDD; font-size: 14px;">561 (Florida)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">918</span>
                                            </div>
                                            
                                            <!-- Other states area codes -->
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-404" style="margin-right: 8px;">
                                                <label for="area-404" style="color: #DDD; font-size: 14px;">404 (Georgia)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">487</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-702" style="margin-right: 8px;">
                                                <label for="area-702" style="color: #DDD; font-size: 14px;">702 (Nevada)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">342</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-213" style="margin-right: 8px;">
                                                <label for="area-213" style="color: #DDD; font-size: 14px;">213 (California)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">189</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-312" style="margin-right: 8px;">
                                                <label for="area-312" style="color: #DDD; font-size: 14px;">312 (Illinois)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">156</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-212" style="margin-right: 8px;">
                                                <label for="area-212" style="color: #DDD; font-size: 14px;">212 (New York)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">143</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-415" style="margin-right: 8px;">
                                                <label for="area-415" style="color: #DDD; font-size: 14px;">415 (California)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">112</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-214" style="margin-right: 8px;">
                                                <label for="area-214" style="color: #DDD; font-size: 14px;">214 (Texas)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">97</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-202" style="margin-right: 8px;">
                                                <label for="area-202" style="color: #DDD; font-size: 14px;">202 (DC)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">85</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-516" style="margin-right: 8px;">
                                                <label for="area-516" style="color: #DDD; font-size: 14px;">516 (New York)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">64</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-609" style="margin-right: 8px;">
                                                <label for="area-609" style="color: #DDD; font-size: 14px;">609 (New Jersey)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">47</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-201" style="margin-right: 8px;">
                                                <label for="area-201" style="color: #DDD; font-size: 14px;">201 (New Jersey)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">38</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-551" style="margin-right: 8px;">
                                                <label for="area-551" style="color: #DDD; font-size: 14px;">551 (New Jersey)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">24</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-856" style="margin-right: 8px;">
                                                <label for="area-856" style="color: #DDD; font-size: 14px;">856 (New Jersey)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">12</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-973" style="margin-right: 8px;">
                                                <label for="area-973" style="color: #DDD; font-size: 14px;">973 (New Jersey)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">8</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-732" style="margin-right: 8px;">
                                                <label for="area-732" style="color: #DDD; font-size: 14px;">732 (New Jersey)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">5</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-908" style="margin-right: 8px;">
                                                <label for="area-908" style="color: #DDD; font-size: 14px;">908 (New Jersey)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">3</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-862" style="margin-right: 8px;">
                                                <label for="area-862" style="color: #DDD; font-size: 14px;">862 (New Jersey)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">2</span>
                                            </div>
                                            <div style="background: #333; border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;">
                                                <input type="checkbox" id="area-848" style="margin-right: 8px;">
                                                <label for="area-848" style="color: #DDD; font-size: 14px;">848 (New Jersey)</label>
                                                <span style="margin-left: 8px; background: #555; padding: 2px 6px; border-radius: 10px; font-size: 12px; color: #AAA;">1</span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <!-- State-based Filters -->
                                    <div style="margin-bottom: 15px;">
                                        <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">State Filters</label>
                                        <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 10px;">
                                            <button id="select-all-areas" style="background: #444; color: #EEE; border: none; padding: 6px 12px; border-radius: 3px; cursor: pointer; font-size: 13px;">All States</button>
                                            <button id="select-florida-only" style="background: #444; color: #EEE; border: none; padding: 6px 12px; border-radius: 3px; cursor: pointer; font-size: 13px;">Florida</button>
                                            <button id="select-new-jersey-only" style="background: #444; color: #EEE; border: none; padding: 6px 12px; border-radius: 3px; cursor: pointer; font-size: 13px;">New Jersey</button>
                                            <button id="select-new-york-only" style="background: #444; color: #EEE; border: none; padding: 6px 12px; border-radius: 3px; cursor: pointer; font-size: 13px;">New York</button>
                                            <button id="select-california-only" style="background: #444; color: #EEE; border: none; padding: 6px 12px; border-radius: 3px; cursor: pointer; font-size: 13px;">California</button>
                                            <button id="select-texas-only" style="background: #444; color: #EEE; border: none; padding: 6px 12px; border-radius: 3px; cursor: pointer; font-size: 13px;">Texas</button>
                                            <button id="select-georgia-only" style="background: #444; color: #EEE; border: none; padding: 6px 12px; border-radius: 3px; cursor: pointer; font-size: 13px;">Georgia</button>
                                            <button id="select-illinois-only" style="background: #444; color: #EEE; border: none; padding: 6px 12px; border-radius: 3px; cursor: pointer; font-size: 13px;">Illinois</button>
                                            <button id="select-nevada-only" style="background: #444; color: #EEE; border: none; padding: 6px 12px; border-radius: 3px; cursor: pointer; font-size: 13px;">Nevada</button>
                                            <div class="dropdown" style="position: relative; display: inline-block;">
                                                <button style="background: #444; color: #EEE; border: none; padding: 6px 12px; border-radius: 3px; cursor: pointer; font-size: 13px; display: flex; align-items: center;">
                                                    More States
                                                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" viewBox="0 0 16 16" style="margin-left: 5px;">
                                                        <path d="M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z"/>
                                                    </svg>
                                                </button>
                                                <div class="dropdown-content" style="display: none; position: absolute; background-color: #222; min-width: 150px; box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.5); z-index: 1; border-radius: 3px; border: 1px solid #444;">
                                                    <button style="width: 100%; text-align: left; padding: 8px 12px; border: none; background: transparent; color: #DDD; cursor: pointer; font-size: 13px;">Pennsylvania</button>
                                                    <button style="width: 100%; text-align: left; padding: 8px 12px; border: none; background: transparent; color: #DDD; cursor: pointer; font-size: 13px;">Ohio</button>
                                                    <button style="width: 100%; text-align: left; padding: 8px 12px; border: none; background: transparent; color: #DDD; cursor: pointer; font-size: 13px;">Michigan</button>
                                                    <button style="width: 100%; text-align: left; padding: 8px 12px; border: none; background: transparent; color: #DDD; cursor: pointer; font-size: 13px;">Washington</button>
                                                    <button style="width: 100%; text-align: left; padding: 8px 12px; border: none; background: transparent; color: #DDD; cursor: pointer; font-size: 13px;">Colorado</button>
                                                    <button style="width: 100%; text-align: left; padding: 8px 12px; border: none; background: transparent; color: #DDD; cursor: pointer; font-size: 13px;">Arizona</button>
                                                    <button style="width: 100%; text-align: left; padding: 8px 12px; border: none; background: transparent; color: #DDD; cursor: pointer; font-size: 13px;">District of Columbia</button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div style="display: flex; align-items: center; margin-top: 15px; justify-content: space-between;">
                                        <div style="display: flex; align-items: center;">
                                            <button id="unselect-all" style="background: #333; color: #DDD; border: 1px solid #555; padding: 6px 12px; border-radius: 3px; cursor: pointer; margin-right: 10px; font-size: 13px;">Unselect All</button>
                                            <button id="invert-selection" style="background: #333; color: #DDD; border: 1px solid #555; padding: 6px 12px; border-radius: 3px; cursor: pointer; font-size: 13px;">Invert Selection</button>
                                        </div>
                                        <span style="color: #AAA; font-size: 13px; font-weight: bold;">8,123 accounts selected of 10,000 total</span>
                                    </div>
                                </div>
                                
                                <!-- Account Age Selection (hidden by default) -->
                                <div id="account-age-selection" style="display: none; margin-top: 15px;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Account Age</label>
                                    <p style="color: #AAA; font-size: 13px; margin-bottom: 10px;">Select accounts based on their age.</p>
                                    
                                    <div style="display: flex; align-items: center; margin-bottom: 15px;">
                                        <div style="margin-right: 20px; display: flex; align-items: center;">
                                            <input type="checkbox" id="age-new" checked style="margin-right: 8px;">
                                            <label for="age-new" style="color: #DDD; font-size: 14px;">New (0-7 days)</label>
                                        </div>
                                        <div style="margin-right: 20px; display: flex; align-items: center;">
                                            <input type="checkbox" id="age-recent" checked style="margin-right: 8px;">
                                            <label for="age-recent" style="color: #DDD; font-size: 14px;">Recent (8-30 days)</label>
                                        </div>
                                        <div style="margin-right: 20px; display: flex; align-items: center;">
                                            <input type="checkbox" id="age-established" checked style="margin-right: 8px;">
                                            <label for="age-established" style="color: #DDD; font-size: 14px;">Established (31+ days)</label>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Health Score Selection (hidden by default) -->
                                <div id="health-score-selection" style="display: none; margin-top: 15px;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Health Score</label>
                                    <p style="color: #AAA; font-size: 13px; margin-bottom: 10px;">Select accounts based on their health and activity metrics.</p>
                                    
                                    <div style="display: flex; align-items: center; margin-bottom: 15px;">
                                        <div style="margin-right: 20px; display: flex; align-items: center;">
                                            <input type="checkbox" id="health-excellent" checked style="margin-right: 8px;">
                                            <label for="health-excellent" style="color: #DDD; font-size: 14px;">Excellent (90-100)</label>
                                        </div>
                                        <div style="margin-right: 20px; display: flex; align-items: center;">
                                            <input type="checkbox" id="health-good" checked style="margin-right: 8px;">
                                            <label for="health-good" style="color: #DDD; font-size: 14px;">Good (70-89)</label>
                                        </div>
                                        <div style="margin-right: 20px; display: flex; align-items: center;">
                                            <input type="checkbox" id="health-fair" style="margin-right: 8px;">
                                            <label for="health-fair" style="color: #DDD; font-size: 14px;">Fair (50-69)</label>
                                        </div>
                                        <div style="margin-right: 20px; display: flex; align-items: center;">
                                            <input type="checkbox" id="health-poor" style="margin-right: 8px;">
                                            <label for="health-poor" style="color: #DDD; font-size: 14px;">Poor (<50)</label>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Custom Account Selection (hidden by default) -->
                                <div id="custom-account-selection" style="display: none; margin-top: 15px;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #DDD;">Custom Selection</label>
                                    <p style="color: #AAA; font-size: 13px; margin-bottom: 10px;">Manually select specific accounts to use.</p>
                                    
                                    <div style="display: flex; flex-direction: column; max-height: 200px; overflow-y: auto; border: 1px solid #444; border-radius: 5px; padding: 10px; background: #222;">
                                        <div style="display: flex; align-items: center; padding: 8px; border-bottom: 1px solid #333;">
                                            <input type="checkbox" style="margin-right: 10px;">
                                            <div style="display: flex; flex: 1; justify-content: space-between;">
                                                <span style="color: #DDD; font-size: 14px;">+1 (954) 555-1234</span>
                                                <span style="color: #AAA; font-size: 13px;">42 days old | 95% health</span>
                                            </div>
                                        </div>
                                        <div style="display: flex; align-items: center; padding: 8px; border-bottom: 1px solid #333;">
                                            <input type="checkbox" style="margin-right: 10px;">
                                            <div style="display: flex; flex: 1; justify-content: space-between;">
                                                <span style="color: #DDD; font-size: 14px;">+1 (754) 555-2345</span>
                                                <span style="color: #AAA; font-size: 13px;">29 days old | 88% health</span>
                                            </div>
                                        </div>
                                        <div style="display: flex; align-items: center; padding: 8px; border-bottom: 1px solid #333;">
                                            <input type="checkbox" style="margin-right: 10px;">
                                            <div style="display: flex; flex: 1; justify-content: space-between;">
                                                <span style="color: #DDD; font-size: 14px;">+1 (305) 555-3456</span>
                                                <span style="color: #AAA; font-size: 13px;">15 days old | 92% health</span>
                                            </div>
                                        </div>
                                        <div style="display: flex; align-items: center; padding: 8px; border-bottom: 1px solid #333;">
                                            <input type="checkbox" style="margin-right: 10px;">
                                            <div style="display: flex; flex: 1; justify-content: space-between;">
                                                <span style="color: #DDD; font-size: 14px;">+1 (786) 555-4567</span>
                                                <span style="color: #AAA; font-size: 13px;">7 days old | 85% health</span>
                                            </div>
                                        </div>
                                        <div style="display: flex; align-items: center; padding: 8px;">
                                            <input type="checkbox" style="margin-right: 10px;">
                                            <div style="display: flex; flex: 1; justify-content: space-between;">
                                                <span style="color: #DDD; font-size: 14px;">+1 (561) 555-5678</span>
                                                <span style="color: #AAA; font-size: 13px;">3 days old | 97% health</span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div style="margin-top: 10px; color: #AAA; font-size: 13px; text-align: right;">
                                        Showing 5 of 10,000 accounts. Use filters to narrow down.
                                    </div>
                                </div>
                            </div>
                            
                            <div style="display: flex; justify-content: flex-end; margin-top: 30px;">
                                <button id="cancel-campaign" style="background: #444; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-right: 10px;">Cancel</button>
                                <button id="create-campaign" style="background: #FF6600; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold;">Create Campaign</button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="campaign-filters">
                        <label class="filter-label">Status</label>
                        <div class="filter-options">
                            <div class="filter-checkbox">
                                <input type="checkbox" id="status-active" checked>
                                <label for="status-active">Active</label>
                            </div>
                            <div class="filter-checkbox">
                                <input type="checkbox" id="status-draft" checked>
                                <label for="status-draft">Draft</label>
                            </div>
                            <div class="filter-checkbox">
                                <input type="checkbox" id="status-completed" checked>
                                <label for="status-completed">Completed</label>
                            </div>
                        </div>
                        
                        <label class="filter-label" style="margin-top: 15px;">Sort By</label>
                        <select class="filter-select">
                            <option value="created_newest">Created Date (Newest)</option>
                            <option value="created_oldest">Created Date (Oldest)</option>
                            <option value="name_az">Name (A-Z)</option>
                            <option value="name_za">Name (Z-A)</option>
                            <option value="progress">Progress</option>
                        </select>
                    </div>
                    
                    <div style="color: #AAA; font-size: 14px; margin-top: 30px;">
                        <div style="margin-bottom: 10px; font-weight: bold;">Quick Stats</div>
                        <div style="margin-bottom: 5px;">Active Campaigns: 1</div>
                        <div style="margin-bottom: 5px;">Messages Today: 1,245</div>
                        <div style="margin-bottom: 5px;">Total Messages: 32,500</div>
                        <div style="margin-bottom: 20px;">Response Rate: 18%</div>
                        
                        <div style="height: 8px; background-color: #444; border-radius: 4px; overflow: hidden; margin-bottom: 5px;">
                            <div style="height: 100%; background-color: #FF6600; width: 35%"></div>
                        </div>
                        <div style="font-size: 12px; color: #888;">Daily Target: 35%</div>
                    </div>
                </div>
                
                <div class="campaigns-right">
                    <div class="campaigns-search">
                        <input type="text" class="search-input" placeholder="Search campaigns...">
                        <button class="search-button">Search</button>
                    </div>
                    
                    <div class="campaign-list">
                        <div class="campaign-item">
                            <div class="campaign-header">
                                <div class="campaign-name">March Madness Promotion</div>
                                <div class="campaign-status status-active">Active</div>
                            </div>
                            <div class="campaign-details">Target: 10,000 messages</div>
                            <div class="campaign-progress-container">
                                <div class="campaign-progress-fill" style="width: 35%"></div>
                            </div>
                            <div class="campaign-stats">
                                <div class="campaign-stat">Completed: 3,500</div>
                                <div class="campaign-stat">Remaining: 6,500</div>
                            </div>
                            <div class="campaign-actions">
                                <a href="/dashboard" class="campaign-button">Accounts</a>
                                <a href="#" class="campaign-button">Message</a>
                                <a href="/campaign_schedule" class="campaign-button btn-primary">Schedule</a>
                            </div>
                        </div>
                        
                        <div class="campaign-item">
                            <div class="campaign-header">
                                <div class="campaign-name">NFL Week 1 Special</div>
                                <div class="campaign-status status-draft">Draft</div>
                            </div>
                            <div class="campaign-details">Target: 5,000 messages</div>
                            <div class="campaign-progress-container">
                                <div class="campaign-progress-fill" style="width: 0%"></div>
                            </div>
                            <div class="campaign-stats">
                                <div class="campaign-stat">Completed: 0</div>
                                <div class="campaign-stat">Remaining: 5,000</div>
                            </div>
                            <div class="campaign-actions">
                                <a href="/dashboard" class="campaign-button">Accounts</a>
                                <a href="#" class="campaign-button">Message</a>
                                <a href="/campaign_schedule" class="campaign-button btn-primary">Schedule</a>
                            </div>
                        </div>
                        
                        <div class="campaign-item">
                            <div class="campaign-header">
                                <div class="campaign-name">Welcome Bonus Campaign</div>
                                <div class="campaign-status status-completed">Completed</div>
                            </div>
                            <div class="campaign-details">Target: 2,000 messages</div>
                            <div class="campaign-progress-container">
                                <div class="campaign-progress-fill" style="width: 100%"></div>
                            </div>
                            <div class="campaign-stats">
                                <div class="campaign-stat">Completed: 2,000</div>
                                <div class="campaign-stat">Remaining: 0</div>
                            </div>
                            <div class="campaign-actions">
                                <a href="/dashboard" class="campaign-button">Accounts</a>
                                <a href="#" class="campaign-button">Message</a>
                                <a href="/campaign_schedule" class="campaign-button">Report</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="app-footer">
                © PB BETTING™ | ProgressGhostCreator v1.0.0 | Campaigns: 3 | Messages Today: 1,245
            </div>
        </div>
        
        <script>
            // Campaign Modal Functionality
            document.getElementById('new-campaign-btn').addEventListener('click', function() {
                document.getElementById('campaign-modal').style.display = 'flex';
            });
            
            document.getElementById('close-modal').addEventListener('click', function() {
                document.getElementById('campaign-modal').style.display = 'none';
            });
            
            document.getElementById('cancel-campaign').addEventListener('click', function() {
                document.getElementById('campaign-modal').style.display = 'none';
            });
            
            // Message Type Selection
            document.getElementById('message-source-select').addEventListener('change', function() {
                const selectedType = this.value;
                
                // Hide all message input types
                document.getElementById('single-message-input').style.display = 'none';
                document.getElementById('variations-message-input').style.display = 'none';
                document.getElementById('csv-message-input').style.display = 'none';
                
                // Show the selected input type
                if (selectedType === 'single') {
                    document.getElementById('single-message-input').style.display = 'block';
                } else if (selectedType === 'variations') {
                    document.getElementById('variations-message-input').style.display = 'block';
                } else if (selectedType === 'csv') {
                    document.getElementById('csv-message-input').style.display = 'block';
                }
            });
            
            // MMS Checkbox Toggle
            document.getElementById('include-mms').addEventListener('change', function() {
                document.getElementById('mms-upload-section').style.display = this.checked ? 'block' : 'none';
            });
            
            // CSV File Input
            document.getElementById('csv-file-input').addEventListener('change', function() {
                if (this.files.length > 0) {
                    document.getElementById('csv-filename').textContent = this.files[0].name;
                } else {
                    document.getElementById('csv-filename').textContent = 'No file chosen';
                }
            });
            
            // MMS File Input
            document.getElementById('mms-file-input').addEventListener('change', function() {
                if (this.files.length > 0) {
                    const file = this.files[0];
                    const previewElement = document.getElementById('mms-preview-1');
                    const previewImg = document.getElementById('mms-preview-img-1');
                    
                    // Show preview
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        previewImg.src = e.target.result;
                        previewElement.style.display = 'block';
                    };
                    reader.readAsDataURL(file);
                }
            });
            
            // MMS Source Type Selection
            document.getElementById('mms-source-type').addEventListener('change', function() {
                const selectedType = this.value;
                
                // Hide all source types
                document.getElementById('folder-selection').style.display = 'none';
                document.getElementById('individual-upload').style.display = 'none';
                document.getElementById('category-folders').style.display = 'none';
                
                // Show the selected source type
                if (selectedType === 'folder') {
                    document.getElementById('folder-selection').style.display = 'block';
                } else if (selectedType === 'individual') {
                    document.getElementById('individual-upload').style.display = 'block';
                } else if (selectedType === 'categories') {
                    document.getElementById('category-folders').style.display = 'block';
                }
            });
            
            // Phone Numbers File Upload
            document.getElementById('numbers-file').addEventListener('change', function() {
                if (this.files.length > 0) {
                    const file = this.files[0];
                    document.getElementById('numbers-file-display').value = file.name;
                    // Simulate reading file content
                    const phoneCount = Math.floor(Math.random() * 50000) + 10000; // Random number between 10,000 and 60,000
                    document.getElementById('numbers-count').textContent = phoneCount.toLocaleString() + ' numbers found';
                }
            });
            
            // Phone Number Selection Mode
            document.getElementById('numbers-selection-mode').addEventListener('change', function() {
                const selectedMode = this.value;
                
                // Hide all selection options
                document.getElementById('random-selection-options').style.display = 'none';
                document.getElementById('count-selector').style.display = 'none';
                document.getElementById('percentage-selector').style.display = 'none';
                
                // Show relevant options based on selection mode
                if (selectedMode === 'count') {
                    document.getElementById('random-selection-options').style.display = 'block';
                    document.getElementById('count-selector').style.display = 'block';
                } else if (selectedMode === 'percentage') {
                    document.getElementById('random-selection-options').style.display = 'block';
                    document.getElementById('percentage-selector').style.display = 'block';
                } else if (selectedMode === 'random') {
                    document.getElementById('random-selection-options').style.display = 'block';
                    document.getElementById('count-selector').style.display = 'block';
                }
            });
            
            // Sender Account Selection Method
            document.getElementById('sender-selection-method').addEventListener('change', function() {
                const selectedMethod = this.value;
                
                // Hide all selection options
                document.getElementById('area-code-selection').style.display = 'none';
                document.getElementById('account-age-selection').style.display = 'none';
                document.getElementById('health-score-selection').style.display = 'none';
                document.getElementById('custom-account-selection').style.display = 'none';
                
                // Show relevant options based on selection method
                if (selectedMethod === 'area-codes') {
                    document.getElementById('area-code-selection').style.display = 'block';
                } else if (selectedMethod === 'account-age') {
                    document.getElementById('account-age-selection').style.display = 'block';
                } else if (selectedMethod === 'health-score') {
                    document.getElementById('health-score-selection').style.display = 'block';
                } else if (selectedMethod === 'custom') {
                    document.getElementById('custom-account-selection').style.display = 'block';
                }
            });
            
            // Area code and state selection functionality
            document.getElementById('select-all-areas').addEventListener('click', function() {
                // Select all area codes
                const checkboxes = document.querySelectorAll('input[id^="area-"]');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = true;
                });
            });
            
            document.getElementById('unselect-all').addEventListener('click', function() {
                // Unselect all area codes
                const checkboxes = document.querySelectorAll('input[id^="area-"]');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
            });
            
            document.getElementById('invert-selection').addEventListener('click', function() {
                // Invert the current selection
                const checkboxes = document.querySelectorAll('input[id^="area-"]');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = !checkbox.checked;
                });
            });
            
            // State filter buttons
            document.getElementById('select-florida-only').addEventListener('click', function() {
                // First unselect all
                const checkboxes = document.querySelectorAll('input[id^="area-"]');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
                
                // Then select only Florida area codes
                document.getElementById('area-954').checked = true;
                document.getElementById('area-754').checked = true;
                document.getElementById('area-305').checked = true;
                document.getElementById('area-786').checked = true;
                document.getElementById('area-561').checked = true;
            });
            
            document.getElementById('select-new-jersey-only').addEventListener('click', function() {
                // First unselect all
                const checkboxes = document.querySelectorAll('input[id^="area-"]');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
                
                // Then select only New Jersey area codes
                document.getElementById('area-201').checked = true;
                document.getElementById('area-551').checked = true;
                document.getElementById('area-609').checked = true;
                document.getElementById('area-856').checked = true;
                document.getElementById('area-732').checked = true;
                document.getElementById('area-908').checked = true;
                document.getElementById('area-862').checked = true;
                document.getElementById('area-848').checked = true;
                document.getElementById('area-973').checked = true;
            });
            
            document.getElementById('select-new-york-only').addEventListener('click', function() {
                // First unselect all
                const checkboxes = document.querySelectorAll('input[id^="area-"]');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
                
                // Then select only New York area codes
                document.getElementById('area-212').checked = true;
                document.getElementById('area-516').checked = true;
            });
            
            document.getElementById('select-california-only').addEventListener('click', function() {
                // First unselect all
                const checkboxes = document.querySelectorAll('input[id^="area-"]');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
                
                // Then select only California area codes
                document.getElementById('area-213').checked = true;
                document.getElementById('area-415').checked = true;
            });
            
            document.getElementById('select-texas-only').addEventListener('click', function() {
                // First unselect all
                const checkboxes = document.querySelectorAll('input[id^="area-"]');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
                
                // Then select only Texas area codes
                document.getElementById('area-214').checked = true;
            });
            
            document.getElementById('select-georgia-only').addEventListener('click', function() {
                // First unselect all
                const checkboxes = document.querySelectorAll('input[id^="area-"]');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
                
                // Then select only Georgia area codes
                document.getElementById('area-404').checked = true;
            });
            
            document.getElementById('select-illinois-only').addEventListener('click', function() {
                // First unselect all
                const checkboxes = document.querySelectorAll('input[id^="area-"]');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
                
                // Then select only Illinois area codes
                document.getElementById('area-312').checked = true;
            });
            
            document.getElementById('select-nevada-only').addEventListener('click', function() {
                // First unselect all
                const checkboxes = document.querySelectorAll('input[id^="area-"]');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
                
                // Then select only Nevada area codes
                document.getElementById('area-702').checked = true;
            });
            
            // More States dropdown toggle
            const dropdown = document.querySelector('.dropdown button');
            const dropdownContent = document.querySelector('.dropdown-content');
            
            dropdown.addEventListener('click', function(e) {
                e.stopPropagation();
                if (dropdownContent.style.display === 'block') {
                    dropdownContent.style.display = 'none';
                } else {
                    dropdownContent.style.display = 'block';
                }
            });
            
            // Close dropdown when clicking elsewhere
            document.addEventListener('click', function() {
                if (dropdownContent.style.display === 'block') {
                    dropdownContent.style.display = 'none';
                }
            });
            
            // Prevent closing dropdown when clicking inside it
            dropdownContent.addEventListener('click', function(e) {
                e.stopPropagation();
            });
            
            // Area code search functionality
            document.getElementById('area-code-search').addEventListener('input', function() {
                const searchText = this.value.toLowerCase();
                const areaCodeDivs = document.querySelectorAll('div[style*="border-radius: 5px; padding: 10px 15px; display: flex; align-items: center;"]');
                
                areaCodeDivs.forEach(div => {
                    const label = div.querySelector('label');
                    if (label && label.textContent.toLowerCase().includes(searchText)) {
                        div.style.display = 'flex';
                    } else {
                        div.style.display = 'none';
                    }
                });
            });
            
            // Create Campaign
            document.getElementById('create-campaign').addEventListener('click', function() {
                // Simulate campaign creation
                alert('Campaign created successfully! You can now schedule it to start sending messages.');
                document.getElementById('campaign-modal').style.display = 'none';
            });
        </script>
    </body>
    </html>
    ''', logo_exists=os.path.exists("static/progress_logo.png"))

@app.route('/message-dashboard')
def message_dashboard_route():
    """The message monitoring dashboard interface"""
    process_assets()
    nav_menu = get_nav_menu('/message-dashboard')
    return message_dashboard_page(logo_exists=os.path.exists("static/progress_logo.png"), nav_menu=nav_menu)

@app.route('/image-dashboard')
def image_dashboard_route():
    """The image management dashboard interface"""
    process_assets()
    nav_menu = get_nav_menu('/image-dashboard')
    return image_dashboard_page(logo_exists=os.path.exists("static/progress_logo.png"), nav_menu=nav_menu)

@app.route('/account-health')
def account_health_route():
    """The account health monitoring dashboard interface"""
    process_assets()
    nav_menu = get_nav_menu('/account-health')
    return account_health_dashboard_page(logo_exists=os.path.exists("static/progress_logo.png"), nav_menu=nav_menu)

@app.route('/voicemail-manager')
def voicemail_manager_route():
    """The voicemail management interface"""
    process_assets()
    nav_menu = get_nav_menu('/voicemail-manager')
    return voicemail_manager_page(logo_exists=os.path.exists("static/progress_logo.png"), nav_menu=nav_menu)

@app.route('/campaign_schedule')
def campaign_schedule_route():
    """The campaign scheduling interface"""
    process_assets()
    logo_exists = os.path.exists("static/progress_logo.png")
    nav_menu = get_nav_menu('/campaign_schedule')
    from campaign_schedule import campaign_schedule_page
    return campaign_schedule_page(logo_exists=logo_exists, nav_menu=nav_menu)
        <title>ProgressGhostCreator - Campaign Schedule</title>
        <style>
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
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ProgressGhostCreator - Manual Messaging</title>
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
            
            .app-content {
                display: flex;
                flex: 1;
                overflow: hidden;
            }
            
            .accounts-panel {
                width: 250px;
                background-color: #2A2A2A;
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
            
            .messaging-panel {
                flex: 1;
                display: flex;
                flex-direction: column;
                padding: 20px;
            }
            
            .panel-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            
            .panel-title {
                font-size: 18px;
                font-weight: bold;
            }
            
            .recipient-section {
                background-color: #2A2A2A;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 15px;
            }
            
            .section-title {
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 10px;
                color: #EEE;
            }
            
            .recipient-input {
                width: 100%;
                height: 100px;
                padding: 10px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 14px;
                resize: none;
                font-family: monospace;
            }
            
            .recipient-hint {
                font-size: 12px;
                color: #AAA;
                margin-top: 5px;
            }
            
            .message-section {
                background-color: #2A2A2A;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 15px;
                flex: 1;
                display: flex;
                flex-direction: column;
            }
            
            .message-input {
                width: 100%;
                flex: 1;
                padding: 10px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 14px;
                resize: none;
                font-family: Arial, sans-serif;
                margin-bottom: 10px;
            }
            
            .send-options {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .send-from {
                display: flex;
                align-items: center;
            }
            
            .send-label {
                margin-right: 10px;
                font-size: 14px;
                color: #CCC;
            }
            
            .send-select {
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 14px;
            }
            
            .send-button {
                background-color: #FF6600;
                color: white;
                border: none;
                padding: 10px 20px;
                cursor: pointer;
                border-radius: 4px;
                font-weight: bold;
            }
            
            .send-button:hover {
                background-color: #FF7722;
            }
            
            .stats-panel {
                width: 250px;
                background-color: #2A2A2A;
                border-left: 1px solid #444;
                padding: 15px;
                overflow-y: auto;
            }
            
            .stats-header {
                font-weight: bold;
                margin-bottom: 15px;
                border-bottom: 1px solid #444;
                padding-bottom: 10px;
            }
            
            .stat-group {
                margin-bottom: 20px;
            }
            
            .stat-title {
                font-size: 13px;
                color: #CCC;
                margin-bottom: 5px;
            }
            
            .stat-value {
                font-size: 18px;
                font-weight: bold;
                color: #EEE;
            }
            
            .stat-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            
            .stat-label {
                font-size: 13px;
                color: #AAA;
            }
            
            .account-filter {
                margin-top: 10px;
                font-size: 13px;
                color: #AAA;
                display: flex;
                align-items: center;
            }
            
            .filter-checkbox {
                margin-right: 5px;
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
                        Available Accounts (15)
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
                    </div>
                </div>
                
                <div class="messaging-panel">
                    <div class="panel-header">
                        <div class="panel-title">Manual Message Sending</div>
                    </div>
                    
                    <div class="recipient-section">
                        <div class="section-title">Recipients (phone numbers)</div>
                        <textarea class="recipient-input" placeholder="Enter phone numbers, one per line or comma-separated">5555551234
5555552345
5555553456, 5555554567
5555555678</textarea>
                        <div class="recipient-hint">Enter one number per line or comma-separated. Format: 10 digits, with or without formatting.</div>
                    </div>
                    
                    <div class="message-section">
                        <div class="section-title">Message Content</div>
                        <textarea class="message-input" placeholder="Type your message here...">Hey there! Check out our latest promo at PB Betting. Reply STOP to opt out.</textarea>
                        
                        <div class="mms-section" style="margin-bottom: 10px; border-top: 1px solid #444; padding-top: 10px;">
                            <div class="section-title">MMS Attachments</div>
                            <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px;">
                                <div style="display: flex; flex-direction: column; align-items: center;">
                                    <div style="width: 80px; height: 80px; background: #333; border: 1px dashed #666; border-radius: 5px; display: flex; justify-content: center; align-items: center; cursor: pointer;">
                                        <span style="font-size: 24px; color: #666;">+</span>
                                    </div>
                                    <span style="font-size: 12px; color: #AAA; margin-top: 5px;">Add Image</span>
                                </div>
                                <div style="display: flex; flex-direction: column; align-items: center;">
                                    <div style="width: 80px; height: 80px; background: #333; border-radius: 5px; position: relative; overflow: hidden;">
                                        <div style="position: absolute; top: 0; right: 0; background: rgba(0,0,0,0.5); width: 20px; height: 20px; display: flex; justify-content: center; align-items: center; cursor: pointer;">
                                            <span style="color: #FFF; font-size: 14px;">×</span>
                                        </div>
                                        <div style="width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; color: #AAA; font-size: 10px; padding: 5px; text-align: center;">
                                            example.jpg
                                        </div>
                                    </div>
                                    <span style="font-size: 12px; color: #AAA; margin-top: 5px;">20 KB</span>
                                </div>
                            </div>
                            <div style="margin-top: 10px;">
                                <input type="file" id="mms-file" style="display: none;" multiple accept="image/*,video/*,.csv,.txt,.xlsx,.xls">
                                <button style="background-color: #444; color: white; border: none; padding: 6px 12px; cursor: pointer; border-radius: 3px; font-size: 12px;" onclick="document.getElementById('mms-file').click()">Upload Files</button>
                                <span style="font-size: 11px; color: #AAA; margin-left: 10px;">Supported: JPG, PNG, GIF, MP4, CSV, TXT, XLSX, XLS (max 5MB)</span>
                            </div>
                        </div>
                        
                        <div class="time-distribution" style="margin-bottom: 15px; border-top: 1px solid #444; padding-top: 15px;">
                            <div class="section-title">Time Distribution</div>
                            <div style="display: flex; margin-top: 10px; align-items: center; justify-content: space-between;">
                                <div style="flex: 1;">
                                    <div style="margin-bottom: 8px; display: flex; align-items: center;">
                                        <input type="radio" id="dist-none" name="distribution" checked style="margin-right: 8px;">
                                        <label for="dist-none" style="font-size: 13px; color: #CCC;">No Distribution (Send Immediately)</label>
                                    </div>
                                    <div style="margin-bottom: 8px; display: flex; align-items: center;">
                                        <input type="radio" id="dist-1h" name="distribution" style="margin-right: 8px;">
                                        <label for="dist-1h" style="font-size: 13px; color: #CCC;">1 Hour Distribution</label>
                                    </div>
                                    <div style="margin-bottom: 8px; display: flex; align-items: center;">
                                        <input type="radio" id="dist-2h" name="distribution" style="margin-right: 8px;">
                                        <label for="dist-2h" style="font-size: 13px; color: #CCC;">2 Hour Distribution</label>
                                    </div>
                                </div>
                                <div style="flex: 1;">
                                    <div style="margin-bottom: 8px; display: flex; align-items: center;">
                                        <input type="radio" id="dist-4h" name="distribution" style="margin-right: 8px;">
                                        <label for="dist-4h" style="font-size: 13px; color: #CCC;">4 Hour Distribution</label>
                                    </div>
                                    <div style="margin-bottom: 8px; display: flex; align-items: center;">
                                        <input type="radio" id="dist-12h" name="distribution" style="margin-right: 8px;">
                                        <label for="dist-12h" style="font-size: 13px; color: #CCC;">12 Hour Distribution</label>
                                    </div>
                                    <div style="margin-bottom: 8px; display: flex; align-items: center;">
                                        <input type="radio" id="dist-24h" name="distribution" style="margin-right: 8px;">
                                        <label for="dist-24h" style="font-size: 13px; color: #CCC;">24 Hour Distribution</label>
                                    </div>
                                </div>
                            </div>
                            <div style="margin-top: 5px; font-size: 11px; color: #AAA;">
                                Messages will be distributed evenly over the selected time period to avoid detection. The system will automatically vary timing between messages.
                            </div>
                        </div>
                        
                        <div class="send-options">
                            <div class="send-from">
                                <div class="send-label">Send from:</div>
                                <select class="send-select">
                                    <option>ghost_user_123 (954-555-1234)</option>
                                    <option>phantom_754 (754-555-2345)</option>
                                    <option>Random Account</option>
                                    <option>Distribute Among All</option>
                                </select>
                            </div>
                            
                            <div style="display: flex;">
                                <button id="start-button" class="send-button" style="background-color: #FF6600; margin-right: 10px; padding: 10px 20px; border: none; color: white; font-weight: bold; border-radius: 4px; cursor: pointer;">Start</button>
                                <button id="pause-button" style="background-color: #DDAA00; margin-right: 10px; padding: 10px 15px; border: none; color: white; font-weight: bold; border-radius: 4px; cursor: pointer; opacity: 0.5;" disabled>Pause</button>
                                <button id="stop-button" style="background-color: #DD3300; padding: 10px 15px; border: none; color: white; font-weight: bold; border-radius: 4px; cursor: pointer; opacity: 0.5;" disabled>Stop</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="stats-panel">
                    <div class="stats-header">Messaging Statistics</div>
                    
                    <div class="stat-group">
                        <div class="stat-title">Today's Activity</div>
                        <div class="stat-row">
                            <div class="stat-label">Messages Sent:</div>
                            <div class="stat-value">1,256</div>
                        </div>
                        <div class="stat-row">
                            <div class="stat-label">Delivery Rate:</div>
                            <div class="stat-value">98.5%</div>
                        </div>
                        <div class="stat-row">
                            <div class="stat-label">Response Rate:</div>
                            <div class="stat-value">12.3%</div>
                        </div>
                    </div>
                    
                    <div class="stat-group">
                        <div class="stat-title">Account Health</div>
                        <div class="stat-row">
                            <div class="stat-label">Active Accounts:</div>
                            <div class="stat-value">12/15</div>
                        </div>
                        <div class="stat-row">
                            <div class="stat-label">At Risk:</div>
                            <div class="stat-value">2</div>
                        </div>
                        <div class="stat-row">
                            <div class="stat-label">Blocked:</div>
                            <div class="stat-value">1</div>
                        </div>
                    </div>
                    
                    <div class="stat-group">
                        <div class="stat-title">Rate Limits</div>
                        <div class="stat-row">
                            <div class="stat-label">Daily Limit:</div>
                            <div class="stat-value">100K</div>
                        </div>
                        <div class="stat-row">
                            <div class="stat-label">Used Today:</div>
                            <div class="stat-value">1.3%</div>
                        </div>
                        <div class="stat-row">
                            <div class="stat-label">Per Account:</div>
                            <div class="stat-value">~105</div>
                        </div>
                    </div>
                    
                    <div class="account-filter">
                        <input type="checkbox" id="show-active" class="filter-checkbox" checked>
                        <label for="show-active">Show only active accounts</label>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Get distribution time
            function getSelectedDistribution() {
                const distributions = document.querySelectorAll('input[name="distribution"]');
                for (const dist of distributions) {
                    if (dist.checked) {
                        return dist.id;
                    }
                }
                return 'dist-none';
            }
            
            // Variables to track messaging job
            let messagingActive = false;
            let messagingPaused = false;
            let progressInterval = null;
            let progressCounter = 0;
            let totalMessages = 0;
            let sentMessages = 0;
            
            // Handle button states
            function updateButtonStates() {
                const startButton = document.getElementById('start-button');
                const pauseButton = document.getElementById('pause-button');
                const stopButton = document.getElementById('stop-button');
                
                if (messagingActive) {
                    startButton.disabled = true;
                    startButton.style.opacity = '0.5';
                    stopButton.disabled = false;
                    stopButton.style.opacity = '1';
                    
                    if (messagingPaused) {
                        pauseButton.innerHTML = 'Resume';
                        pauseButton.style.backgroundColor = '#55AA00';
                    } else {
                        pauseButton.innerHTML = 'Pause';
                        pauseButton.style.backgroundColor = '#DDAA00';
                    }
                    
                    pauseButton.disabled = false;
                    pauseButton.style.opacity = '1';
                } else {
                    startButton.disabled = false;
                    startButton.style.opacity = '1';
                    pauseButton.disabled = true;
                    pauseButton.style.opacity = '0.5';
                    stopButton.disabled = true;
                    stopButton.style.opacity = '0.5';
                    pauseButton.innerHTML = 'Pause';
                }
            }
            
            // Start messaging job
            document.getElementById('start-button').addEventListener('click', function() {
                const recipients = document.querySelector('.recipient-input').value;
                const message = document.querySelector('.message-input').value;
                const selectedAccount = document.querySelector('.send-select').value;
                const distribution = getSelectedDistribution();
                
                totalMessages = 0;
                recipients.split(/[\n,]/).forEach(function(recipient) {
                    if (recipient.trim().length > 0) {
                        totalMessages++;
                    }
                });
                
                if (totalMessages === 0) {
                    alert('Please enter at least one recipient phone number.');
                    return;
                }
                
                if (message.trim() === '') {
                    alert('Please enter a message to send.');
                    return;
                }
                
                // Get distribution time display
                let distDisplay = "immediately";
                let updateFrequency = 100; // milliseconds
                
                switch(distribution) {
                    case 'dist-1h': 
                        distDisplay = "over 1 hour"; 
                        updateFrequency = 1000; 
                        break;
                    case 'dist-2h': 
                        distDisplay = "over 2 hours"; 
                        updateFrequency = 2000; 
                        break;
                    case 'dist-4h': 
                        distDisplay = "over 4 hours"; 
                        updateFrequency = 3000; 
                        break;
                    case 'dist-12h': 
                        distDisplay = "over 12 hours"; 
                        updateFrequency = 5000; 
                        break;
                    case 'dist-24h': 
                        distDisplay = "over 24 hours"; 
                        updateFrequency = 8000; 
                        break;
                }
                
                messagingActive = true;
                messagingPaused = false;
                sentMessages = 0;
                updateButtonStates();
                
                // For the demo, we'll simulate sending with a progress counter
                progressInterval = setInterval(function() {
                    if (!messagingPaused && sentMessages < totalMessages) {
                        sentMessages++;
                        document.querySelector('.stat-value').innerText = sentMessages.toLocaleString();
                        document.querySelector('.stat-value:nth-child(2)').innerText = Math.round((sentMessages / totalMessages) * 100) + '%';
                        
                        // Update progress in stats
                        const usedPercentage = (sentMessages / 100000 * 100).toFixed(1);
                        document.querySelector('.stat-group:nth-child(3) .stat-row:nth-child(2) .stat-value').innerText = usedPercentage + '%';
                        
                        if (sentMessages >= totalMessages) {
                            clearInterval(progressInterval);
                            messagingActive = false;
                            updateButtonStates();
                            alert(`Completed sending ${totalMessages} messages!`);
                        }
                    }
                }, updateFrequency);
                
                alert(`Starting to send ${totalMessages} messages ${distDisplay} from account: ${selectedAccount}`);
            });
            
            // Pause messaging job
            document.getElementById('pause-button').addEventListener('click', function() {
                if (messagingActive) {
                    messagingPaused = !messagingPaused;
                    
                    if (messagingPaused) {
                        alert('Message sending paused. Click "Resume" to continue.');
                    } else {
                        alert('Message sending resumed.');
                    }
                    
                    updateButtonStates();
                }
            });
            
            // Stop messaging job
            document.getElementById('stop-button').addEventListener('click', function() {
                if (messagingActive) {
                    clearInterval(progressInterval);
                    messagingActive = false;
                    messagingPaused = false;
                    alert(`Messaging stopped. ${sentMessages} out of ${totalMessages} messages were sent.`);
                    updateButtonStates();
                }
            });
            
            document.querySelectorAll('.account-item').forEach(function(item) {
                item.addEventListener('click', function() {
                    document.querySelectorAll('.account-item').forEach(function(i) {
                        i.classList.remove('active');
                    });
                    item.classList.add('active');
                });
            });
        </script>
    </body>
    </html>
    ''', logo_exists=os.path.exists("static/progress_logo.png"))

if __name__ == '__main__':
    # Check if assets folder exists and create it if not
    os.makedirs('assets', exist_ok=True)
    
    # Copy logo and background from attached_assets if needed
    if os.path.exists("attached_assets/progress_logo.png") and not os.path.exists("assets/progress_logo.png"):
        import shutil
        shutil.copy("attached_assets/progress_logo.png", "assets/progress_logo.png")
        
    if os.path.exists("attached_assets/progress_background.jpg") and not os.path.exists("assets/progress_background.jpg"):
        import shutil
        shutil.copy("attached_assets/progress_background.jpg", "assets/progress_background.jpg")
    
    # Start the Flask development server
    app.run(host='0.0.0.0', port=5000, debug=True)