"""
COMPLETE ProgressGhostCreator app with ALL sections and CLICKABLE BUTTONS

This version includes ALL content from app_preview_fixed.py with proper clickable functionality
"""

import os
import shutil
from flask import Flask, render_template_string, send_from_directory, redirect, url_for

app = Flask(__name__)

# Ensure static folder exists
os.makedirs('static', exist_ok=True)

# Process assets
def process_assets():
    """Process and copy assets to static folder"""
    # Make sure static directory exists
    os.makedirs("static", exist_ok=True)
    
    # Look in multiple potential locations for the assets
    logo_locations = [
        "assets/progress_logo.png",
        "attached_assets/progress_logo.png",
        "progress_logo.png"
    ]
    
    background_locations = [
        "assets/progress_background.jpg",
        "attached_assets/progress_background.jpg",
        "progress_background.jpg"
    ]
    
    # Try to find and copy the logo
    for logo_path in logo_locations:
        if os.path.exists(logo_path):
            print(f"Found logo at {logo_path}")
            shutil.copy(logo_path, "static/progress_logo.png")
            break
    else:
        print("Warning: Could not find progress_logo.png")
    
    # Try to find and copy the background
    for bg_path in background_locations:
        if os.path.exists(bg_path):
            print(f"Found background at {bg_path}")
            shutil.copy(bg_path, "static/progress_background.jpg")
            break
    else:
        print("Warning: Could not find progress_background.jpg")

# Base HTML template with fixed navigation
BASE_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>ProgressGhostCreator - {{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #1E1E1E;
            color: #EEE;
        }
        
        .nav-bar {
            background-color: #252525;
            padding: 15px 20px;
            display: flex;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
        }
        
        .nav-logo {
            height: 30px;
            margin-right: 25px;
        }
        
        .nav-menu {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        
        .nav-link {
            color: #CCC;
            text-decoration: none;
            padding: 8px 15px;
            border-radius: 4px;
            font-size: 14px;
            white-space: nowrap;
        }
        
        .nav-link:hover {
            background-color: #333;
            color: #FFF;
        }
        
        .nav-link.active {
            background-color: #FF6600;
            color: white;
        }
        
        .content-wrapper {
            margin-top: 60px;
            min-height: calc(100vh - 60px);
            padding: 20px;
            background-image: url('/static/progress_background.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        
        .app-container {
            background-color: rgba(30, 30, 30, 0.9);
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            margin: 20px auto;
            max-width: 1200px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: calc(100vh - 100px);
        }
        
        .app-content {
            flex: 1;
            overflow: auto;
            padding: 20px;
        }
        
        /* Form elements */
        .form-panel {
            background-color: #252525;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .form-section {
            margin-bottom: 15px;
        }
        
        .form-label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #CCC;
        }
        
        .form-input {
            width: 100%;
            padding: 8px 10px;
            border-radius: 4px;
            border: 1px solid #444;
            background-color: #333;
            color: #EEE;
            font-size: 14px;
        }
        
        .form-select {
            width: 100%;
            padding: 8px 10px;
            border-radius: 4px;
            border: 1px solid #444;
            background-color: #333;
            color: #EEE;
            font-size: 14px;
            appearance: none;
        }
        
        .form-button {
            background-color: #FF6600;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            font-weight: bold;
            cursor: pointer;
            font-size: 14px;
        }
        
        .form-button:hover {
            background-color: #FF7722;
        }
        
        .secondary-button {
            background-color: #444;
        }
        
        .secondary-button:hover {
            background-color: #555;
        }
        
        .checkbox-group {
            margin-top: 10px;
        }
        
        .checkbox-label {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            color: #CCC;
        }
        
        .checkbox-input {
            margin-right: 8px;
        }
        
        /* Dashboard table */
        .dashboard-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        .dashboard-table th {
            text-align: left;
            padding: 12px 15px;
            background-color: #333;
            border-bottom: 1px solid #444;
            font-weight: bold;
            color: #EEE;
        }
        
        .dashboard-table td {
            padding: 10px 15px;
            border-bottom: 1px solid #444;
            color: #CCC;
        }
        
        .dashboard-table tr:hover td {
            background-color: #2A2A2A;
        }
        
        .status-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 30px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .status-active {
            background-color: #4CAF50;
            color: #FFF;
        }
        
        .status-warning {
            background-color: #FFC107;
            color: #333;
        }
        
        .status-danger {
            background-color: #F44336;
            color: #FFF;
        }
        
        .status-neutral {
            background-color: #9E9E9E;
            color: #FFF;
        }
        
        /* Progress bar */
        .progress-bar {
            height: 20px;
            background-color: #333;
            border-radius: 10px;
            margin-bottom: 10px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background-color: #FF6600;
            border-radius: 10px;
        }
        
        /* Tabs */
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

        /* Click Effect */
        button, .nav-link, .form-button, .tab {
            position: relative;
            overflow: hidden;
            transition: transform 0.1s;
        }
        
        button:active, .nav-link:active, .form-button:active, .tab:active {
            transform: scale(0.97);
        }
        
        /* Status messages */
        .status-message {
            position: fixed;
            top: 70px;
            right: 20px;
            padding: 12px 20px;
            background-color: rgba(40, 40, 40, 0.9);
            color: #FFF;
            border-radius: 5px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            transition: opacity 0.5s, transform 0.3s;
            transform: translateY(-10px);
            opacity: 0;
        }
        
        .status-message.success {
            background-color: rgba(40, 180, 40, 0.9);
        }
        
        .status-message.error {
            background-color: rgba(180, 40, 40, 0.9);
        }
        
        .status-message.show {
            transform: translateY(0);
            opacity: 1;
        }
    </style>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Make all buttons and links clickable with feedback
            document.querySelectorAll('button, .tab, .nav-link, .form-button').forEach(function(element) {
                element.addEventListener('click', function(e) {
                    // Only prevent default if not a proper link
                    if (element.classList.contains('nav-link') && element.getAttribute('href')) {
                        // This is a navigation link, let it work normally
                        return;
                    }
                    
                    e.preventDefault();
                    
                    // Show message
                    var text = this.textContent.trim();
                    showStatusMessage('Clicked: ' + text, 'success');
                });
            });
        });
        
        function showStatusMessage(message, type) {
            // Create message element
            var msgElement = document.createElement('div');
            msgElement.className = 'status-message ' + (type || '');
            msgElement.textContent = message;
            document.body.appendChild(msgElement);
            
            // Show message
            setTimeout(function() {
                msgElement.classList.add('show');
            }, 10);
            
            // Hide after 3 seconds
            setTimeout(function() {
                msgElement.classList.remove('show');
                setTimeout(function() {
                    document.body.removeChild(msgElement);
                }, 500);
            }, 3000);
        }
    </script>
</head>
<body>
    <!-- Fixed Navigation Bar -->
    <div class="nav-bar">
        <img src="/static/progress_logo.png" alt="PB BETTING Logo" class="nav-logo">
        <div class="nav-menu">
            <a href="/" class="nav-link {{ 'active' if active_page == '/' else '' }}">Home</a>
            <a href="/creator" class="nav-link {{ 'active' if active_page == '/creator' else '' }}">Creator</a>
            <a href="/dashboard" class="nav-link {{ 'active' if active_page == '/dashboard' else '' }}">Dashboard</a>
            <a href="/campaigns" class="nav-link {{ 'active' if active_page == '/campaigns' else '' }}">Campaigns</a>
            <a href="/manual-messaging" class="nav-link {{ 'active' if active_page == '/manual-messaging' else '' }}">Manual Messages</a>
            <a href="/message-templates" class="nav-link {{ 'active' if active_page == '/message-templates' else '' }}">Message Templates</a>
            <a href="/message-dashboard" class="nav-link {{ 'active' if active_page == '/message-dashboard' else '' }}">Message Monitor</a>
            <a href="/image-dashboard" class="nav-link {{ 'active' if active_page == '/image-dashboard' else '' }}">Image Manager</a>
            <a href="/account-health" class="nav-link {{ 'active' if active_page == '/account-health' else '' }}">Account Health</a>
            <a href="/voicemail-manager" class="nav-link {{ 'active' if active_page == '/voicemail-manager' else '' }}">Voicemail Manager</a>
            <a href="/campaign-schedule" class="nav-link {{ 'active' if active_page == '/campaign-schedule' else '' }}">Schedule</a>
        </div>
    </div>
    
    <!-- Page Content -->
    <div class="content-wrapper">
        {{ content|safe }}
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    """Display the mockup of the ProgressGhostCreator application"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Home",
        active_page="/",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%;">
                    <div style="max-width: 800px; text-align: center;">
                        <h1 style="font-size: 28px; margin-bottom: 20px; color: #FF6600;">ProgressGhostCreator</h1>
                        <p>The advanced TextNow account management and automation platform. Create, manage, and utilize ghost accounts with sophisticated distribution, voicemail setup, and messaging capabilities.</p>
                        
                        <div style="display: flex; justify-content: center; gap: 15px; margin: 30px 0;">
                            <a href="/creator" class="form-button">Create Accounts</a>
                            <a href="/dashboard" class="form-button">Manage Accounts</a>
                            <a href="/campaigns" class="form-button">Run Campaigns</a>
                        </div>
                        
                        <div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; margin-top: 30px;">
                            <div style="background-color: #252525; padding: 20px; border-radius: 6px; min-width: 160px; text-align: center;">
                                <div style="font-size: 24px; font-weight: bold; color: #FF6600;">10,563</div>
                                <div style="color: #AAA; margin-top: 5px;">Total Accounts</div>
                            </div>
                            <div style="background-color: #252525; padding: 20px; border-radius: 6px; min-width: 160px; text-align: center;">
                                <div style="font-size: 24px; font-weight: bold; color: #FF6600;">5,219</div>
                                <div style="color: #AAA; margin-top: 5px;">Active Accounts</div>
                            </div>
                            <div style="background-color: #252525; padding: 20px; border-radius: 6px; min-width: 160px; text-align: center;">
                                <div style="font-size: 24px; font-weight: bold; color: #FF6600;">892,145</div>
                                <div style="color: #AAA; margin-top: 5px;">Messages Sent</div>
                            </div>
                            <div style="background-color: #252525; padding: 20px; border-radius: 6px; min-width: 160px; text-align: center;">
                                <div style="font-size: 24px; font-weight: bold; color: #FF6600;">98.7%</div>
                                <div style="color: #AAA; margin-top: 5px;">Success Rate</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
    )

@app.route('/creator')
def creator_page():
    """The main account creator page with area code input and start button"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Account Creator",
        active_page="/creator",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; gap: 20px; height: 100%;">
                    <!-- Settings Panel -->
                    <div style="width: 280px; background-color: #252525; border-radius: 6px; padding: 20px;">
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 20px; color: #EEE;">
                            Creation Settings
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label class="form-label">Number of Accounts</label>
                            <input type="number" class="form-input" value="100" min="1" max="10000">
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label class="form-label">Device Mode</label>
                            <select class="form-select">
                                <option selected>Production (BLU G44)</option>
                                <option>Demo (No Device)</option>
                            </select>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label class="form-label">Area Codes</label>
                            <input type="text" class="form-input" value="954, 754, 305, 786, 561" placeholder="Enter area codes separated by commas">
                            <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                Enter area codes separated by commas
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label class="form-label">Voicemail Setup</label>
                            <select class="form-select">
                                <option selected>Auto-assign random voicemails</option>
                                <option>Use specific voicemail profile</option>
                                <option>No voicemail setup</option>
                            </select>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label class="form-label">Area Code Presets</label>
                            <div style="display: flex; gap: 5px; flex-wrap: wrap;">
                                <button class="form-button secondary-button">Florida</button>
                                <button class="form-button secondary-button">Georgia</button>
                                <button class="form-button secondary-button">New York</button>
                            </div>
                        </div>
                        
                        <button class="form-button" style="width: 100%; margin-top: 15px;">START CREATION</button>
                    </div>
                    
                    <!-- Main Content -->
                    <div style="flex: 1; display: flex; flex-direction: column;">
                        <!-- Progress Panel -->
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px; margin-bottom: 20px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                                <div style="font-size: 16px; font-weight: bold; color: #EEE;">Current Batch Progress</div>
                                <div>
                                    <button class="form-button secondary-button">Pause</button>
                                    <button class="form-button secondary-button">Cancel</button>
                                </div>
                            </div>
                            
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: 35%;"></div>
                            </div>
                            
                            <div style="display: flex; justify-content: space-between; color: #CCC; font-size: 14px;">
                                <div>Created: 35 / 100</div>
                                <div>Success Rate: 100%</div>
                                <div>Time Left: 32m 18s</div>
                            </div>
                        </div>
                        
                        <!-- Log Panel -->
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px; flex: 1;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                                <div style="font-size: 16px; font-weight: bold; color: #EEE;">Process Log</div>
                                <div>
                                    <button class="form-button secondary-button">Clear</button>
                                    <button class="form-button secondary-button">Export</button>
                                </div>
                            </div>
                            
                            <div style="background-color: #1A1A1A; border-radius: 4px; padding: 15px; height: 300px; overflow-y: auto; font-family: monospace; font-size: 13px;">
                                <div style="margin-bottom: 8px; color: #5F5;">
                                    <span style="color: #999;">[14:45:32]</span> Account created: Sarah Johnson (786-123-4567)
                                </div>
                                <div style="margin-bottom: 8px; color: #5F5;">
                                    <span style="color: #999;">[14:44:18]</span> Voicemail setup completed for: 786-123-4567
                                </div>
                                <div style="margin-bottom: 8px; color: #5F5;">
                                    <span style="color: #999;">[14:43:55]</span> Account verified: 786-123-4567
                                </div>
                                <div style="margin-bottom: 8px; color: #5F5;">
                                    <span style="color: #999;">[14:43:22]</span> Phone number assigned: 786-123-4567
                                </div>
                                <div style="margin-bottom: 8px; color: #5F5;">
                                    <span style="color: #999;">[14:42:45]</span> Registration form submitted: sarah.johnson91@example.com
                                </div>
                                <div style="margin-bottom: 8px; color: #5F5;">
                                    <span style="color: #999;">[14:42:10]</span> Generating account details: sarah.johnson91@example.com
                                </div>
                                <div style="margin-bottom: 8px; color: #5F5;">
                                    <span style="color: #999;">[14:42:00]</span> Device connected: BLU G44
                                </div>
                                <div style="margin-bottom: 8px; color: #5F5;">
                                    <span style="color: #999;">[14:41:45]</span> Starting account creation process
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
    )

@app.route('/dashboard')
def dashboard_page():
    """The account management dashboard page"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Account Dashboard",
        active_page="/dashboard",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <div style="font-size: 20px; font-weight: bold; color: #EEE;">Account Dashboard</div>
                    <div>
                        <button class="form-button secondary-button">Export CSV</button>
                        <button class="form-button">Add Account</button>
                    </div>
                </div>
                
                <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                    <div style="flex: 1;">
                        <input type="text" class="form-input" placeholder="Search accounts...">
                    </div>
                    <div>
                        <button class="form-button secondary-button">Filter</button>
                        <button class="form-button secondary-button">Refresh</button>
                    </div>
                </div>
                
                <div style="background-color: #252525; border-radius: 6px; overflow: hidden;">
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th>Phone Number</th>
                                <th>Name</th>
                                <th>Area Code</th>
                                <th>Status</th>
                                <th>Last Used</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>(954) 123-4567</td>
                                <td>John Smith</td>
                                <td>954</td>
                                <td><span class="status-badge status-active">Active</span></td>
                                <td>Today, 2:30 PM</td>
                                <td>
                                    <button class="form-button secondary-button">Edit</button>
                                    <button class="form-button secondary-button">Login</button>
                                </td>
                            </tr>
                            <tr>
                                <td>(786) 987-6543</td>
                                <td>Jane Doe</td>
                                <td>786</td>
                                <td><span class="status-badge status-active">Active</span></td>
                                <td>Today, 1:15 PM</td>
                                <td>
                                    <button class="form-button secondary-button">Edit</button>
                                    <button class="form-button secondary-button">Login</button>
                                </td>
                            </tr>
                            <tr>
                                <td>(305) 456-7890</td>
                                <td>Robert Johnson</td>
                                <td>305</td>
                                <td><span class="status-badge status-warning">Warning</span></td>
                                <td>Yesterday, 5:45 PM</td>
                                <td>
                                    <button class="form-button secondary-button">Edit</button>
                                    <button class="form-button secondary-button">Login</button>
                                </td>
                            </tr>
                            <tr>
                                <td>(754) 321-0987</td>
                                <td>Sarah Williams</td>
                                <td>754</td>
                                <td><span class="status-badge status-danger">Flagged</span></td>
                                <td>3 days ago</td>
                                <td>
                                    <button class="form-button secondary-button">Edit</button>
                                    <button class="form-button secondary-button">Replace</button>
                                </td>
                            </tr>
                            <tr>
                                <td>(561) 555-1212</td>
                                <td>Michael Brown</td>
                                <td>561</td>
                                <td><span class="status-badge status-active">Active</span></td>
                                <td>Today, 10:20 AM</td>
                                <td>
                                    <button class="form-button secondary-button">Edit</button>
                                    <button class="form-button secondary-button">Login</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div style="display: flex; justify-content: space-between; margin-top: 15px; color: #AAA; font-size: 14px;">
                    <div>Showing 5 of 10,563 accounts</div>
                    <div>
                        <button class="form-button secondary-button">Previous</button>
                        <button class="form-button secondary-button">Next</button>
                    </div>
                </div>
            </div>
        </div>
        '''
    )

@app.route('/campaigns')
def campaigns_page():
    """The campaigns management page"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Campaign Manager",
        active_page="/campaigns",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; gap: 20px; height: 100%;">
                    <!-- Campaign Creation Panel -->
                    <div style="width: 300px;">
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px;">
                            <div style="font-size: 16px; font-weight: bold; margin-bottom: 20px; color: #EEE;">
                                Create Campaign
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Campaign Name</label>
                                <input type="text" class="form-input" placeholder="Enter campaign name">
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Message Template</label>
                                <select class="form-select">
                                    <option selected>Spring Promotion</option>
                                    <option>Welcome Message</option>
                                    <option>Sports Event</option>
                                </select>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Target Numbers</label>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <button class="form-button secondary-button" style="flex: 1;">Upload CSV</button>
                                    <span style="color: #CCC; font-size: 12px;">0 numbers</span>
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Schedule</label>
                                <select class="form-select">
                                    <option selected>Start Immediately</option>
                                    <option>Schedule Time</option>
                                </select>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Active Hours</label>
                                <div style="display: flex; gap: 10px; align-items: center;">
                                    <input type="text" class="form-input" value="8" style="width: 60px;">
                                    <span style="color: #CCC;">to</span>
                                    <input type="text" class="form-input" value="20" style="width: 60px;">
                                </div>
                                <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                    8:00 AM to 8:00 PM
                                </div>
                            </div>
                            
                            <button class="form-button" style="width: 100%; margin-top: 15px;">START CAMPAIGN</button>
                        </div>
                    </div>
                    
                    <!-- Campaign List Panel -->
                    <div style="flex: 1;">
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px;">
                            <div style="font-size: 16px; font-weight: bold; margin-bottom: 20px; color: #EEE;">
                                Active Campaigns
                            </div>
                            
                            <div style="background-color: #333; padding: 15px; border-radius: 4px; margin-bottom: 15px; border-left: 3px solid #FF6600;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                    <div style="font-weight: bold; color: #EEE;">Spring Promotion</div>
                                    <div>
                                        <span class="status-badge status-active">Active</span>
                                    </div>
                                </div>
                                <div style="color: #CCC; margin-bottom: 10px; font-size: 14px;">
                                    10,000 targets • 35% complete • Started: Today, 1:30 PM • 8am-8pm
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: 35%;"></div>
                                </div>
                                <div style="display: flex; gap: 10px; margin-top: 15px;">
                                    <button class="form-button secondary-button">Pause</button>
                                    <button class="form-button secondary-button">View Details</button>
                                </div>
                            </div>
                            
                            <div style="background-color: #2A2A2A; padding: 15px; border-radius: 4px; margin-bottom: 15px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                    <div style="font-weight: bold; color: #EEE;">Weekend Special</div>
                                    <div>
                                        <span class="status-badge status-warning">Paused</span>
                                    </div>
                                </div>
                                <div style="color: #CCC; margin-bottom: 10px; font-size: 14px;">
                                    5,000 targets • 42% complete • Started: Yesterday • 9am-9pm
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: 42%;"></div>
                                </div>
                                <div style="display: flex; gap: 10px; margin-top: 15px;">
                                    <button class="form-button secondary-button">Resume</button>
                                    <button class="form-button secondary-button">View Details</button>
                                </div>
                            </div>
                            
                            <div style="font-size: 16px; font-weight: bold; margin: 25px 0 15px; color: #EEE; border-top: 1px solid #444; padding-top: 15px;">
                                Completed Campaigns
                            </div>
                            
                            <div style="background-color: #2A2A2A; padding: 15px; border-radius: 4px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                    <div style="font-weight: bold; color: #EEE;">March Madness</div>
                                    <div>
                                        <span class="status-badge status-neutral">Completed</span>
                                    </div>
                                </div>
                                <div style="color: #CCC; margin-bottom: 10px; font-size: 14px;">
                                    8,750 targets • 100% complete • Completed: April 5
                                </div>
                                <div style="display: flex; gap: 10px; margin-top: 10px;">
                                    <button class="form-button secondary-button">View Report</button>
                                    <button class="form-button secondary-button">Clone</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
    )

@app.route('/message-templates')
def message_templates_page():
    """The message templates creation and management page"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Message Templates",
        active_page="/message-templates",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; gap: 20px; height: 100%;">
                    <!-- Template List Panel -->
                    <div style="width: 250px;">
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px; height: 100%;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                <div style="font-size: 16px; font-weight: bold; color: #EEE;">Saved Templates</div>
                                <button class="form-button">New</button>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <input type="text" class="form-input" placeholder="Search templates...">
                            </div>
                            
                            <div style="background-color: #333; padding: 10px; border-radius: 4px; margin-top: 15px; cursor: pointer; border-left: 3px solid #FF6600;">
                                <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Spring Promotion</div>
                                <div style="font-size: 12px; color: #CCC;">Last edited: 2 days ago</div>
                            </div>
                            
                            <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-top: 10px; cursor: pointer;">
                                <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Welcome Message</div>
                                <div style="font-size: 12px; color: #CCC;">Last edited: 1 week ago</div>
                            </div>
                            
                            <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-top: 10px; cursor: pointer;">
                                <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Sports Event</div>
                                <div style="font-size: 12px; color: #CCC;">Last edited: 2 weeks ago</div>
                            </div>
                            
                            <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-top: 10px; cursor: pointer;">
                                <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Customer Follow-up</div>
                                <div style="font-size: 12px; color: #CCC;">Last edited: 3 weeks ago</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Template Editor Panel -->
                    <div style="flex: 1;">
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px; height: 100%;">
                            <div style="margin-bottom: 15px;">
                                <input type="text" class="form-input" value="Spring Promotion" placeholder="Template name">
                            </div>
                            
                            <div style="margin-bottom: 20px;">
                                <label class="form-label">Message Text</label>
                                <textarea class="form-input" style="height: 150px; resize: vertical;">Hey {{first_name}}, check out our latest sports odds for the upcoming games! Visit ProgressBets.com for exclusive offers and the best lines on {{event_name}}. Reply STOP to opt out.</textarea>
                            </div>
                            
                            <div style="margin-bottom: 20px;">
                                <label class="form-label">Variables</label>
                                <div style="font-size: 12px; color: #AAA; margin-bottom: 10px;">Click to add a variable to your message</div>
                                <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                                    <button class="form-button secondary-button">{{first_name}}</button>
                                    <button class="form-button secondary-button">{{last_name}}</button>
                                    <button class="form-button secondary-button">{{event_name}}</button>
                                    <button class="form-button secondary-button">{{city}}</button>
                                    <button class="form-button secondary-button">{{team}}</button>
                                    <button class="form-button secondary-button">{{odds}}</button>
                                    <button class="form-button secondary-button">{{date}}</button>
                                    <button class="form-button secondary-button">+ Add Custom</button>
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 20px;">
                                <label class="form-label">Image (Optional)</label>
                                <div style="display: flex; gap: 15px; align-items: center;">
                                    <div style="width: 100px; height: 100px; background-color: #333; border-radius: 4px; display: flex; justify-content: center; align-items: center; color: #777;">No Image</div>
                                    <div style="flex: 1;">
                                        <button class="form-button secondary-button" style="width: 100%; margin-bottom: 10px;">Upload Image</button>
                                        <button class="form-button secondary-button" style="width: 100%;">Select from Library</button>
                                    </div>
                                </div>
                            </div>
                            
                            <div style="display: flex; gap: 10px; justify-content: space-between; margin-top: 20px;">
                                <div>
                                    <button class="form-button secondary-button">Test Message</button>
                                    <button class="form-button secondary-button">Preview</button>
                                </div>
                                <div>
                                    <button class="form-button secondary-button">Delete</button>
                                    <button class="form-button">Save Template</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
    )

@app.route('/manual-messaging')
def manual_messaging_page():
    """The manual messaging page where you can send messages from a list of numbers"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Manual Messaging",
        active_page="/manual-messaging",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; gap: 20px; height: 100%;">
                    <!-- Sender Panel -->
                    <div style="width: 300px;">
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px;">
                            <div style="font-size: 16px; font-weight: bold; margin-bottom: 20px; color: #EEE;">
                                Sender Account
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Select Account</label>
                                <select class="form-select">
                                    <option>(954) 123-4567 - John Smith</option>
                                    <option>(786) 987-6543 - Jane Doe</option>
                                    <option>(305) 456-7890 - Robert Johnson</option>
                                    <option>(754) 321-0987 - Sarah Williams</option>
                                </select>
                            </div>
                            
                            <div style="margin-bottom: 20px;">
                                <label class="form-label">Account Status</label>
                                <div style="background-color: #333; border-radius: 4px; padding: 10px;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                        <div style="color: #CCC;">Status:</div>
                                        <div style="color: #4CAF50;">Active</div>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                        <div style="color: #CCC;">Health Score:</div>
                                        <div style="color: #4CAF50;">95/100</div>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                        <div style="color: #CCC;">Last Used:</div>
                                        <div style="color: #CCC;">Today, 2:30 PM</div>
                                    </div>
                                    <div style="display: flex; justify-content: space-between;">
                                        <div style="color: #CCC;">Messages Today:</div>
                                        <div style="color: #CCC;">42/100</div>
                                    </div>
                                </div>
                            </div>
                            
                            <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE; border-top: 1px solid #444; padding-top: 15px;">
                                Recipient
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Phone Number</label>
                                <input type="text" class="form-input" placeholder="Enter phone number">
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Name (Optional)</label>
                                <input type="text" class="form-input" placeholder="Enter recipient name">
                            </div>
                        </div>
                    </div>
                    
                    <!-- Message Panel -->
                    <div style="flex: 1;">
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px; height: 100%;">
                            <div style="font-size: 16px; font-weight: bold; margin-bottom: 20px; color: #EEE;">
                                Message
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Template (Optional)</label>
                                <select class="form-select">
                                    <option value="">-- Select Template --</option>
                                    <option>Spring Promotion</option>
                                    <option>Welcome Message</option>
                                    <option>Sports Event</option>
                                </select>
                            </div>
                            
                            <div style="margin-bottom: 20px;">
                                <label class="form-label">Message Text</label>
                                <textarea class="form-input" style="height: 200px; resize: vertical;" placeholder="Type your message here..."></textarea>
                            </div>
                            
                            <div style="margin-bottom: 20px;">
                                <label class="form-label">Image (Optional)</label>
                                <div style="display: flex; gap: 10px;">
                                    <button class="form-button secondary-button" style="flex: 1;">Upload Image</button>
                                    <button class="form-button secondary-button" style="flex: 1;">Select from Library</button>
                                </div>
                            </div>
                            
                            <div style="display: flex; justify-content: space-between; margin-top: 20px;">
                                <button class="form-button secondary-button">Save as Draft</button>
                                <button class="form-button">Send Message</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
    )

@app.route('/message-dashboard')
def message_dashboard_route():
    """The message monitoring dashboard interface"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Message Monitor",
        active_page="/message-dashboard",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <div style="font-size: 20px; font-weight: bold; color: #EEE;">Message Monitor</div>
                    <div>
                        <button class="form-button secondary-button">Export Data</button>
                        <button class="form-button">Refresh</button>
                    </div>
                </div>
                
                <div style="display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 200px; background-color: #252525; border-radius: 6px; padding: 15px; text-align: center;">
                        <div style="color: #AAA; margin-bottom: 5px; font-size: 14px;">Total Messages</div>
                        <div style="font-size: 24px; font-weight: bold; color: #FF6600;">892,145</div>
                    </div>
                    <div style="flex: 1; min-width: 200px; background-color: #252525; border-radius: 6px; padding: 15px; text-align: center;">
                        <div style="color: #AAA; margin-bottom: 5px; font-size: 14px;">Sent Today</div>
                        <div style="font-size: 24px; font-weight: bold; color: #FF6600;">3,427</div>
                    </div>
                    <div style="flex: 1; min-width: 200px; background-color: #252525; border-radius: 6px; padding: 15px; text-align: center;">
                        <div style="color: #AAA; margin-bottom: 5px; font-size: 14px;">Delivery Rate</div>
                        <div style="font-size: 24px; font-weight: bold; color: #FF6600;">98.7%</div>
                    </div>
                    <div style="flex: 1; min-width: 200px; background-color: #252525; border-radius: 6px; padding: 15px; text-align: center;">
                        <div style="color: #AAA; margin-bottom: 5px; font-size: 14px;">Response Rate</div>
                        <div style="font-size: 24px; font-weight: bold; color: #FF6600;">7.2%</div>
                    </div>
                </div>
                
                <div style="background-color: #252525; border-radius: 6px; overflow: hidden;">
                    <div style="padding: 15px; display: flex; gap: 15px; border-bottom: 1px solid #333;">
                        <div style="flex: 1;">
                            <input type="text" class="form-input" placeholder="Search messages...">
                        </div>
                        <div>
                            <select class="form-select" style="width: 150px;">
                                <option>All Messages</option>
                                <option>Delivered</option>
                                <option>Failed</option>
                                <option>With Responses</option>
                            </select>
                        </div>
                        <div>
                            <button class="form-button secondary-button">Filter</button>
                        </div>
                    </div>
                    
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th>Date/Time</th>
                                <th>From</th>
                                <th>To</th>
                                <th>Message</th>
                                <th>Status</th>
                                <th>Campaign</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>2:45 PM</td>
                                <td>(954) 123-4567</td>
                                <td>(305) 555-7890</td>
                                <td>Hey Mark, check out our latest sports odds...</td>
                                <td><span class="status-badge status-active">Delivered</span></td>
                                <td>Spring Promotion</td>
                                <td>
                                    <button class="form-button secondary-button">View</button>
                                </td>
                            </tr>
                            <tr>
                                <td>2:42 PM</td>
                                <td>(786) 987-6543</td>
                                <td>(561) 123-4567</td>
                                <td>Hey John, check out our latest sports odds...</td>
                                <td><span class="status-badge status-active">Delivered</span></td>
                                <td>Spring Promotion</td>
                                <td>
                                    <button class="form-button secondary-button">View</button>
                                </td>
                            </tr>
                            <tr>
                                <td>2:38 PM</td>
                                <td>(305) 456-7890</td>
                                <td>(754) 987-6543</td>
                                <td>Hey Sarah, check out our latest sports odds...</td>
                                <td><span class="status-badge status-danger">Failed</span></td>
                                <td>Spring Promotion</td>
                                <td>
                                    <button class="form-button secondary-button">View</button>
                                </td>
                            </tr>
                            <tr>
                                <td>2:32 PM</td>
                                <td>(754) 321-0987</td>
                                <td>(305) 111-2222</td>
                                <td>Hey Robert, check out our latest sports odds...</td>
                                <td><span class="status-badge status-active">Delivered</span></td>
                                <td>Spring Promotion</td>
                                <td>
                                    <button class="form-button secondary-button">View</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <div style="padding: 15px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #333;">
                        <div style="color: #AAA; font-size: 14px;">Showing 4 of 3,427 messages</div>
                        <div>
                            <button class="form-button secondary-button">Previous</button>
                            <button class="form-button secondary-button">Next</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
    )

@app.route('/image-dashboard')
def image_dashboard_route():
    """The image management dashboard interface"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Image Manager",
        active_page="/image-dashboard",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <div style="font-size: 20px; font-weight: bold; color: #EEE;">Image Manager</div>
                    <div>
                        <button class="form-button secondary-button">Import Images</button>
                        <button class="form-button">Upload New</button>
                    </div>
                </div>
                
                <div style="display: flex; gap: 20px; height: calc(100% - 60px);">
                    <!-- Image Categories Panel -->
                    <div style="width: 250px;">
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px; height: 100%;">
                            <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE;">
                                Categories
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <input type="text" class="form-input" placeholder="Search images...">
                            </div>
                            
                            <div style="margin-top: 20px;">
                                <div style="background-color: #333; padding: 10px; border-radius: 4px; margin-bottom: 8px; cursor: pointer; border-left: 3px solid #FF6600;">
                                    <div style="font-weight: bold; color: #EEE;">All Images</div>
                                    <div style="font-size: 12px; color: #CCC;">120 images</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-bottom: 8px; cursor: pointer;">
                                    <div style="font-weight: bold; color: #EEE;">Sports</div>
                                    <div style="font-size: 12px; color: #CCC;">45 images</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-bottom: 8px; cursor: pointer;">
                                    <div style="font-weight: bold; color: #EEE;">Promotions</div>
                                    <div style="font-size: 12px; color: #CCC;">32 images</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-bottom: 8px; cursor: pointer;">
                                    <div style="font-weight: bold; color: #EEE;">Profile Pictures</div>
                                    <div style="font-size: 12px; color: #CCC;">28 images</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-bottom: 8px; cursor: pointer;">
                                    <div style="font-weight: bold; color: #EEE;">Uncategorized</div>
                                    <div style="font-size: 12px; color: #CCC;">15 images</div>
                                </div>
                                
                                <button class="form-button secondary-button" style="width: 100%; margin-top: 15px;">Add Category</button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Image Gallery Panel -->
                    <div style="flex: 1;">
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px; height: 100%;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                                <div style="font-size: 16px; font-weight: bold; color: #EEE;">All Images (120)</div>
                                <div>
                                    <select class="form-select" style="width: 150px;">
                                        <option>Recent First</option>
                                        <option>Oldest First</option>
                                        <option>Most Used</option>
                                        <option>Least Used</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 15px; overflow-y: auto; height: calc(100% - 50px);">
                                <div style="background-color: #333; border-radius: 6px; overflow: hidden; cursor: pointer;">
                                    <div style="height: 120px; background-color: #444; display: flex; justify-content: center; align-items: center; color: #777;">Image 1</div>
                                    <div style="padding: 10px;">
                                        <div style="font-size: 14px; color: #EEE; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">sports_promo_1.jpg</div>
                                        <div style="font-size: 12px; color: #AAA;">Used: 24 times</div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 6px; overflow: hidden; cursor: pointer;">
                                    <div style="height: 120px; background-color: #444; display: flex; justify-content: center; align-items: center; color: #777;">Image 2</div>
                                    <div style="padding: 10px;">
                                        <div style="font-size: 14px; color: #EEE; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">basketball_odds.jpg</div>
                                        <div style="font-size: 12px; color: #AAA;">Used: 18 times</div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 6px; overflow: hidden; cursor: pointer;">
                                    <div style="height: 120px; background-color: #444; display: flex; justify-content: center; align-items: center; color: #777;">Image 3</div>
                                    <div style="padding: 10px;">
                                        <div style="font-size: 14px; color: #EEE; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">football_special.jpg</div>
                                        <div style="font-size: 12px; color: #AAA;">Used: 12 times</div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 6px; overflow: hidden; cursor: pointer;">
                                    <div style="height: 120px; background-color: #444; display: flex; justify-content: center; align-items: center; color: #777;">Image 4</div>
                                    <div style="padding: 10px;">
                                        <div style="font-size: 14px; color: #EEE; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">welcome_bonus.jpg</div>
                                        <div style="font-size: 12px; color: #AAA;">Used: 31 times</div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 6px; overflow: hidden; cursor: pointer;">
                                    <div style="height: 120px; background-color: #444; display: flex; justify-content: center; align-items: center; color: #777;">Image 5</div>
                                    <div style="padding: 10px;">
                                        <div style="font-size: 14px; color: #EEE; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">profile_pic_1.jpg</div>
                                        <div style="font-size: 12px; color: #AAA;">Used: 8 times</div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 6px; overflow: hidden; cursor: pointer;">
                                    <div style="height: 120px; background-color: #444; display: flex; justify-content: center; align-items: center; color: #777;">Image 6</div>
                                    <div style="padding: 10px;">
                                        <div style="font-size: 14px; color: #EEE; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">baseball_odds.jpg</div>
                                        <div style="font-size: 12px; color: #AAA;">Used: 15 times</div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 6px; overflow: hidden; cursor: pointer;">
                                    <div style="height: 120px; background-color: #444; display: flex; justify-content: center; align-items: center; color: #777;">Image 7</div>
                                    <div style="padding: 10px;">
                                        <div style="font-size: 14px; color: #EEE; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">profile_pic_2.jpg</div>
                                        <div style="font-size: 12px; color: #AAA;">Used: 7 times</div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 6px; overflow: hidden; cursor: pointer;">
                                    <div style="height: 120px; background-color: #444; display: flex; justify-content: center; align-items: center; color: #777;">Image 8</div>
                                    <div style="padding: 10px;">
                                        <div style="font-size: 14px; color: #EEE; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">hockey_promo.jpg</div>
                                        <div style="font-size: 12px; color: #AAA;">Used: 9 times</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
    )

@app.route('/account-health')
def account_health_route():
    """The account health monitoring dashboard interface"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Account Health",
        active_page="/account-health",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <div style="font-size: 20px; font-weight: bold; color: #EEE;">Account Health Monitor</div>
                    <div>
                        <button class="form-button secondary-button">Run Health Check</button>
                        <button class="form-button">Refresh</button>
                    </div>
                </div>
                
                <div style="display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 200px; background-color: #252525; border-radius: 6px; padding: 15px; text-align: center;">
                        <div style="color: #AAA; margin-bottom: 5px; font-size: 14px;">Total Accounts</div>
                        <div style="font-size: 24px; font-weight: bold; color: #FF6600;">10,563</div>
                    </div>
                    <div style="flex: 1; min-width: 200px; background-color: #252525; border-radius: 6px; padding: 15px; text-align: center;">
                        <div style="color: #AAA; margin-bottom: 5px; font-size: 14px;">Healthy Accounts</div>
                        <div style="font-size: 24px; font-weight: bold; color: #4CAF50;">10,104</div>
                        <div style="font-size: 12px; color: #AAA;">95.7%</div>
                    </div>
                    <div style="flex: 1; min-width: 200px; background-color: #252525; border-radius: 6px; padding: 15px; text-align: center;">
                        <div style="color: #AAA; margin-bottom: 5px; font-size: 14px;">Flagged Accounts</div>
                        <div style="font-size: 24px; font-weight: bold; color: #FFC107;">356</div>
                        <div style="font-size: 12px; color: #AAA;">3.4%</div>
                    </div>
                    <div style="flex: 1; min-width: 200px; background-color: #252525; border-radius: 6px; padding: 15px; text-align: center;">
                        <div style="color: #AAA; margin-bottom: 5px; font-size: 14px;">Blocked Accounts</div>
                        <div style="font-size: 24px; font-weight: bold; color: #F44336;">103</div>
                        <div style="font-size: 12px; color: #AAA;">0.9%</div>
                    </div>
                </div>
                
                <div style="background-color: #252525; border-radius: 6px; overflow: hidden;">
                    <div style="padding: 15px 20px; border-bottom: 1px solid #333;">
                        <div style="font-size: 16px; font-weight: bold; color: #EEE;">Account Health Issues</div>
                    </div>
                    
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th>Phone Number</th>
                                <th>Account Name</th>
                                <th>Status</th>
                                <th>Health Score</th>
                                <th>Issue</th>
                                <th>Last Check</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>(754) 321-0987</td>
                                <td>Sarah Williams</td>
                                <td><span class="status-badge status-danger">Blocked</span></td>
                                <td>25/100</td>
                                <td>Account login failed: Invalid credentials</td>
                                <td>Today, 1:30 PM</td>
                                <td>
                                    <button class="form-button secondary-button">Replace</button>
                                </td>
                            </tr>
                            <tr>
                                <td>(305) 456-7890</td>
                                <td>Robert Johnson</td>
                                <td><span class="status-badge status-warning">Flagged</span></td>
                                <td>65/100</td>
                                <td>High message failure rate (12%)</td>
                                <td>Today, 12:45 PM</td>
                                <td>
                                    <button class="form-button secondary-button">Health Check</button>
                                </td>
                            </tr>
                            <tr>
                                <td>(786) 555-1234</td>
                                <td>Michael Brown</td>
                                <td><span class="status-badge status-warning">Flagged</span></td>
                                <td>72/100</td>
                                <td>CAPTCHA detected during login</td>
                                <td>Today, 11:20 AM</td>
                                <td>
                                    <button class="form-button secondary-button">Health Check</button>
                                </td>
                            </tr>
                            <tr>
                                <td>(954) 789-0123</td>
                                <td>Jennifer Davis</td>
                                <td><span class="status-badge status-danger">Blocked</span></td>
                                <td>15/100</td>
                                <td>Account suspended by platform</td>
                                <td>Yesterday, 5:15 PM</td>
                                <td>
                                    <button class="form-button secondary-button">Replace</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <div style="padding: 15px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #333;">
                        <div style="color: #AAA; font-size: 14px;">Showing 4 of 459 flagged/blocked accounts</div>
                        <div>
                            <button class="form-button secondary-button">Previous</button>
                            <button class="form-button secondary-button">Next</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
    )

@app.route('/voicemail-manager')
def voicemail_manager_route():
    """The voicemail management interface"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Voicemail Manager",
        active_page="/voicemail-manager",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; gap: 20px; height: 100%;">
                    <!-- Voicemail Library Panel -->
                    <div style="width: 280px;">
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px; height: 100%;">
                            <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE; border-bottom: 1px solid #444; padding-bottom: 10px;">
                                Voicemail Library
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <button class="form-button" style="width: 100%; margin-bottom: 10px; position: relative; overflow: hidden;">
                                    Import Voicemails (Bulk)
                                    <input type="file" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;" multiple accept=".mp3,.wav">
                                </button>
                                <button class="form-button secondary-button" style="width: 100%;">Record New</button>
                            </div>
                            
                            <div style="margin-bottom: 15px; padding: 10px; background-color: #333; border-radius: 4px;">
                                <div style="font-weight: bold; color: #EEE; margin-bottom: 8px;">Batch Assignment</div>
                                <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #2A2A2A; color: #EEE; font-size: 14px; margin-bottom: 10px;">
                                    <option selected>Change All Account Voicemails</option>
                                    <option>Assign to Selected Accounts</option>
                                    <option>Randomly Rotate Across Accounts</option>
                                    <option>Reset to Default Voicemails</option>
                                </select>
                                <button class="form-button" style="width: 100%;">START</button>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <input type="text" class="form-input" placeholder="Search voicemails..." style="margin-bottom: 10px;">
                                
                                <select class="form-select">
                                    <option>All Voicemails</option>
                                    <option selected>Male Voice</option>
                                    <option>Female Voice</option>
                                    <option>Custom Recordings</option>
                                    <option>Generated</option>
                                </select>
                            </div>
                            
                            <div style="margin-top: 20px; height: calc(100% - 350px); overflow-y: auto;">
                                <div style="font-size: 14px; color: #CCC; margin-bottom: 10px;">42 voicemails found</div>
                                
                                <div style="background-color: #333; padding: 10px; border-radius: 4px; margin-bottom: 10px; cursor: pointer; border-left: 3px solid #FF6600;">
                                    <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Male_Greeting_1.mp3</div>
                                    <div style="font-size: 12px; color: #CCC; margin-bottom: 5px;">Duration: 12s • Used: 37 times</div>
                                    <div style="display: flex; gap: 5px;">
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px;">▶ Play</button>
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px;">Assign</button>
                                    </div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-bottom: 10px; cursor: pointer;">
                                    <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Male_Greeting_2.mp3</div>
                                    <div style="font-size: 12px; color: #CCC; margin-bottom: 5px;">Duration: 10s • Used: 24 times</div>
                                    <div style="display: flex; gap: 5px;">
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px;">▶ Play</button>
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px;">Assign</button>
                                    </div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-bottom: 10px; cursor: pointer;">
                                    <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Male_Business_1.mp3</div>
                                    <div style="font-size: 12px; color: #CCC; margin-bottom: 5px;">Duration: 15s • Used: 18 times</div>
                                    <div style="display: flex; gap: 5px;">
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px;">▶ Play</button>
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px;">Assign</button>
                                    </div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-bottom: 10px; cursor: pointer;">
                                    <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Male_Casual_1.mp3</div>
                                    <div style="font-size: 12px; color: #CCC; margin-bottom: 5px;">Duration: 8s • Used: 15 times</div>
                                    <div style="display: flex; gap: 5px;">
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px;">▶ Play</button>
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px;">Assign</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Voicemail Management Panel -->
                    <div style="flex: 1;">
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px; height: 100%;">
                            <div style="font-size: 16px; font-weight: bold; margin-bottom: 20px; color: #EEE;">
                                Voicemail Assignment
                            </div>
                            
                            <div class="tabs">
                                <div class="tab active">Current Assignments</div>
                                <div class="tab">Voice Generator</div>
                                <div class="tab">Auto-Assignment Rules</div>
                            </div>
                            
                            <div style="padding: 20px; background-color: #2A2A2A; border-radius: 0 0 6px 6px;">
                                <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                                    <div style="flex: 1;">
                                        <input type="text" class="form-input" placeholder="Search accounts...">
                                    </div>
                                    <div>
                                        <select class="form-select" style="width: 150px;">
                                            <option>All Accounts</option>
                                            <option>With Voicemail</option>
                                            <option>Without Voicemail</option>
                                        </select>
                                    </div>
                                    <div>
                                        <button class="form-button secondary-button">Filter</button>
                                    </div>
                                </div>
                                
                                <table class="dashboard-table">
                                    <thead>
                                        <tr>
                                            <th style="width: 30px;"><input type="checkbox" style="margin: 0;"></th>
                                            <th>Phone Number</th>
                                            <th>Account Name</th>
                                            <th>Current Voicemail</th>
                                            <th>Last Changed</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td><input type="checkbox" style="margin: 0;"></td>
                                            <td>(954) 123-4567</td>
                                            <td>John Smith</td>
                                            <td>Male_Greeting_1.mp3</td>
                                            <td>2 weeks ago</td>
                                            <td>
                                                <button class="form-button secondary-button">Change</button>
                                                <button class="form-button secondary-button">▶ Play</button>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td><input type="checkbox" style="margin: 0;"></td>
                                            <td>(786) 987-6543</td>
                                            <td>Jane Doe</td>
                                            <td>Female_Casual_2.mp3</td>
                                            <td>1 week ago</td>
                                            <td>
                                                <button class="form-button secondary-button">Change</button>
                                                <button class="form-button secondary-button">▶ Play</button>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td><input type="checkbox" style="margin: 0;"></td>
                                            <td>(305) 456-7890</td>
                                            <td>Robert Johnson</td>
                                            <td>Male_Business_3.mp3</td>
                                            <td>3 days ago</td>
                                            <td>
                                                <button class="form-button secondary-button">Change</button>
                                                <button class="form-button secondary-button">▶ Play</button>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td><input type="checkbox" style="margin: 0;"></td>
                                            <td>(754) 321-0987</td>
                                            <td>Sarah Williams</td>
                                            <td>Female_Professional_1.mp3</td>
                                            <td>5 days ago</td>
                                            <td>
                                                <button class="form-button secondary-button">Change</button>
                                                <button class="form-button secondary-button">▶ Play</button>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                                
                                <div style="margin-top: 20px; display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <button class="form-button secondary-button">Assign Selected</button>
                                        <button class="form-button secondary-button">Change Selected</button>
                                    </div>
                                    <div>
                                        <button class="form-button secondary-button">Previous</button>
                                        <button class="form-button secondary-button">Next</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
    )

@app.route('/campaign-schedule')
def campaign_schedule_route():
    """The campaign scheduling interface"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Campaign Schedule",
        active_page="/campaign-schedule",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <div style="font-size: 20px; font-weight: bold; color: #EEE;">Campaign Schedule</div>
                    <div>
                        <button class="form-button">New Schedule</button>
                    </div>
                </div>
                
                <div style="display: flex; gap: 20px; height: calc(100% - 60px);">
                    <!-- Schedule Editor Panel -->
                    <div style="width: 350px;">
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px; height: 100%;">
                            <div style="font-size: 16px; font-weight: bold; margin-bottom: 20px; color: #EEE;">
                                Schedule Settings
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Schedule Name</label>
                                <input type="text" class="form-input" value="Weekday Campaign" placeholder="Enter schedule name">
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Campaign</label>
                                <select class="form-select">
                                    <option selected>Spring Promotion</option>
                                    <option>Weekend Special</option>
                                    <option>NBA Finals Promo</option>
                                </select>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Active Days</label>
                                <div style="display: flex; flex-wrap: wrap; gap: 5px; margin-top: 5px;">
                                    <button class="form-button secondary-button" style="min-width: 40px;">Sun</button>
                                    <button class="form-button" style="min-width: 40px;">Mon</button>
                                    <button class="form-button" style="min-width: 40px;">Tue</button>
                                    <button class="form-button" style="min-width: 40px;">Wed</button>
                                    <button class="form-button" style="min-width: 40px;">Thu</button>
                                    <button class="form-button" style="min-width: 40px;">Fri</button>
                                    <button class="form-button secondary-button" style="min-width: 40px;">Sat</button>
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Active Hours</label>
                                <div style="display: flex; gap: 10px; align-items: center;">
                                    <input type="text" class="form-input" value="8" style="width: 60px;">
                                    <span style="color: #CCC;">to</span>
                                    <input type="text" class="form-input" value="20" style="width: 60px;">
                                </div>
                                <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                    8:00 AM to 8:00 PM
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Message Distribution</label>
                                <select class="form-select">
                                    <option selected>Evenly throughout active hours</option>
                                    <option>Front-loaded (more in morning)</option>
                                    <option>Back-loaded (more in afternoon)</option>
                                    <option>Custom distribution</option>
                                </select>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Maximum Messages</label>
                                <input type="text" class="form-input" value="10,000" placeholder="Enter max messages per day">
                                <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                    Per active day
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Schedule Status</label>
                                <select class="form-select">
                                    <option selected>Active</option>
                                    <option>Paused</option>
                                    <option>Draft</option>
                                </select>
                            </div>
                            
                            <div style="display: flex; gap: 10px; margin-top: 20px;">
                                <button class="form-button secondary-button" style="flex: 1;">Reset</button>
                                <button class="form-button" style="flex: 1;">Save Schedule</button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Schedule Visualization Panel -->
                    <div style="flex: 1;">
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px; height: 100%;">
                            <div style="font-size: 16px; font-weight: bold; margin-bottom: 20px; color: #EEE;">
                                Schedule Calendar
                            </div>
                            
                            <div style="background-color: #2A2A2A; border-radius: 6px; padding: 15px; margin-bottom: 20px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                                    <div style="font-weight: bold; color: #EEE;">April 2024</div>
                                    <div>
                                        <button class="form-button secondary-button">◀</button>
                                        <button class="form-button secondary-button">Today</button>
                                        <button class="form-button secondary-button">▶</button>
                                    </div>
                                </div>
                                
                                <table style="width: 100%; border-collapse: collapse; text-align: center;">
                                    <thead>
                                        <tr>
                                            <th style="padding: 10px; color: #CCC;">Sun</th>
                                            <th style="padding: 10px; color: #CCC;">Mon</th>
                                            <th style="padding: 10px; color: #CCC;">Tue</th>
                                            <th style="padding: 10px; color: #CCC;">Wed</th>
                                            <th style="padding: 10px; color: #CCC;">Thu</th>
                                            <th style="padding: 10px; color: #CCC;">Fri</th>
                                            <th style="padding: 10px; color: #CCC;">Sat</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td style="padding: 10px; color: #777;">31</td>
                                            <td style="padding: 10px; color: #EEE;">1</td>
                                            <td style="padding: 10px; color: #EEE;">2</td>
                                            <td style="padding: 10px; color: #EEE;">3</td>
                                            <td style="padding: 10px; color: #EEE;">4</td>
                                            <td style="padding: 10px; color: #EEE;">5</td>
                                            <td style="padding: 10px; color: #EEE;">6</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 10px; color: #EEE;">7</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.2); border-radius: 4px;">8</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.2); border-radius: 4px;">9</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.2); border-radius: 4px;">10</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.2); border-radius: 4px;">11</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.2); border-radius: 4px;">12</td>
                                            <td style="padding: 10px; color: #EEE;">13</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 10px; color: #EEE;">14</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.2); border-radius: 4px;">15</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.2); border-radius: 4px;">16</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.2); border-radius: 4px;">17</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.2); border-radius: 4px;">18</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.2); border-radius: 4px;">19</td>
                                            <td style="padding: 10px; color: #EEE;">20</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 10px; color: #EEE;">21</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.2); border-radius: 4px;">22</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.2); border-radius: 4px;">23</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.2); border-radius: 4px;">24</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.6); border-radius: 4px; font-weight: bold;">25</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.2); border-radius: 4px;">26</td>
                                            <td style="padding: 10px; color: #EEE;">27</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 10px; color: #EEE;">28</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.2); border-radius: 4px;">29</td>
                                            <td style="padding: 10px; color: #EEE; background-color: rgba(255, 102, 0, 0.2); border-radius: 4px;">30</td>
                                            <td style="padding: 10px; color: #777;">1</td>
                                            <td style="padding: 10px; color: #777;">2</td>
                                            <td style="padding: 10px; color: #777;">3</td>
                                            <td style="padding: 10px; color: #777;">4</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            
                            <div style="background-color: #2A2A2A; border-radius: 6px; padding: 15px;">
                                <div style="font-weight: bold; color: #EEE; margin-bottom: 15px;">Today's Schedule (April 25)</div>
                                
                                <div style="margin-bottom: 20px;">
                                    <div style="font-size: 14px; color: #CCC; margin-bottom: 10px;">Message Distribution</div>
                                    <div style="height: 25px; background-color: #333; border-radius: 4px; position: relative;">
                                        <div style="position: absolute; top: 0; bottom: 0; left: 0; width: 2px; background-color: #FF6600;"></div>
                                        <div style="position: absolute; top: 0; bottom: 0; left: 33.3%; width: 2px; background-color: #FF6600;"></div>
                                        <div style="position: absolute; top: 0; bottom: 0; left: 66.6%; width: 2px; background-color: #FF6600;"></div>
                                        <div style="position: absolute; top: 0; bottom: 0; right: 0; width: 2px; background-color: #FF6600;"></div>
                                        
                                        <div style="position: absolute; top: -20px; left: 0; color: #AAA; font-size: 12px;">8am</div>
                                        <div style="position: absolute; top: -20px; left: 33.3%; color: #AAA; font-size: 12px; transform: translateX(-50%);">12pm</div>
                                        <div style="position: absolute; top: -20px; left: 66.6%; color: #AAA; font-size: 12px; transform: translateX(-50%);">4pm</div>
                                        <div style="position: absolute; top: -20px; right: 0; color: #AAA; font-size: 12px;">8pm</div>
                                        
                                        <!-- Distribution Bars -->
                                        <div style="position: absolute; bottom: 0; left: 0%; height: 60%; width: 8.33%; background-color: #FF6600; opacity: 0.6;"></div>
                                        <div style="position: absolute; bottom: 0; left: 8.33%; height: 70%; width: 8.33%; background-color: #FF6600; opacity: 0.6;"></div>
                                        <div style="position: absolute; bottom: 0; left: 16.66%; height: 85%; width: 8.33%; background-color: #FF6600; opacity: 0.6;"></div>
                                        <div style="position: absolute; bottom: 0; left: 25%; height: 100%; width: 8.33%; background-color: #FF6600; opacity: 0.6;"></div>
                                        <div style="position: absolute; bottom: 0; left: 33.33%; height: 90%; width: 8.33%; background-color: #FF6600; opacity: 0.6;"></div>
                                        <div style="position: absolute; bottom: 0; left: 41.66%; height: 75%; width: 8.33%; background-color: #FF6600; opacity: 0.6;"></div>
                                        <div style="position: absolute; bottom: 0; left: 50%; height: 80%; width: 8.33%; background-color: #FF6600; opacity: 0.6;"></div>
                                        <div style="position: absolute; bottom: 0; left: 58.33%; height: 95%; width: 8.33%; background-color: #FF6600; opacity: 0.6;"></div>
                                        <div style="position: absolute; bottom: 0; left: 66.66%; height: 100%; width: 8.33%; background-color: #FF6600; opacity: 0.6;"></div>
                                        <div style="position: absolute; bottom: 0; left: 75%; height: 80%; width: 8.33%; background-color: #FF6600; opacity: 0.6;"></div>
                                        <div style="position: absolute; bottom: 0; left: 83.33%; height: 60%; width: 8.33%; background-color: #FF6600; opacity: 0.6;"></div>
                                        <div style="position: absolute; bottom: 0; left: 91.66%; height: 40%; width: 8.33%; background-color: #FF6600; opacity: 0.6;"></div>
                                    </div>
                                </div>
                                
                                <div style="display: flex; gap: 15px; margin-bottom: 15px;">
                                    <div style="flex: 1; background-color: #333; border-radius: 4px; padding: 15px; text-align: center;">
                                        <div style="font-size: 24px; font-weight: bold; color: #FF6600;">10,000</div>
                                        <div style="color: #AAA; font-size: 14px;">Scheduled Messages</div>
                                    </div>
                                    <div style="flex: 1; background-color: #333; border-radius: 4px; padding: 15px; text-align: center;">
                                        <div style="font-size: 24px; font-weight: bold; color: #4CAF50;">3,427</div>
                                        <div style="color: #AAA; font-size: 14px;">Sent So Far</div>
                                    </div>
                                    <div style="flex: 1; background-color: #333; border-radius: 4px; padding: 15px; text-align: center;">
                                        <div style="font-size: 24px; font-weight: bold; color: #FF6600;">6,573</div>
                                        <div style="color: #AAA; font-size: 14px;">Remaining</div>
                                    </div>
                                </div>
                                
                                <div style="display: flex; justify-content: space-between; margin-top: 20px;">
                                    <button class="form-button secondary-button">Pause Today</button>
                                    <button class="form-button secondary-button">View Details</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
    )

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Process assets before starting the server
    process_assets()
    
    print("\n" + "="*60)
    print("COMPLETE PROGRESS GHOST CREATOR - ALL SECTIONS WITH CLICKABLE BUTTONS")
    print("="*60)
    print("\nAccess the application in your web browser at: http://localhost:5000")
    print("\nThis version includes ALL sections including voicemail management.")
    print("All buttons and navigation links are now properly clickable.")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)