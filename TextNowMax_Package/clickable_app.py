"""
ProgressGhostCreator app with CLICKABLE BUTTONS

This version focuses on making all buttons and navigation links clickable
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

# Base HTML template with working navigation
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
            color: white;
            background-color: #1E1E1E;
            background-image: url('/static/progress_background.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        
        .app-container {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        
        .app-header {
            background-color: rgba(30, 30, 30, 0.9);
            padding: 15px;
            display: flex;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
            z-index: 100;
        }
        
        .app-logo {
            height: 40px;
            margin-right: 15px;
        }
        
        .app-nav {
            display: flex;
            align-items: center;
            margin-left: 20px;
        }
        
        .nav-item {
            color: #CCC;
            text-decoration: none;
            padding: 8px 15px;
            margin-right: 5px;
            border-radius: 4px;
            transition: background-color 0.2s, color 0.2s;
            cursor: pointer; /* Ensure cursor shows it's clickable */
        }
        
        .nav-item:hover {
            background-color: #333;
            color: white;
        }
        
        .nav-item.active {
            background-color: #FF6600;
            color: white;
        }
        
        .app-content {
            flex: 1;
            padding: 30px;
        }
        
        .app-footer {
            background-color: rgba(20, 20, 20, 0.9);
            padding: 15px;
            text-align: center;
            color: #777;
            font-size: 12px;
            box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.3);
        }
        
        /* Button styles */
        button, .button {
            background-color: #FF6600;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            transition: background-color 0.2s;
            display: inline-block;
            text-decoration: none;
        }
        
        button:hover, .button:hover {
            background-color: #FF8533;
        }
        
        .secondary-button {
            background-color: #444;
            color: #FFF;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            transition: background-color 0.2s;
        }
        
        .secondary-button:hover {
            background-color: #555;
        }
        
        /* Status messages */
        .status-message {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background-color: rgba(40, 40, 40, 0.9);
            color: #FFF;
            border-radius: 5px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            display: none;
        }
        
        .status-message.success {
            background-color: rgba(40, 180, 40, 0.9);
        }
        
        .status-message.error {
            background-color: rgba(180, 40, 40, 0.9);
        }
    </style>
    <script>
        function showMessage(message, type) {
            // Create message element
            var msgElement = document.createElement('div');
            msgElement.className = 'status-message ' + (type || '');
            msgElement.textContent = message;
            document.body.appendChild(msgElement);
            
            // Show message
            setTimeout(function() {
                msgElement.style.display = 'block';
            }, 100);
            
            // Hide and remove after 3 seconds
            setTimeout(function() {
                msgElement.style.opacity = '0';
                msgElement.style.transition = 'opacity 0.5s';
                setTimeout(function() {
                    document.body.removeChild(msgElement);
                }, 500);
            }, 3000);
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            // Make all buttons show feedback when clicked
            document.querySelectorAll('button, .button, .nav-item, .secondary-button').forEach(function(button) {
                button.addEventListener('click', function(e) {
                    // Don't prevent default for links with href
                    if (!this.getAttribute('href')) {
                        e.preventDefault();
                        
                        // Show message based on button text
                        var buttonText = this.textContent.trim();
                        showMessage('Clicked: ' + buttonText, 'success');
                    }
                    
                    // Add visual feedback
                    this.style.transform = 'scale(0.95)';
                    this.style.opacity = '0.8';
                    
                    // Reset after 100ms
                    var btn = this;
                    setTimeout(function() {
                        btn.style.transform = '';
                        btn.style.opacity = '';
                    }, 100);
                });
            });
        });
    </script>
</head>
<body>
    <div class="app-container">
        <div class="app-header">
            <img src="/static/progress_logo.png" alt="Logo" class="app-logo">
            
            <div class="app-nav">
                <a href="/" class="nav-item {{ 'active' if active_page == '/' else '' }}">Home</a>
                <a href="/creator" class="nav-item {{ 'active' if active_page == '/creator' else '' }}">Create Accounts</a>
                <a href="/dashboard" class="nav-item {{ 'active' if active_page == '/dashboard' else '' }}">Dashboard</a>
                <a href="/campaigns" class="nav-item {{ 'active' if active_page == '/campaigns' else '' }}">Campaigns</a>
                <a href="/message-templates" class="nav-item {{ 'active' if active_page == '/message-templates' else '' }}">Templates</a>
                <a href="/manual-messaging" class="nav-item {{ 'active' if active_page == '/manual-messaging' else '' }}">Messaging</a>
                <a href="/message-dashboard" class="nav-item {{ 'active' if active_page == '/message-dashboard' else '' }}">Monitor</a>
                <a href="/account-health" class="nav-item {{ 'active' if active_page == '/account-health' else '' }}">Health</a>
            </div>
        </div>
        
        {{ content | safe }}
        
        <div class="app-footer">
            © ProgressBets™ | TextNow v1.0.0 | 5 Accounts Active
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    """Display the mockup of the ProgressGhostCreator application"""
    return render_template_string(
        BASE_HTML, 
        title="Home",
        active_page="/",
        content='''
        <div class="app-content">
            <div style="background-color: rgba(40, 40, 40, 0.9); border-radius: 10px; padding: 30px; max-width: 800px; margin: 0 auto; box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3); text-align: center;">
                <h1 style="color: #FF6600; margin-top: 0;">Welcome to ProgressGhostCreator</h1>
                <p>The advanced TextNow account management and automation platform. Create, manage, and utilize ghost accounts with sophisticated distribution, voicemail setup, and messaging capabilities.</p>
                
                <div style="display: flex; justify-content: center; gap: 15px; margin: 30px 0;">
                    <a href="/creator" class="button">Create Accounts</a>
                    <a href="/dashboard" class="button">Manage Accounts</a>
                    <a href="/campaigns" class="button">Campaigns</a>
                </div>
            
                <div style="display: flex; justify-content: space-between; margin: 30px 0; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 120px; background-color: rgba(60, 60, 60, 0.7); border-radius: 5px; padding: 15px; margin: 5px;">
                        <div style="font-size: 24px; font-weight: bold; color: #FF6600;">10,563</div>
                        <div style="font-size: 14px; margin-top: 5px; color: #CCC;">Ghost Accounts</div>
                    </div>
                    <div style="flex: 1; min-width: 120px; background-color: rgba(60, 60, 60, 0.7); border-radius: 5px; padding: 15px; margin: 5px;">
                        <div style="font-size: 24px; font-weight: bold; color: #FF6600;">5,219</div>
                        <div style="font-size: 14px; margin-top: 5px; color: #CCC;">Active Accounts</div>
                    </div>
                    <div style="flex: 1; min-width: 120px; background-color: rgba(60, 60, 60, 0.7); border-radius: 5px; padding: 15px; margin: 5px;">
                        <div style="font-size: 24px; font-weight: bold; color: #FF6600;">892,145</div>
                        <div style="font-size: 14px; margin-top: 5px; color: #CCC;">Messages Sent</div>
                    </div>
                    <div style="flex: 1; min-width: 120px; background-color: rgba(60, 60, 60, 0.7); border-radius: 5px; padding: 15px; margin: 5px;">
                        <div style="font-size: 24px; font-weight: bold; color: #FF6600;">98.7%</div>
                        <div style="font-size: 14px; margin-top: 5px; color: #CCC;">Success Rate</div>
                    </div>
                </div>
                
                <div style="margin-top: 30px; color: #777; font-size: 12px;">ProgressGhostCreator v1.0.0 | © 2024 ProgressBets™ | 5 Accounts Active</div>
            </div>
        </div>
        '''
    )

@app.route('/creator')
def creator_page():
    """The main account creator page with area code input and start button"""
    return render_template_string(
        BASE_HTML,
        title="Account Creator",
        active_page="/creator",
        content='''
        <div class="app-content" style="display: flex;">
            <div style="width: 300px; background-color: rgba(35, 35, 35, 0.9); padding: 20px; border-radius: 10px; margin-right: 20px;">
                <div style="font-size: 16px; font-weight: bold; margin-bottom: 20px; color: #EEE;">Account Creation Settings</div>
                
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; color: #CCC;">Number of Accounts</label>
                    <input type="number" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;" value="100" min="1" max="10000">
                </div>
                
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; color: #CCC;">Device Mode</label>
                    <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;">
                        <option selected>Production (BLU G44)</option>
                        <option>Demo (No Device)</option>
                    </select>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; color: #CCC;">Area Codes</label>
                    <input type="text" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;" placeholder="Enter area codes separated by commas" value="954, 754, 305, 786, 561">
                    <div style="margin-top: 8px; font-size: 12px; color: #AAA;">Enter any area codes you want, separated by commas</div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; color: #CCC;">Area Code Presets</label>
                    <div style="display: flex; gap: 5px; flex-wrap: wrap;">
                        <button class="secondary-button">Florida</button>
                        <button class="secondary-button">Georgia</button>
                        <button class="secondary-button">New York</button>
                    </div>
                </div>
                
                <button style="width: 100%; padding: 12px; margin-top: 25px; background-color: #FF6600; color: white; font-weight: bold; border: none; border-radius: 4px; cursor: pointer;">START CREATION</button>
            </div>
            
            <div style="flex: 1; background-color: rgba(35, 35, 35, 0.9); padding: 20px; border-radius: 10px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <div style="font-size: 16px; font-weight: bold; color: #EEE;">Account Creator</div>
                    <div style="color: #CCC;">Total Accounts: 10,563</div>
                </div>
                
                <div style="background-color: rgba(30, 30, 30, 0.7); padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <div style="font-weight: bold; color: #EEE;">Current Batch Status</div>
                        <div>
                            <button class="secondary-button">Pause</button>
                            <button class="secondary-button">Cancel</button>
                        </div>
                    </div>
                    
                    <div style="height: 20px; background-color: #333; border-radius: 10px; margin-bottom: 10px; overflow: hidden;">
                        <div style="width: 35%; height: 100%; background-color: #FF6600; border-radius: 10px;"></div>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; font-size: 14px; color: #CCC;">
                        <div>Created: 35 / 100</div>
                        <div>Success Rate: 100%</div>
                        <div>Time Left: 32m 18s</div>
                    </div>
                </div>
                
                <div style="background-color: rgba(30, 30, 30, 0.7); padding: 15px; border-radius: 6px; flex: 1;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <div style="font-weight: bold; color: #EEE;">Process Log</div>
                        <div>
                            <button class="secondary-button">Clear</button>
                            <button class="secondary-button">Export</button>
                        </div>
                    </div>
                    
                    <div style="height: 300px; overflow-y: auto; font-family: monospace; font-size: 13px; background-color: #222; padding: 10px; border-radius: 4px;">
                        <div style="margin-bottom: 5px;">
                            <span style="color: #888;">[14:45:32]</span> <span style="color: #5F5;">Account created: Sarah Johnson (786-123-4567)</span>
                        </div>
                        <div style="margin-bottom: 5px;">
                            <span style="color: #888;">[14:44:18]</span> <span style="color: #5F5;">Voicemail setup completed for: 786-123-4567</span>
                        </div>
                        <div style="margin-bottom: 5px;">
                            <span style="color: #888;">[14:43:55]</span> <span style="color: #5F5;">Account verified: 786-123-4567</span>
                        </div>
                        <div style="margin-bottom: 5px;">
                            <span style="color: #888;">[14:43:22]</span> <span style="color: #5F5;">Phone number assigned: 786-123-4567</span>
                        </div>
                        <div style="margin-bottom: 5px;">
                            <span style="color: #888;">[14:42:45]</span> <span style="color: #5F5;">Registration form submitted: sarah.johnson91@example.com</span>
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
    return render_template_string(
        BASE_HTML,
        title="Dashboard",
        active_page="/dashboard",
        content='''
        <div class="app-content">
            <div style="background-color: rgba(35, 35, 35, 0.9); padding: 20px; border-radius: 10px; max-width: 1000px; margin: 0 auto;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <div style="font-size: 18px; font-weight: bold; color: #EEE;">Account Dashboard</div>
                    <div>
                        <button class="secondary-button">Export CSV</button>
                        <button class="button">Add Account</button>
                    </div>
                </div>
                
                <div style="margin-bottom: 20px; display: flex; gap: 10px;">
                    <input type="text" style="flex: 1; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;" placeholder="Search accounts...">
                    <button class="secondary-button">Search</button>
                    <button class="secondary-button">Filter</button>
                </div>
                
                <div style="background-color: #2A2A2A; border-radius: 6px; overflow: hidden;">
                    <table style="width: 100%; border-collapse: collapse; color: #CCC;">
                        <thead>
                            <tr style="background-color: #333; color: #EEE;">
                                <th style="padding: 12px; text-align: left;">Phone Number</th>
                                <th style="padding: 12px; text-align: left;">Name</th>
                                <th style="padding: 12px; text-align: left;">Area Code</th>
                                <th style="padding: 12px; text-align: left;">Status</th>
                                <th style="padding: 12px; text-align: left;">Last Used</th>
                                <th style="padding: 12px; text-align: left;">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom: 1px solid #444;">
                                <td style="padding: 10px;">(954) 123-4567</td>
                                <td style="padding: 10px;">John Smith</td>
                                <td style="padding: 10px;">954</td>
                                <td style="padding: 10px;"><span style="background-color: #5F5; color: #333; padding: 3px 8px; border-radius: 10px; font-size: 12px;">Active</span></td>
                                <td style="padding: 10px;">Today, 2:30 PM</td>
                                <td style="padding: 10px;">
                                    <button class="secondary-button">Edit</button>
                                    <button class="secondary-button">Login</button>
                                </td>
                            </tr>
                            <tr style="border-bottom: 1px solid #444;">
                                <td style="padding: 10px;">(786) 987-6543</td>
                                <td style="padding: 10px;">Jane Doe</td>
                                <td style="padding: 10px;">786</td>
                                <td style="padding: 10px;"><span style="background-color: #5F5; color: #333; padding: 3px 8px; border-radius: 10px; font-size: 12px;">Active</span></td>
                                <td style="padding: 10px;">Today, 1:15 PM</td>
                                <td style="padding: 10px;">
                                    <button class="secondary-button">Edit</button>
                                    <button class="secondary-button">Login</button>
                                </td>
                            </tr>
                            <tr style="border-bottom: 1px solid #444;">
                                <td style="padding: 10px;">(305) 456-7890</td>
                                <td style="padding: 10px;">Robert Johnson</td>
                                <td style="padding: 10px;">305</td>
                                <td style="padding: 10px;"><span style="background-color: #FA3; color: #333; padding: 3px 8px; border-radius: 10px; font-size: 12px;">Warning</span></td>
                                <td style="padding: 10px;">Yesterday, 5:45 PM</td>
                                <td style="padding: 10px;">
                                    <button class="secondary-button">Edit</button>
                                    <button class="secondary-button">Login</button>
                                </td>
                            </tr>
                            <tr style="border-bottom: 1px solid #444;">
                                <td style="padding: 10px;">(754) 321-0987</td>
                                <td style="padding: 10px;">Sarah Williams</td>
                                <td style="padding: 10px;">754</td>
                                <td style="padding: 10px;"><span style="background-color: #F55; color: #333; padding: 3px 8px; border-radius: 10px; font-size: 12px;">Flagged</span></td>
                                <td style="padding: 10px;">3 days ago</td>
                                <td style="padding: 10px;">
                                    <button class="secondary-button">Edit</button>
                                    <button class="secondary-button">Replace</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div style="margin-top: 20px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="color: #AAA; font-size: 14px;">Showing 4 of 10,563 accounts</div>
                    <div>
                        <button class="secondary-button">Previous</button>
                        <button class="secondary-button">Next</button>
                    </div>
                </div>
            </div>
        </div>
        '''
    )

@app.route('/campaigns')
def campaigns_page():
    """The campaigns management page"""
    return render_template_string(
        BASE_HTML,
        title="Campaigns",
        active_page="/campaigns",
        content='''
        <div class="app-content">
            <div style="background-color: rgba(35, 35, 35, 0.9); padding: 20px; border-radius: 10px; max-width: 1000px; margin: 0 auto;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <div style="font-size: 18px; font-weight: bold; color: #EEE;">Campaign Manager</div>
                    <div>
                        <button class="button">Create Campaign</button>
                    </div>
                </div>
                
                <div style="display: flex; gap: 20px;">
                    <div style="width: 300px; background-color: #2A2A2A; padding: 15px; border-radius: 6px;">
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE;">Create Campaign</div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Campaign Name</label>
                            <input type="text" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;" placeholder="Enter campaign name">
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Message Template</label>
                            <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;">
                                <option selected>Spring Promotion</option>
                                <option>Welcome Message</option>
                                <option>Sports Event</option>
                            </select>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Target Numbers</label>
                            <div style="display: flex; gap: 5px; align-items: center;">
                                <input type="file" id="targetNumbersFile" style="display: none;">
                                <button onclick="document.getElementById('targetNumbersFile').click()" class="secondary-button" style="flex: 1;">Upload CSV</button>
                                <span style="color: #CCC; font-size: 12px;">0 numbers</span>
                            </div>
                            <div style="margin-top: 5px; font-size: 12px; color: #F55; font-weight: bold;">Target numbers file is required</div>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Schedule</label>
                            <div style="display: flex; gap: 5px;">
                                <select style="flex: 1; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;">
                                    <option selected>Start Immediately</option>
                                    <option>Schedule Time</option>
                                </select>
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Active Hours</label>
                            <div style="display: flex; gap: 5px;">
                                <input type="text" style="flex: 1; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;" value="8" placeholder="Start">
                                <span style="color: #CCC; line-height: 34px;">to</span>
                                <input type="text" style="flex: 1; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;" value="20" placeholder="End">
                            </div>
                            <div style="margin-top: 5px; font-size: 12px; color: #AAA;">8:00 AM to 8:00 PM</div>
                        </div>
                        
                        <button style="width: 100%; padding: 12px; margin-top: 15px; background-color: #FF6600; color: white; font-weight: bold; border: none; border-radius: 4px; cursor: pointer;">START CAMPAIGN</button>
                    </div>
                    
                    <div style="flex: 1; background-color: #2A2A2A; padding: 15px; border-radius: 6px;">
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE;">Active Campaigns</div>
                        
                        <div style="background-color: #333; padding: 10px; border-radius: 4px; margin-bottom: 10px; border-left: 3px solid #FF6600; cursor: pointer;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <div style="font-weight: bold; color: #EEE;">Spring Promotion</div>
                                <div style="font-size: 12px; color: #5F5;">Active</div>
                            </div>
                            <div style="font-size: 12px; color: #CCC;">10,000 targets • 35% complete • 8am-8pm</div>
                            <div style="display: flex; gap: 5px; margin-top: 10px;">
                                <button class="secondary-button">Pause</button>
                                <button class="secondary-button">View Details</button>
                            </div>
                        </div>
                        
                        <div style="background-color: #2D2D2D; padding: 10px; border-radius: 4px; margin-bottom: 10px; cursor: pointer;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <div style="font-weight: bold; color: #EEE;">Weekend Special</div>
                                <div style="font-size: 12px; color: #FA3;">Paused</div>
                            </div>
                            <div style="font-size: 12px; color: #CCC;">5,000 targets • 42% complete • 9am-9pm</div>
                            <div style="display: flex; gap: 5px; margin-top: 10px;">
                                <button class="secondary-button">Resume</button>
                                <button class="secondary-button">View Details</button>
                            </div>
                        </div>
                        
                        <div style="background-color: #2D2D2D; padding: 10px; border-radius: 4px; margin-bottom: 10px; cursor: pointer;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <div style="font-weight: bold; color: #EEE;">NBA Finals Promo</div>
                                <div style="font-size: 12px; color: #AAA;">Draft</div>
                            </div>
                            <div style="font-size: 12px; color: #CCC;">7,500 targets • Not started • Not scheduled</div>
                            <div style="display: flex; gap: 5px; margin-top: 10px;">
                                <button class="secondary-button">Edit</button>
                                <button class="secondary-button">Start</button>
                            </div>
                        </div>
                        
                        <div style="margin-top: 20px; font-size: 16px; font-weight: bold; color: #EEE;">Completed Campaigns</div>
                        
                        <div style="background-color: #2D2D2D; padding: 10px; border-radius: 4px; margin-top: 10px; cursor: pointer;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <div style="font-weight: bold; color: #EEE;">March Madness</div>
                                <div style="font-size: 12px; color: #AAA;">Completed</div>
                            </div>
                            <div style="font-size: 12px; color: #CCC;">8,750 targets • 100% complete • April 5</div>
                            <div style="display: flex; gap: 5px; margin-top: 10px;">
                                <button class="secondary-button">View Report</button>
                                <button class="secondary-button">Clone</button>
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
    return render_template_string(
        BASE_HTML,
        title="Message Templates",
        active_page="/message-templates",
        content='''
        <div class="app-content">
            <div style="background-color: rgba(35, 35, 35, 0.9); padding: 20px; border-radius: 10px; max-width: 1000px; margin: 0 auto;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <div style="font-size: 18px; font-weight: bold; color: #EEE;">Message Templates</div>
                    <div>
                        <button class="button">New Template</button>
                    </div>
                </div>
                
                <div style="display: flex; gap: 20px;">
                    <div style="width: 300px; background-color: #2A2A2A; padding: 15px; border-radius: 6px; max-height: 600px; overflow-y: auto;">
                        <div style="margin-bottom: 10px;">
                            <input type="text" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;" placeholder="Search templates...">
                        </div>
                        
                        <div style="margin-top: 15px; font-size: 14px; font-weight: bold; color: #CCC; padding-bottom: 5px; border-bottom: 1px solid #444;">
                            Saved Templates
                        </div>
                        
                        <div style="padding: 10px; background-color: #3D3D3D; margin: 10px 0; border-radius: 4px; cursor: pointer; border-left: 3px solid #FF6600;">
                            <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Spring Promotion</div>
                            <div style="font-size: 12px; color: #CCC;">Last edited: 2 days ago</div>
                        </div>
                        
                        <div style="padding: 10px; background-color: #333; margin: 10px 0; border-radius: 4px; cursor: pointer;">
                            <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Welcome Message</div>
                            <div style="font-size: 12px; color: #CCC;">Last edited: 1 week ago</div>
                        </div>
                        
                        <div style="padding: 10px; background-color: #333; margin: 10px 0; border-radius: 4px; cursor: pointer;">
                            <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Sports Event</div>
                            <div style="font-size: 12px; color: #CCC;">Last edited: 2 weeks ago</div>
                        </div>
                        
                        <div style="padding: 10px; background-color: #333; margin: 10px 0; border-radius: 4px; cursor: pointer;">
                            <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Customer Follow-up</div>
                            <div style="font-size: 12px; color: #CCC;">Last edited: 3 weeks ago</div>
                        </div>
                    </div>
                    
                    <div style="flex: 1; background-color: #2A2A2A; padding: 15px; border-radius: 6px;">
                        <div style="margin-bottom: 15px;">
                            <input type="text" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;" value="Spring Promotion" placeholder="Template name">
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Message Text</label>
                            <textarea style="width: 100%; height: 200px; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE; resize: vertical;">Hey {{first_name}}, check out our latest sports odds for the upcoming games! Visit ProgressBets.com for exclusive offers and the best lines on {{event_name}}. Reply STOP to opt out.</textarea>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Variables</label>
                            <div style="font-size: 12px; color: #AAA; margin-bottom: 10px;">Click to add a variable to your message</div>
                            <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                                <button class="secondary-button">{{first_name}}</button>
                                <button class="secondary-button">{{last_name}}</button>
                                <button class="secondary-button">{{event_name}}</button>
                                <button class="secondary-button">{{city}}</button>
                                <button class="secondary-button">{{team}}</button>
                                <button class="secondary-button">{{odds}}</button>
                                <button class="secondary-button">{{date}}</button>
                                <button class="secondary-button">+ Add Custom</button>
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Image (Optional)</label>
                            <div style="display: flex; gap: 10px; align-items: center;">
                                <div style="width: 100px; height: 100px; background-color: #333; border-radius: 4px; display: flex; justify-content: center; align-items: center; color: #666;">No Image</div>
                                <div style="flex: 1;">
                                    <button class="secondary-button" style="width: 100%; margin-bottom: 5px;">Upload Image</button>
                                    <button class="secondary-button" style="width: 100%;">Select from Library</button>
                                </div>
                            </div>
                        </div>
                        
                        <div style="display: flex; gap: 10px; margin-top: 20px;">
                            <button class="secondary-button">Test Message</button>
                            <button class="secondary-button">Preview</button>
                            <div style="flex: 1;"></div>
                            <button class="secondary-button">Delete</button>
                            <button class="button">Save Template</button>
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
    return render_template_string(
        BASE_HTML,
        title="Manual Messaging",
        active_page="/manual-messaging",
        content='''
        <div class="app-content">
            <div style="background-color: rgba(35, 35, 35, 0.9); padding: 20px; border-radius: 10px; max-width: 1000px; margin: 0 auto;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <div style="font-size: 18px; font-weight: bold; color: #EEE;">Manual Messaging</div>
                    <div>
                        <button class="button">Send Message</button>
                    </div>
                </div>
                
                <div style="display: flex; gap: 20px;">
                    <div style="width: 350px; background-color: #2A2A2A; padding: 15px; border-radius: 6px;">
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE;">Sender Account</div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Select Account</label>
                            <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;">
                                <option>(954) 123-4567 - John Smith</option>
                                <option>(786) 987-6543 - Jane Doe</option>
                                <option>(305) 456-7890 - Robert Johnson</option>
                                <option>(754) 321-0987 - Sarah Williams</option>
                            </select>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Account Status</label>
                            <div style="padding: 10px; background-color: #333; border-radius: 4px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="color: #CCC;">Status:</div>
                                    <div style="color: #5F5;">Active</div>
                                </div>
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="color: #CCC;">Health Score:</div>
                                    <div style="color: #5F5;">95/100</div>
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
                        
                        <div style="font-size: 16px; font-weight: bold; margin: 20px 0 15px; color: #EEE;">Recipient</div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Phone Number</label>
                            <input type="text" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;" placeholder="Enter phone number">
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Name (Optional)</label>
                            <input type="text" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;" placeholder="Enter recipient name">
                        </div>
                    </div>
                    
                    <div style="flex: 1; background-color: #2A2A2A; padding: 15px; border-radius: 6px;">
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE;">Message</div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Template (Optional)</label>
                            <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;">
                                <option value="">-- Select Template --</option>
                                <option>Spring Promotion</option>
                                <option>Welcome Message</option>
                                <option>Sports Event</option>
                            </select>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Message Text</label>
                            <textarea style="width: 100%; height: 200px; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE; resize: vertical;" placeholder="Type your message here..."></textarea>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Attach Image (Optional)</label>
                            <div style="display: flex; gap: 10px;">
                                <button class="secondary-button" style="flex: 1;">Upload Image</button>
                                <button class="secondary-button" style="flex: 1;">Select from Library</button>
                            </div>
                        </div>
                        
                        <div style="display: flex; justify-content: space-between; margin-top: 20px;">
                            <button class="secondary-button">Save as Draft</button>
                            <button class="button">Send Message</button>
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
    return render_template_string(
        BASE_HTML,
        title="Message Monitor",
        active_page="/message-dashboard",
        content='''
        <div class="app-content">
            <div style="background-color: rgba(35, 35, 35, 0.9); padding: 20px; border-radius: 10px; max-width: 1200px; margin: 0 auto;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <div style="font-size: 18px; font-weight: bold; color: #EEE;">Message Monitor</div>
                    <div>
                        <button class="secondary-button">Export Data</button>
                        <button class="button">Refresh</button>
                    </div>
                </div>
                
                <div style="display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 200px; background-color: #2A2A2A; padding: 15px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 14px; color: #CCC; margin-bottom: 5px;">Total Messages Sent</div>
                        <div style="font-size: 24px; font-weight: bold; color: #FF6600;">892,145</div>
                    </div>
                    
                    <div style="flex: 1; min-width: 200px; background-color: #2A2A2A; padding: 15px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 14px; color: #CCC; margin-bottom: 5px;">Sent Today</div>
                        <div style="font-size: 24px; font-weight: bold; color: #FF6600;">3,427</div>
                    </div>
                    
                    <div style="flex: 1; min-width: 200px; background-color: #2A2A2A; padding: 15px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 14px; color: #CCC; margin-bottom: 5px;">Delivery Rate</div>
                        <div style="font-size: 24px; font-weight: bold; color: #FF6600;">98.7%</div>
                    </div>
                    
                    <div style="flex: 1; min-width: 200px; background-color: #2A2A2A; padding: 15px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 14px; color: #CCC; margin-bottom: 5px;">Response Rate</div>
                        <div style="font-size: 24px; font-weight: bold; color: #FF6600;">7.2%</div>
                    </div>
                </div>
                
                <div style="background-color: #2A2A2A; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 15px;">
                        <div style="display: flex; gap: 10px; flex: 2;">
                            <input type="text" style="flex: 1; padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;" placeholder="Search messages...">
                            <button class="secondary-button">Search</button>
                        </div>
                        
                        <div style="display: flex; gap: 10px; flex: 1; justify-content: flex-end;">
                            <select style="padding: 8px; border-radius: 4px; border: 1px solid #444; background-color: #333; color: #EEE;">
                                <option>All Messages</option>
                                <option>Delivered</option>
                                <option>Failed</option>
                                <option>With Responses</option>
                            </select>
                            <button class="secondary-button">Filter</button>
                        </div>
                    </div>
                    
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; color: #CCC; min-width: 800px;">
                            <thead>
                                <tr style="background-color: #333; color: #EEE;">
                                    <th style="padding: 12px; text-align: left;">Date/Time</th>
                                    <th style="padding: 12px; text-align: left;">From</th>
                                    <th style="padding: 12px; text-align: left;">To</th>
                                    <th style="padding: 12px; text-align: left;">Message</th>
                                    <th style="padding: 12px; text-align: left;">Status</th>
                                    <th style="padding: 12px; text-align: left;">Campaign</th>
                                    <th style="padding: 12px; text-align: left;">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr style="border-bottom: 1px solid #444;">
                                    <td style="padding: 10px;">2:45 PM</td>
                                    <td style="padding: 10px;">(954) 123-4567</td>
                                    <td style="padding: 10px;">(305) 555-7890</td>
                                    <td style="padding: 10px;">Hey Mark, check out our latest sports odds...</td>
                                    <td style="padding: 10px;"><span style="background-color: #5F5; color: #333; padding: 3px 8px; border-radius: 10px; font-size: 12px;">Delivered</span></td>
                                    <td style="padding: 10px;">Spring Promotion</td>
                                    <td style="padding: 10px;">
                                        <button class="secondary-button">View</button>
                                    </td>
                                </tr>
                                <tr style="border-bottom: 1px solid #444;">
                                    <td style="padding: 10px;">2:42 PM</td>
                                    <td style="padding: 10px;">(786) 987-6543</td>
                                    <td style="padding: 10px;">(561) 123-4567</td>
                                    <td style="padding: 10px;">Hey John, check out our latest sports odds...</td>
                                    <td style="padding: 10px;"><span style="background-color: #5F5; color: #333; padding: 3px 8px; border-radius: 10px; font-size: 12px;">Delivered</span></td>
                                    <td style="padding: 10px;">Spring Promotion</td>
                                    <td style="padding: 10px;">
                                        <button class="secondary-button">View</button>
                                    </td>
                                </tr>
                                <tr style="border-bottom: 1px solid #444;">
                                    <td style="padding: 10px;">2:38 PM</td>
                                    <td style="padding: 10px;">(305) 456-7890</td>
                                    <td style="padding: 10px;">(754) 987-6543</td>
                                    <td style="padding: 10px;">Hey Sarah, check out our latest sports odds...</td>
                                    <td style="padding: 10px;"><span style="background-color: #F55; color: #333; padding: 3px 8px; border-radius: 10px; font-size: 12px;">Failed</span></td>
                                    <td style="padding: 10px;">Spring Promotion</td>
                                    <td style="padding: 10px;">
                                        <button class="secondary-button">View</button>
                                    </td>
                                </tr>
                                <tr style="border-bottom: 1px solid #444;">
                                    <td style="padding: 10px;">2:32 PM</td>
                                    <td style="padding: 10px;">(754) 321-0987</td>
                                    <td style="padding: 10px;">(305) 111-2222</td>
                                    <td style="padding: 10px;">Hey Robert, check out our latest sports odds...</td>
                                    <td style="padding: 10px;"><span style="background-color: #5F5; color: #333; padding: 3px 8px; border-radius: 10px; font-size: 12px;">Delivered</span></td>
                                    <td style="padding: 10px;">Spring Promotion</td>
                                    <td style="padding: 10px;">
                                        <button class="secondary-button">View</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="color: #AAA; font-size: 14px;">Showing 4 of 3,427 messages</div>
                        <div>
                            <button class="secondary-button">Previous</button>
                            <button class="secondary-button">Next</button>
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
    return render_template_string(
        BASE_HTML,
        title="Account Health",
        active_page="/account-health",
        content='''
        <div class="app-content">
            <div style="background-color: rgba(35, 35, 35, 0.9); padding: 20px; border-radius: 10px; max-width: 1200px; margin: 0 auto;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <div style="font-size: 18px; font-weight: bold; color: #EEE;">Account Health Monitor</div>
                    <div>
                        <button class="secondary-button">Run Health Check</button>
                        <button class="button">Refresh</button>
                    </div>
                </div>
                
                <div style="display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 200px; background-color: #2A2A2A; padding: 15px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 14px; color: #CCC; margin-bottom: 5px;">Total Accounts</div>
                        <div style="font-size: 24px; font-weight: bold; color: #FF6600;">10,563</div>
                    </div>
                    
                    <div style="flex: 1; min-width: 200px; background-color: #2A2A2A; padding: 15px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 14px; color: #CCC; margin-bottom: 5px;">Healthy Accounts</div>
                        <div style="font-size: 24px; font-weight: bold; color: #5F5;">10,104</div>
                        <div style="font-size: 12px; color: #AAA;">95.7%</div>
                    </div>
                    
                    <div style="flex: 1; min-width: 200px; background-color: #2A2A2A; padding: 15px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 14px; color: #CCC; margin-bottom: 5px;">Flagged Accounts</div>
                        <div style="font-size: 24px; font-weight: bold; color: #FA3;">356</div>
                        <div style="font-size: 12px; color: #AAA;">3.4%</div>
                    </div>
                    
                    <div style="flex: 1; min-width: 200px; background-color: #2A2A2A; padding: 15px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 14px; color: #CCC; margin-bottom: 5px;">Blocked Accounts</div>
                        <div style="font-size: 24px; font-weight: bold; color: #F55;">103</div>
                        <div style="font-size: 12px; color: #AAA;">0.9%</div>
                    </div>
                </div>
                
                <div style="background-color: #2A2A2A; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                    <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE;">Account Health Issues</div>
                    
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; color: #CCC; min-width: 800px;">
                            <thead>
                                <tr style="background-color: #333; color: #EEE;">
                                    <th style="padding: 12px; text-align: left;">Phone Number</th>
                                    <th style="padding: 12px; text-align: left;">Account Name</th>
                                    <th style="padding: 12px; text-align: left;">Status</th>
                                    <th style="padding: 12px; text-align: left;">Health Score</th>
                                    <th style="padding: 12px; text-align: left;">Issue</th>
                                    <th style="padding: 12px; text-align: left;">Last Check</th>
                                    <th style="padding: 12px; text-align: left;">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr style="border-bottom: 1px solid #444;">
                                    <td style="padding: 10px;">(754) 321-0987</td>
                                    <td style="padding: 10px;">Sarah Williams</td>
                                    <td style="padding: 10px;"><span style="background-color: #F55; color: #333; padding: 3px 8px; border-radius: 10px; font-size: 12px;">Blocked</span></td>
                                    <td style="padding: 10px;">25/100</td>
                                    <td style="padding: 10px;">Account login failed: Invalid credentials</td>
                                    <td style="padding: 10px;">Today, 1:30 PM</td>
                                    <td style="padding: 10px;">
                                        <button class="secondary-button">Replace</button>
                                    </td>
                                </tr>
                                <tr style="border-bottom: 1px solid #444;">
                                    <td style="padding: 10px;">(305) 456-7890</td>
                                    <td style="padding: 10px;">Robert Johnson</td>
                                    <td style="padding: 10px;"><span style="background-color: #FA3; color: #333; padding: 3px 8px; border-radius: 10px; font-size: 12px;">Flagged</span></td>
                                    <td style="padding: 10px;">65/100</td>
                                    <td style="padding: 10px;">High message failure rate (12%)</td>
                                    <td style="padding: 10px;">Today, 12:45 PM</td>
                                    <td style="padding: 10px;">
                                        <button class="secondary-button">Health Check</button>
                                    </td>
                                </tr>
                                <tr style="border-bottom: 1px solid #444;">
                                    <td style="padding: 10px;">(786) 555-1234</td>
                                    <td style="padding: 10px;">Michael Brown</td>
                                    <td style="padding: 10px;"><span style="background-color: #FA3; color: #333; padding: 3px 8px; border-radius: 10px; font-size: 12px;">Flagged</span></td>
                                    <td style="padding: 10px;">72/100</td>
                                    <td style="padding: 10px;">CAPTCHA detected during login</td>
                                    <td style="padding: 10px;">Today, 11:20 AM</td>
                                    <td style="padding: 10px;">
                                        <button class="secondary-button">Health Check</button>
                                    </td>
                                </tr>
                                <tr style="border-bottom: 1px solid #444;">
                                    <td style="padding: 10px;">(954) 789-0123</td>
                                    <td style="padding: 10px;">Jennifer Davis</td>
                                    <td style="padding: 10px;"><span style="background-color: #F55; color: #333; padding: 3px 8px; border-radius: 10px; font-size: 12px;">Blocked</span></td>
                                    <td style="padding: 10px;">15/100</td>
                                    <td style="padding: 10px;">Account suspended by platform</td>
                                    <td style="padding: 10px;">Yesterday, 5:15 PM</td>
                                    <td style="padding: 10px;">
                                        <button class="secondary-button">Replace</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="color: #AAA; font-size: 14px;">Showing 4 of 459 flagged/blocked accounts</div>
                        <div>
                            <button class="secondary-button">Previous</button>
                            <button class="secondary-button">Next</button>
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
    print("PROGRESS GHOST CREATOR SERVER - CLICKABLE BUTTONS VERSION")
    print("="*60)
    print("\nAccess the application in your web browser at: http://localhost:5000")
    print("\nAll buttons are now clickable and will show feedback when clicked.")
    print("Try clicking any button, link, or navigation item to see the response.")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)