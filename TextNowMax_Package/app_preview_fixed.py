"""
Preview server for ProgressGhostCreator app - FIXED VERSION

This script creates a simple HTTP server that displays a mockup of the application
to showcase how it will look when running as a Windows executable.

Key fixes:
1. Navigation menu is fixed and appears on all pages
2. Area code input uses comma-separated text field rather than checkboxes
3. Start button added for account creation
"""

import os
import shutil
from flask import Flask, render_template_string, send_from_directory

app = Flask(__name__)

# Ensure static folder exists
os.makedirs('static', exist_ok=True)

# Base HTML for consistent page layout with fixed navigation
BASE_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>ProgressGhostCreator - {{ title }}</title>
    <script>
    // Function to add click effect for ALL elements
    function addClickEffect(e) {
        let target = e.target;
        
        // Create ripple effect element
        let effect = document.createElement('div');
        effect.className = 'ripple-effect';
        
        // Position at cursor location
        const rect = target.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        effect.style.left = x + 'px';
        effect.style.top = y + 'px';
        
        // Add to target and remove after animation
        target.appendChild(effect);
        
        setTimeout(function() {
            effect.remove();
        }, 500);
    }
    
    // Function to make EVERYTHING clickable with visual feedback
    window.onload = function() {
        // Add ripple styles
        let style = document.createElement('style');
        style.innerHTML = `
            .ripple-effect {
                position: absolute;
                background-color: rgba(255, 102, 0, 0.4);
                border-radius: 50%;
                width: 5px;
                height: 5px;
                pointer-events: none;
                animation: ripple 0.5s ease-out;
                z-index: 9999;
            }
            
            @keyframes ripple {
                to {
                    transform: scale(30);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
        
        // Make nav links work properly
        document.querySelectorAll('a.nav-link').forEach(function(link) {
            // Remove existing event listeners from nav links
            const newLink = link.cloneNode(true);
            link.parentNode.replaceChild(newLink, link);
            
            // Add the ripple effect only
            newLink.addEventListener('click', function(e) {
                addClickEffect(e);
                showToast('Navigating to: ' + newLink.textContent.trim());
                // Let the default navigation happen
            });
        });
        
        // Add click effect to entire document except nav links
        document.addEventListener('click', function(e) {
            // Don't handle nav links here, they're handled separately
            if (!e.target.classList.contains('nav-link') && !e.target.closest('.nav-link')) {
                addClickEffect(e);
            }
        });
        // Make ALL elements clickable - literally everything
        var allElements = document.querySelectorAll('*');
        
        // Process each element to make it interactive
        allElements.forEach(function(element) {
            // Skip the body and html elements
            if (element.tagName === 'BODY' || element.tagName === 'HTML' || element.tagName === 'SCRIPT') {
                return;
            }
            
            // Add cursor pointer to all elements
            element.style.cursor = 'pointer';
            
            // Add click event to everything
            element.addEventListener('click', function(e) {
                // Don't propagate clicks to parent elements
                e.stopPropagation();
                
                // Get element description
                var elementType = element.tagName.toLowerCase();
                var elementText = element.textContent.trim().substring(0, 30);
                if (elementText.length > 30) elementText += '...';
                
                // Define action based on element type
                var action = '';
                
                if (elementType === 'button' || element.classList.contains('button') || 
                    element.classList.contains('form-button') || element.getAttribute('style')?.includes('cursor: pointer')) {
                    action = 'Button clicked: ';
                    
                    // Add visual feedback
                    element.style.transform = 'scale(0.95)';
                    element.style.opacity = '0.9';
                    setTimeout(() => {
                        element.style.transform = '';
                        element.style.opacity = '';
                    }, 150);
                } 
                else if (elementType === 'a' || element.classList.contains('nav-link')) {
                    action = 'Link clicked: ';
                    
                    // Always allow navigation for links
                    showToast(action + elementText);
                    // Do not prevent default - let the links work
                    e.stopPropagation();
                    return;
                }
                else if (elementType === 'input' || elementType === 'select' || elementType === 'textarea') {
                    action = 'Form element interacted: ';
                    // Don't prevent default for form elements to allow them to be used
                    return;
                }
                else if (elementType === 'div' || elementType === 'span') {
                    if (elementText.length > 0) {
                        action = 'Selected: ';
                        
                        // Highlight effect for text elements
                        var originalBg = element.style.backgroundColor;
                        var originalColor = element.style.color;
                        element.style.backgroundColor = 'rgba(255,102,0,0.2)';
                        if (originalColor !== 'rgb(255, 255, 255)') {
                            element.style.color = '#FFF';
                        }
                        setTimeout(() => {
                            element.style.backgroundColor = originalBg;
                            element.style.color = originalColor;
                        }, 300);
                    } else {
                        action = 'Clicked element: ';
                    }
                }
                else {
                    action = elementType + ' clicked: ';
                }
                
                // Prevent default behavior for non-form elements
                if (elementType !== 'input' && elementType !== 'select' && elementType !== 'textarea') {
                    e.preventDefault();
                }
                
                // Show toast message with element info
                if (elementText.length > 0) {
                    showToast(action + elementText);
                } else {
                    showToast(action + elementType);
                }
            });
        });
        
        // Add change events to form elements
        var formElements = document.querySelectorAll('select, input, textarea');
        formElements.forEach(function(element) {
            element.addEventListener('change', function() {
                var elementName = this.name || this.id || this.placeholder || 'Input';
                showToast('Setting updated: ' + elementName);
            });
        });
        
        // Special handling for file inputs to show selected files
        var fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(function(input) {
            input.addEventListener('change', function() {
                if (this.files.length > 0) {
                    var fileNames = Array.from(this.files).map(f => f.name).join(', ');
                    showToast('Files selected: ' + fileNames);
                    
                    // Update any adjacent text that might show the filename
                    var parent = this.parentElement;
                    var fileText = parent.querySelector('span');
                    if (fileText) {
                        fileText.textContent = this.files.length > 1 ? 
                            this.files.length + ' files selected' : 
                            this.files[0].name;
                    }
                }
            });
        });
    };
    
    // Toast message function
    function showToast(message) {
        // Create toast container if it doesn't exist
        var toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 9999;';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast message
        var toast = document.createElement('div');
        toast.style.cssText = 'background-color: rgba(50, 50, 50, 0.9); color: white; padding: 10px 15px; ' +
                             'margin-top: 10px; border-radius: 4px; font-size: 14px; max-width: 300px; ' +
                             'box-shadow: 0 2px 10px rgba(0,0,0,0.3); opacity: 0; transition: opacity 0.3s;';
        toast.textContent = message;
        
        // Add to container and animate
        toastContainer.appendChild(toast);
        setTimeout(() => { toast.style.opacity = '1'; }, 10);
        
        // Remove after delay
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                toastContainer.removeChild(toast);
            }, 300);
        }, 3000);
    }
    </script>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-image: url('/static/progress_background.jpg');
            background-size: cover;
            background-position: center;
            color: white;
            margin: 0;
            padding: 0;
        }
        
        /* MAKE EVERY SINGLE ELEMENT INTERACTIVE */
        * {
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            position: relative;
        }
        
        *:hover {
            z-index: 1;
        }
        
        /* Enhanced feedback for absolutely all elements */
        *:hover:not(html):not(body):not(script):not(style):not(meta):not(head):not(link):not(title) {
            box-shadow: 0 0 0 2px rgba(255, 102, 0, 0.3) !important;
            filter: brightness(110%) !important;
        }
        
        *:active:not(html):not(body):not(script):not(style):not(meta):not(head):not(link):not(title) {
            transform: scale(0.98) !important;
            filter: brightness(90%) !important;
        }
        
        /* Special styling for interactive elements */
        button, .button, .form-button, .nav-link, .secondary-button, .status-button, .logs-button, 
        a, input[type="button"], input[type="submit"], input[type="reset"], [role="button"],
        [style*="cursor: pointer"] {
            transform-origin: center !important;
        }
        
        button:hover, .button:hover, .form-button:hover, .nav-link:hover, .secondary-button:hover, 
        .status-button:hover, .logs-button:hover, a:hover, input[type="button"]:hover, 
        input[type="submit"]:hover, input[type="reset"]:hover, [role="button"]:hover {
            filter: brightness(120%) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
        }
        
        button:active, .button:active, .form-button:active, .nav-link:active, .secondary-button:active,
        .status-button:active, .logs-button:active, a:active, input[type="button"]:active,
        input[type="submit"]:active, input[type="reset"]:active, [role="button"]:active {
            transform: translateY(1px) !important;
            filter: brightness(90%) !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3) !important;
        }
        
        /* Make text and generic elements give visual feedback */
        div:hover, span:hover, p:hover, h1:hover, h2:hover, h3:hover, h4:hover, h5:hover, h6:hover,
        label:hover, li:hover, td:hover, th:hover {
            background-color: rgba(255, 102, 0, 0.05) !important;
        }
        
        /* Containers and card-like elements */
        [style*="border-radius"], [style*="padding"], .app-container, .sidebar, .main-area, 
        .status-area, .logs-area, [style*="background-color"] {
            overflow: visible !important;
        }
        
        [style*="border-radius"]:hover, [style*="padding"]:hover, .app-container:hover, .sidebar:hover,
        .main-area:hover, .status-area:hover, .logs-area:hover, [style*="background-color"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1) !important;
        }
        
        /* Fixed navigation bar */
        .nav-bar {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background-color: #FF6600;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            z-index: 1000;
        }
        
        .nav-logo {
            height: 40px;
        }
        
        .nav-menu {
            display: flex;
            flex-wrap: wrap;
        }
        
        .nav-link {
            color: white;
            text-decoration: none;
            padding: 8px 15px;
            margin-left: 5px;
            background-color: #AA4400;
            border-radius: 3px;
            font-weight: bold;
            font-size: 14px;
        }
        
        .nav-link:hover {
            background-color: #CC5500;
        }
        
        .nav-link.active {
            background-color: #CC5500;
        }
        
        /* Main content container */
        .content-wrapper {
            padding-top: 70px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: calc(100vh - 70px);
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
        
        .app-content {
            flex: 1;
            overflow: auto;
        }
        
        .app-footer {
            padding: 8px 15px;
            background-color: #252525;
            border-top: 1px solid #444;
            font-size: 12px;
            color: #888;
            text-align: center;
        }
        
        /* Add all other shared styles here */
        .welcome-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 30px;
            text-align: center;
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
        
        /* Creator page specific styles */
        .app-content-creator {
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
            font-size: 16px;
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
        
        /* Dashboard styles */
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
    </style>
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
            </div>
            
            <div class="app-footer">
                © ProgressBets™ | TextNow v1.0.0 | 5 Accounts Active
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
                <div class="app-content-creator">
                    <div class="sidebar">
                        <div class="section-title">Account Creation Settings</div>
                        
                        <div class="form-group">
                            <label class="form-label">Number of Accounts</label>
                            <input type="number" class="form-input" value="100" min="1" max="10000">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Device Mode</label>
                            <select class="form-select">
                                <option selected>Production (BLU G44)</option>
                                <option>Demo (No Device)</option>
                                <option>Custom Emulator</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Creation Speed</label>
                            <select class="form-select">
                                <option>Conservative (Slow)</option>
                                <option selected>Balanced</option>
                                <option>Aggressive (Fast)</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Area Codes</label>
                            <input type="text" class="form-input" placeholder="Enter area codes separated by commas" value="954, 754, 305, 786, 561">
                            <div style="margin-top: 8px; font-size: 12px; color: #AAA;">Enter any area codes you want, separated by commas</div>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Area Code Presets</label>
                            <div style="display: flex; gap: 10px;">
                                <button class="secondary-button status-button">Florida</button>
                                <button class="secondary-button status-button">Georgia</button>
                                <button class="secondary-button status-button">New York</button>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Randomize Names</label>
                            <select class="form-select">
                                <option selected>Auto-generate random names</option>
                                <option>Use custom name list</option>
                                <option>Upload name list</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Voicemail Setup</label>
                            <select class="form-select">
                                <option selected>Auto-assign random voicemails</option>
                                <option>Use specific voicemail profile</option>
                                <option>No voicemail setup</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Upload Data Source (Optional)</label>
                            <input type="file" id="fileUpload" style="display: none;">
                            <button class="secondary-button" style="width: 100%; margin-bottom: 8px;" onclick="document.getElementById('fileUpload').click()">Choose File</button>
                            <div style="font-size: 12px; color: #AAA;">Supports CSV, TXT, XLSX, XLS</div>
                        </div>
                        
                        <button class="form-button" style="font-size: 22px; padding: 20px; margin-top: 25px; background-color: #FF6600; color: white; font-weight: bold; width: 100%; display: block; border-radius: 8px; border: none; cursor: pointer; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">START CREATION</button>
                    </div>
                    
                    <div class="main-area">
                        <div class="main-header">
                            <div class="main-title">Account Creator</div>
                            <div class="account-counter">Total Accounts: 10,563</div>
                        </div>
                        
                        <div class="status-area">
                            <div class="status-header">
                                <div class="status-title">Current Batch Status</div>
                                <div class="status-actions">
                                    <button class="status-button">Pause</button>
                                    <button class="status-button">Cancel</button>
                                </div>
                            </div>
                            
                            <div class="progress-container">
                                <div class="progress-bar"></div>
                            </div>
                            
                            <div class="progress-stats">
                                <div>Created: 35 / 100</div>
                                <div>Success Rate: 100%</div>
                                <div>Time Left: 32m 18s</div>
                            </div>
                        </div>
                        
                        <div class="logs-area">
                            <div class="logs-header">
                                <div class="logs-title">Process Log</div>
                                <div class="logs-actions">
                                    <button class="logs-button">Clear</button>
                                    <button class="logs-button">Export</button>
                                </div>
                            </div>
                            
                            <div class="logs-content">
                                <div class="log-entry">
                                    <span class="log-time">[14:45:32]</span> <span class="log-success">Account created: Sarah Johnson (786-123-4567)</span>
                                </div>
                                <div class="log-entry">
                                    <span class="log-time">[14:44:18]</span> <span class="log-success">Voicemail setup completed for: 786-123-4567</span>
                                </div>
                                <div class="log-entry">
                                    <span class="log-time">[14:43:55]</span> <span class="log-success">Account verified: 786-123-4567</span>
                                </div>
                                <div class="log-entry">
                                    <span class="log-time">[14:43:22]</span> <span class="log-success">Phone number assigned: 786-123-4567</span>
                                </div>
                                <div class="log-entry">
                                    <span class="log-time">[14:42:45]</span> <span class="log-success">Registration form submitted: sarah.johnson91@example.com</span>
                                </div>
                                <div class="log-entry">
                                    <span class="log-time">[14:42:10]</span> <span class="log-success">Device rotation: New fingerprint generated</span>
                                </div>
                                <div class="log-entry">
                                    <span class="log-time">[14:41:30]</span> <span class="log-success">Account created: Michael Wilson (954-987-6543)</span>
                                </div>
                                <div class="log-entry">
                                    <span class="log-time">[14:40:12]</span> <span class="log-success">Voicemail setup completed for: 954-987-6543</span>
                                </div>
                                <div class="log-entry">
                                    <span class="log-time">[14:39:48]</span> <span class="log-success">Account verified: 954-987-6543</span>
                                </div>
                                <div class="log-entry">
                                    <span class="log-time">[14:39:15]</span> <span class="log-success">Phone number assigned: 954-987-6543</span>
                                </div>
                                <div class="log-entry">
                                    <span class="log-time">[14:38:37]</span> <span class="log-success">Registration form submitted: michael.wilson84@example.com</span>
                                </div>
                                <div class="log-entry">
                                    <span class="log-time">[14:38:01]</span> <span class="log-success">Device rotation: New fingerprint generated</span>
                                </div>
                                <div class="log-entry">
                                    <span class="log-time">[14:37:28]</span> <span class="log-success">Account created: Jennifer Brown (305-456-7890)</span>
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
        '''
    )

@app.route('/dashboard')
def dashboard_page():
    """The account management dashboard page"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Dashboard",
        active_page="/dashboard",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; flex: 1; overflow: hidden;">
                    <div class="accounts-panel">
                        <div class="accounts-header">
                            Account Manager (5,219)
                        </div>
                        
                        <div class="accounts-search">
                            <input type="text" class="search-input" placeholder="Search by name or number...">
                        </div>
                        
                        <div class="account-filters">
                            <div class="filter-group">
                                <label class="filter-label">Status</label>
                                <select class="filter-select">
                                    <option>All Statuses</option>
                                    <option selected>Active</option>
                                    <option>Inactive</option>
                                    <option>Warning</option>
                                    <option>Blocked</option>
                                </select>
                            </div>
                            
                            <div class="filter-group">
                                <label class="filter-label">Area Code</label>
                                <select class="filter-select">
                                    <option>All Area Codes</option>
                                    <option selected>954 (Fort Lauderdale)</option>
                                    <option>754 (Fort Lauderdale)</option>
                                    <option>305 (Miami)</option>
                                    <option>786 (Miami)</option>
                                    <option>561 (West Palm Beach)</option>
                                </select>
                            </div>
                            
                            <div class="filter-group">
                                <label class="filter-label">Age</label>
                                <select class="filter-select">
                                    <option>Any Age</option>
                                    <option>Newest (< 7 days)</option>
                                    <option selected>< 30 days</option>
                                    <option>< 90 days</option>
                                    <option>> 90 days</option>
                                </select>
                            </div>
                            
                            <div class="filter-actions">
                                <button class="filter-button">Reset</button>
                                <button class="filter-button">Apply</button>
                            </div>
                        </div>
                        
                        <div class="accounts-list">
                            <div class="account-item active">
                                <div class="account-status status-active"></div>
                                <div>
                                    <div class="account-name">Sarah Johnson</div>
                                    <div class="account-phone">786-123-4567</div>
                                </div>
                            </div>
                            <div class="account-item">
                                <div class="account-status status-active"></div>
                                <div>
                                    <div class="account-name">Michael Wilson</div>
                                    <div class="account-phone">954-987-6543</div>
                                </div>
                            </div>
                            <div class="account-item">
                                <div class="account-status status-warning"></div>
                                <div>
                                    <div class="account-name">Jennifer Brown</div>
                                    <div class="account-phone">305-456-7890</div>
                                </div>
                            </div>
                            <div class="account-item">
                                <div class="account-status status-active"></div>
                                <div>
                                    <div class="account-name">Robert Davis</div>
                                    <div class="account-phone">754-789-0123</div>
                                </div>
                            </div>
                            <div class="account-item">
                                <div class="account-status status-inactive"></div>
                                <div>
                                    <div class="account-name">Emily Martinez</div>
                                    <div class="account-phone">561-234-5678</div>
                                </div>
                            </div>
                            <div class="account-item">
                                <div class="account-status status-active"></div>
                                <div>
                                    <div class="account-name">David Anderson</div>
                                    <div class="account-phone">305-876-5432</div>
                                </div>
                            </div>
                            <div class="account-item">
                                <div class="account-status status-active"></div>
                                <div>
                                    <div class="account-name">Jessica Taylor</div>
                                    <div class="account-phone">954-345-6789</div>
                                </div>
                            </div>
                            <div class="account-item">
                                <div class="account-status status-active"></div>
                                <div>
                                    <div class="account-name">Christopher White</div>
                                    <div class="account-phone">786-890-1234</div>
                                </div>
                            </div>
                            <div class="account-item">
                                <div class="account-status status-warning"></div>
                                <div>
                                    <div class="account-name">Amanda Harris</div>
                                    <div class="account-phone">754-567-8901</div>
                                </div>
                            </div>
                            <div class="account-item">
                                <div class="account-status status-active"></div>
                                <div>
                                    <div class="account-name">Matthew Clark</div>
                                    <div class="account-phone">561-678-9012</div>
                                </div>
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
                                        <div class="detail-title">Sarah Johnson</div>
                                        <div class="detail-phone">786-123-4567</div>
                                    </div>
                                    <div class="detail-actions">
                                        <button class="detail-button danger">Block</button>
                                        <button class="detail-button">Edit</button>
                                        <button class="detail-button primary">Message</button>
                                    </div>
                                </div>
                                
                                <div class="detail-grid">
                                    <div class="detail-section">
                                        <div class="section-header">Account Information</div>
                                        <div class="account-info">
                                            <div class="info-label">Email:</div>
                                            <div class="info-value">sarah.johnson91@example.com</div>
                                            
                                            <div class="info-label">Created:</div>
                                            <div class="info-value">April 15, 2024 (10 days ago)</div>
                                            
                                            <div class="info-label">Last Active:</div>
                                            <div class="info-value">April 25, 2024 (Today)</div>
                                            
                                            <div class="info-label">Status:</div>
                                            <div class="info-value">Active</div>
                                            
                                            <div class="info-label">Login Token:</div>
                                            <div class="info-value">✓ Valid</div>
                                            
                                            <div class="info-label">Device:</div>
                                            <div class="info-value">BLU G44 (#12)</div>
                                        </div>
                                    </div>
                                    
                                    <div class="detail-section">
                                        <div class="section-header">Account Health</div>
                                        <div class="health-info">
                                            <div class="health-label">Overall Health</div>
                                            <div class="health-bar-container">
                                                <div class="health-bar health-excellent" style="width: 95%;"></div>
                                            </div>
                                            <div class="health-value health-excellent">95%</div>
                                        </div>
                                        <div class="health-info">
                                            <div class="health-label">Message Reliability</div>
                                            <div class="health-bar-container">
                                                <div class="health-bar health-excellent" style="width: 98%;"></div>
                                            </div>
                                            <div class="health-value health-excellent">98%</div>
                                        </div>
                                        <div class="health-info">
                                            <div class="health-label">API Response</div>
                                            <div class="health-bar-container">
                                                <div class="health-bar health-excellent" style="width: 100%;"></div>
                                            </div>
                                            <div class="health-value health-excellent">100%</div>
                                        </div>
                                        <div class="health-info">
                                            <div class="health-label">Login Stability</div>
                                            <div class="health-bar-container">
                                                <div class="health-bar health-good" style="width: 90%;"></div>
                                            </div>
                                            <div class="health-value health-good">90%</div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="detail-section">
                                    <div class="section-header">Activity Statistics</div>
                                    <div class="stats-row">
                                        <div class="stat-box">
                                            <div class="stat-value">124</div>
                                            <div class="stat-label">Messages Sent</div>
                                        </div>
                                        <div class="stat-box">
                                            <div class="stat-value">37</div>
                                            <div class="stat-label">Replies Received</div>
                                        </div>
                                        <div class="stat-box">
                                            <div class="stat-value">8</div>
                                            <div class="stat-label">Campaigns</div>
                                        </div>
                                        <div class="stat-box">
                                            <div class="stat-value">3</div>
                                            <div class="stat-label">Current Campaigns</div>
                                        </div>
                                    </div>
                                    
                                    <div class="quick-send">
                                        <textarea class="form-input" style="height: 80px;" placeholder="Type a message to send..."></textarea>
                                        <button class="form-button" style="margin-top: 10px;">Send</button>
                                    </div>
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
                <div style="display: flex; flex: 1;">
                    <div style="width: 280px; background-color: #252525; border-right: 1px solid #444; padding: 20px; display: flex; flex-direction: column;">
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE; border-bottom: 1px solid #444; padding-bottom: 10px;">
                            Message Templates
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <button class="form-button" style="margin-bottom: 10px;">Create New Template</button>
                            <button class="form-button secondary-button">Import Templates</button>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <input type="text" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px; margin-bottom: 8px;" placeholder="Search templates...">
                            
                            <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">
                                <option>All Templates</option>
                                <option>Recently Used</option>
                                <option>By Category</option>
                            </select>
                        </div>
                        
                        <div style="flex: 1; overflow-y: auto; margin: -5px;">
                            <div style="padding: 10px; background-color: #333; margin: 5px; border-radius: 4px; cursor: pointer; border-left: 3px solid #FF6600;">
                                <div style="font-weight: bold; color: #EEE;">Spring Promotion Template #3</div>
                                <div style="font-size: 12px; color: #AAA;">Used in 4 campaigns</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer;">
                                <div style="font-weight: bold; color: #EEE;">Weekend Special Offer</div>
                                <div style="font-size: 12px; color: #AAA;">Used in 2 campaigns</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer;">
                                <div style="font-weight: bold; color: #EEE;">Sports Event Promotion</div>
                                <div style="font-size: 12px; color: #AAA;">Used in 1 campaign</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer;">
                                <div style="font-weight: bold; color: #EEE;">General Welcome Message</div>
                                <div style="font-size: 12px; color: #AAA;">Used in 7 campaigns</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer;">
                                <div style="font-weight: bold; color: #EEE;">Holiday Special</div>
                                <div style="font-size: 12px; color: #AAA;">Never used</div>
                            </div>
                        </div>
                    </div>
                    
                    <div style="flex: 1; padding: 20px; display: flex; flex-direction: column;">
                        <!-- Template Editor -->
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                            <div>
                                <input type="text" value="Spring Promotion Template #3" style="font-size: 20px; font-weight: bold; color: #EEE; background-color: transparent; border: 1px solid transparent; padding: 5px; border-radius: 4px; width: 400px;" onfocus="this.style.backgroundColor='#333'; this.style.borderColor='#555';" onblur="this.style.backgroundColor='transparent'; this.style.borderColor='transparent';">
                            </div>
                            <div>
                                <button style="padding: 8px 12px; background-color: #555; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Duplicate</button>
                                <button style="padding: 8px 12px; background-color: #FF6600; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Save</button>
                                <button style="padding: 8px 12px; background-color: #C33; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Delete</button>
                            </div>
                        </div>
                        
                        <div style="background-color: #252525; border-radius: 5px; padding: 20px; flex: 1; display: flex; flex-direction: column;">
                            <div style="margin-bottom: 20px;">
                                <label style="display: block; margin-bottom: 8px; color: #EEE; font-weight: bold;">Message Text</label>
                                <textarea style="width: 100%; height: 180px; padding: 12px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px; resize: vertical;">Hey {first_name}! Check out our special promotion at PB Betting. We've got boosted odds on all MLB games this weekend!

Get a 100% deposit match up to $1000 when you sign up using this link: {link}

Reply STOP to opt out.</textarea>
                            </div>
                            
                            <div style="margin-bottom: 20px;">
                                <label style="display: block; margin-bottom: 8px; color: #EEE; font-weight: bold;">Available Variables</label>
                                <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                                    <span style="background-color: #444; color: #EEE; padding: 5px 10px; border-radius: 4px; font-size: 12px; cursor: pointer;">{first_name}</span>
                                    <span style="background-color: #444; color: #EEE; padding: 5px 10px; border-radius: 4px; font-size: 12px; cursor: pointer;">{last_name}</span>
                                    <span style="background-color: #444; color: #EEE; padding: 5px 10px; border-radius: 4px; font-size: 12px; cursor: pointer;">{phone}</span>
                                    <span style="background-color: #444; color: #EEE; padding: 5px 10px; border-radius: 4px; font-size: 12px; cursor: pointer;">{link}</span>
                                    <span style="background-color: #444; color: #EEE; padding: 5px 10px; border-radius: 4px; font-size: 12px; cursor: pointer;">{date}</span>
                                    <span style="background-color: #444; color: #EEE; padding: 5px 10px; border-radius: 4px; font-size: 12px; cursor: pointer;">{custom_1}</span>
                                    <span style="background-color: #444; color: #EEE; padding: 5px 10px; border-radius: 4px; font-size: 12px; cursor: pointer;">{custom_2}</span>
                                    <span style="background-color: #FF6600; color: white; padding: 5px 10px; border-radius: 4px; font-size: 12px; cursor: pointer;">+ Add Custom</span>
                                </div>
                            </div>
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                                <div>
                                    <label style="display: block; margin-bottom: 8px; color: #EEE; font-weight: bold;">Category</label>
                                    <select style="width: 100%; padding: 10px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">
                                        <option>Promotions</option>
                                        <option>Welcome Messages</option>
                                        <option>Reminders</option>
                                        <option>Special Events</option>
                                        <option>Seasonal</option>
                                    </select>
                                </div>
                                
                                <div>
                                    <label style="display: block; margin-bottom: 8px; color: #EEE; font-weight: bold;">Recommended Images</label>
                                    <select style="width: 100%; padding: 10px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">
                                        <option>Spring Promo Image Set</option>
                                        <option>Sports Betting Image Set</option>
                                        <option>Generic Logo Set</option>
                                        <option>No Image Recommendation</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div style="background-color: #333; border-radius: 5px; padding: 15px; margin-bottom: 20px;">
                                <div style="font-weight: bold; color: #EEE; margin-bottom: 10px;">Message Preview</div>
                                <div style="background-color: #EEE; border-radius: 10px; padding: 15px; color: #333; position: relative; margin-left: 20px; max-width: 70%;">
                                    Hey John! Check out our special promotion at PB Betting. We've got boosted odds on all MLB games this weekend!<br><br>
                                    Get a 100% deposit match up to $1000 when you sign up using this link: https://pb.bet/promo<br><br>
                                    Reply STOP to opt out.
                                    <div style="position: absolute; left: -12px; top: 15px; width: 0; height: 0; border-top: 8px solid transparent; border-right: 12px solid #EEE; border-bottom: 8px solid transparent;"></div>
                                </div>
                            </div>
                            
                            <div style="margin-top: auto;">
                                <div style="display: flex; justify-content: space-between; padding-top: 15px; border-top: 1px solid #444;">
                                    <div style="font-size: 12px; color: #AAA;">
                                        Created: April 15, 2024 • Last Modified: April 22, 2024
                                    </div>
                                    <div>
                                        <button style="padding: 8px 16px; background-color: #FF6600; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">SAVE TEMPLATE</button>
                                    </div>
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
        '''
    )

@app.route('/campaigns')
def campaigns_page():
    """The campaigns management page"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Campaigns",
        active_page="/campaigns",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; flex: 1;">
                    <div style="width: 280px; background-color: #252525; border-right: 1px solid #444; padding: 20px;">
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE; border-bottom: 1px solid #444; padding-bottom: 10px;">
                            Campaign Management
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <button class="form-button" style="margin-bottom: 10px; font-weight: bold; background-color: #FF6600; color: white;">Create New Campaign</button>
                            <button class="form-button secondary-button">Import Campaign</button>
                        </div>
                        
                        <!-- Campaign Creation Modal - Would be hidden/shown with JavaScript in the actual app -->
                        <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.8); display: flex; justify-content: center; align-items: center; z-index: 1000;">
                            <div style="width: 600px; background-color: #252525; border-radius: 8px; box-shadow: 0 5px 20px rgba(0,0,0,0.5);">
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; border-bottom: 1px solid #444;">
                                    <div style="font-size: 18px; font-weight: bold; color: #EEE;">Create New Campaign</div>
                                    <button style="background: none; border: none; color: #AAA; font-size: 18px; cursor: pointer;">×</button>
                                </div>
                                
                                <div style="padding: 20px;">
                                    <div style="margin-bottom: 15px;">
                                        <label style="display: block; margin-bottom: 5px; color: #CCC;">Campaign Name</label>
                                        <input type="text" style="width: 100%; padding: 10px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;" placeholder="Enter campaign name" value="Spring Promotion 2024">
                                    </div>
                                    
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                                        <div>
                                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Start Date</label>
                                            <input type="text" style="width: 100%; padding: 10px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;" placeholder="MM/DD/YYYY" value="04/15/2024">
                                        </div>
                                        <div>
                                            <label style="display: block; margin-bottom: 5px; color: #CCC;">End Date</label>
                                            <input type="text" style="width: 100%; padding: 10px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;" placeholder="MM/DD/YYYY" value="04/30/2024">
                                        </div>
                                    </div>
                                    
                                    <!-- Sender Selection -->
                                    <div style="margin-bottom: 15px; border: 1px solid #555; padding: 15px; border-radius: 4px; background-color: #252525;">
                                        <label style="display: block; margin-bottom: 8px; color: #EEE; font-weight: bold;">Select Numbers to Send From</label>
                                        
                                        <div style="margin-bottom: 10px;">
                                            <select style="width: 100%; padding: 10px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px; margin-bottom: 10px;">
                                                <option value="all">All Available Numbers (10,563)</option>
                                                <option value="area_codes">Specific Area Codes</option>
                                                <option value="account_health">Best Performing Accounts Only (9,876)</option>
                                                <option value="age">Newest Accounts Only</option>
                                                <option value="custom_list">Custom Account List</option>
                                            </select>
                                        </div>
                                        
                                        <div style="margin-bottom: 10px;">
                                            <div style="margin-bottom: 5px; color: #CCC;">Select Area Codes</div>
                                            <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                                                <label style="background-color: #333; padding: 5px 10px; border-radius: 4px; cursor: pointer; display: flex; align-items: center; min-width: 80px;">
                                                    <input type="checkbox" style="margin-right: 5px;" checked> 954
                                                </label>
                                                <label style="background-color: #333; padding: 5px 10px; border-radius: 4px; cursor: pointer; display: flex; align-items: center; min-width: 80px;">
                                                    <input type="checkbox" style="margin-right: 5px;" checked> 754
                                                </label>
                                                <label style="background-color: #333; padding: 5px 10px; border-radius: 4px; cursor: pointer; display: flex; align-items: center; min-width: 80px;">
                                                    <input type="checkbox" style="margin-right: 5px;" checked> 305
                                                </label>
                                                <label style="background-color: #333; padding: 5px 10px; border-radius: 4px; cursor: pointer; display: flex; align-items: center; min-width: 80px;">
                                                    <input type="checkbox" style="margin-right: 5px;" checked> 786
                                                </label>
                                                <label style="background-color: #333; padding: 5px 10px; border-radius: 4px; cursor: pointer; display: flex; align-items: center; min-width: 80px;">
                                                    <input type="checkbox" style="margin-right: 5px;" checked> 561
                                                </label>
                                                <label style="background-color: #333; padding: 5px 10px; border-radius: 4px; cursor: pointer; display: flex; align-items: center; min-width: 80px;">
                                                    <input type="checkbox" style="margin-right: 5px;"> 239
                                                </label>
                                                <label style="background-color: #333; padding: 5px 10px; border-radius: 4px; cursor: pointer; display: flex; align-items: center; min-width: 80px;">
                                                    <input type="checkbox" style="margin-right: 5px;"> 407
                                                </label>
                                                <label style="background-color: #333; padding: 5px 10px; border-radius: 4px; cursor: pointer; display: flex; align-items: center; min-width: 80px;">
                                                    <input type="checkbox" style="margin-right: 5px;"> 321
                                                </label>
                                            </div>
                                        </div>
                                        
                                        <div style="margin-top: 8px;">
                                            <button style="padding: 5px 10px; background-color: #444; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">Upload Custom Account List</button>
                                            <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                                Selected: 5,478 numbers from Florida area codes
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div style="margin-bottom: 15px;">
                                        <label style="display: block; margin-bottom: 5px; color: #CCC;">Number of Accounts</label>
                                        <input type="number" style="width: 100%; padding: 10px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;" value="10000">
                                    </div>
                                    
                                    <!-- Target Number Upload Section -->
                                    <div style="margin-bottom: 15px; border: 1px solid #FF6600; padding: 15px; border-radius: 4px; background-color: rgba(255,102,0,0.1);">
                                        <label style="display: block; margin-bottom: 5px; color: #EEE; font-weight: bold;">Upload Target Numbers (Required)</label>
                                        <div style="margin-bottom: 10px; display: flex; align-items: center;">
                                            <input type="file" id="targetNumbersUpload" style="display: none;">
                                            <button style="flex: 1; padding: 10px; background-color: #FF6600; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;" onclick="document.getElementById('targetNumbersUpload').click()">Choose Target List</button>
                                            <span style="margin-left: 10px; color: #AAA; font-size: 12px;">No file chosen</span>
                                        </div>
                                        <div style="font-size: 12px; color: #EEE; margin-top: 8px;">
                                            Upload a CSV or TXT file with your target phone numbers. The system will use these numbers for message delivery.
                                        </div>
                                    </div>
                                    
                                    <!-- Message Template Section -->
                                    <div style="margin-bottom: 20px;">
                                        <label style="display: block; margin-bottom: 5px; color: #CCC;">Message Template</label>
                                        <select style="width: 100%; padding: 10px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px; margin-bottom: 10px;">
                                            <option selected>Spring Promotion Template #3</option>
                                            <option>Weekend Special Offer</option>
                                            <option>Sports Event Promotion</option>
                                            <option>General Welcome Message</option>
                                            <option>Custom Message</option>
                                        </select>
                                        
                                        <!-- Manual Message Input -->
                                        <div style="margin-top: 10px;">
                                            <label style="display: block; margin-bottom: 5px; color: #CCC;">Custom Message Text</label>
                                            <textarea style="width: 100%; height: 80px; padding: 10px; border-radius: 4px; border: 1px solid #555; background-color: #2A2A2A; color: #EEE; font-size: 14px; margin-bottom: 5px; resize: vertical;" placeholder="Enter your custom message text here...">Hey {first_name}! Check out our special offer at PB Betting. Sign up now using this link: {link}</textarea>
                                            <div style="font-size: 12px; color: #AAA;">
                                                Use {first_name}, {last_name}, {phone}, and {link} as placeholders that will be replaced automatically.
                                            </div>
                                        </div>
                                        
                                        <!-- Message Pool Upload Section -->
                                        <div style="margin-top: 15px; border: 1px dashed #555; padding: 15px; border-radius: 4px;">
                                            <label style="display: block; margin-bottom: 5px; color: #CCC; font-weight: bold;">Upload Message Pool (Optional)</label>
                                            <div style="margin-bottom: 10px; display: flex; align-items: center;">
                                                <input type="file" id="messagePoolUpload" style="display: none;" multiple>
                                                <button style="flex: 1; padding: 10px; background-color: #444; color: white; border: none; border-radius: 4px; cursor: pointer;" onclick="document.getElementById('messagePoolUpload').click()">Choose Files</button>
                                                <span style="margin-left: 10px; color: #AAA; font-size: 12px;">No files chosen</span>
                                            </div>
                                            <div style="font-size: 12px; color: #AAA;">
                                                Upload multiple TXT files containing message variations. Messages will be randomly selected from this pool to reduce pattern detection.
                                            </div>
                                        </div>
                                        
                                        <!-- Image Upload Section -->
                                        <div style="margin-top: 15px; border: 1px dashed #555; padding: 15px; border-radius: 4px;">
                                            <label style="display: block; margin-bottom: 5px; color: #CCC; font-weight: bold;">Upload Campaign Images</label>
                                            <div style="margin-bottom: 10px; display: flex; align-items: center;">
                                                <input type="file" id="campaignImageUpload" style="display: none;" multiple accept="image/*">
                                                <button style="flex: 1; padding: 10px; background-color: #444; color: white; border: none; border-radius: 4px; cursor: pointer;" onclick="document.getElementById('campaignImageUpload').click()">Choose Images</button>
                                                <span style="margin-left: 10px; color: #AAA; font-size: 12px;">No images chosen</span>
                                            </div>
                                            <div style="font-size: 12px; color: #AAA;">
                                                Upload multiple JPG, PNG or other image files at once. The system will randomly select from these images during message delivery to avoid pattern detection.
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 25px; padding-top: 20px; border-top: 1px solid #444;">
                                        <div style="display: flex; gap: 10px;">
                                            <select style="padding: 10px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">
                                                <option selected>8am - 8pm (Default)</option>
                                                <option>24 Hours</option>
                                                <option>9am - 5pm</option>
                                                <option>Custom Hours</option>
                                            </select>
                                        </div>
                                        <div style="display: flex; gap: 10px;">
                                            <button style="padding: 10px 15px; background-color: #444; color: white; border: none; border-radius: 4px; cursor: pointer;">Cancel</button>
                                            <button style="padding: 10px 20px; background-color: #FF6600; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 16px;">START CAMPAIGN</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #CCC; font-size: 14px;">Filter Campaigns</label>
                            <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px; margin-bottom: 10px;">
                                <option>All Campaigns</option>
                                <option selected>Active</option>
                                <option>Paused</option>
                                <option>Completed</option>
                                <option>Failed</option>
                            </select>
                            
                            <input type="text" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;" placeholder="Search campaigns...">
                        </div>
                        
                        <div style="font-size: 14px; font-weight: bold; margin-bottom: 10px; color: #CCC; padding-top: 10px;">
                            Active Campaigns
                        </div>
                        
                        <div style="max-height: 300px; overflow-y: auto;">
                            <div style="padding: 10px; background-color: #333; margin-bottom: 8px; border-radius: 4px; cursor: pointer; border-left: 3px solid #FF6600;">
                                <div style="font-weight: bold; margin-bottom: 3px;">Spring Promotion 2024</div>
                                <div style="font-size: 12px; color: #AAA;">10,000 accounts • 68% complete</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin-bottom: 8px; border-radius: 4px; cursor: pointer;">
                                <div style="font-weight: bold; margin-bottom: 3px;">Florida Weekend Special</div>
                                <div style="font-size: 12px; color: #AAA;">5,000 accounts • 37% complete</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin-bottom: 8px; border-radius: 4px; cursor: pointer;">
                                <div style="font-weight: bold; margin-bottom: 3px;">Miami Sports Event</div>
                                <div style="font-size: 12px; color: #AAA;">7,500 accounts • 24% complete</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin-bottom: 8px; border-radius: 4px; cursor: pointer;">
                                <div style="font-weight: bold; margin-bottom: 3px;">New Customer Acquisition</div>
                                <div style="font-size: 12px; color: #AAA;">8,200 accounts • 12% complete</div>
                            </div>
                        </div>
                    </div>
                    
                    <div style="flex: 1; padding: 20px; display: flex; flex-direction: column;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                            <div style="font-size: 20px; font-weight: bold; color: #EEE;">Spring Promotion 2024</div>
                            <div>
                                <button style="padding: 8px 12px; background-color: #555; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Edit</button>
                                <button style="padding: 8px 12px; background-color: #FF6600; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Pause</button>
                                <button style="padding: 8px 12px; background-color: #C33; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Stop</button>
                            </div>
                        </div>
                        
                        <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                            <div style="flex: 1; background-color: #333; border-radius: 5px; padding: 15px;">
                                <div style="font-size: 16px; font-weight: bold; color: #EEE; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px;">Campaign Status</div>
                                
                                <div style="margin-bottom: 15px;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                        <div style="color: #CCC;">Progress:</div>
                                        <div style="color: #EEE; font-weight: bold;">68% (6,823 / 10,000)</div>
                                    </div>
                                    <div style="width: 100%; height: 8px; background-color: #444; border-radius: 4px; overflow: hidden;">
                                        <div style="height: 100%; background-color: #FF6600; width: 68%;"></div>
                                    </div>
                                </div>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                    <div>
                                        <div style="color: #AAA; font-size: 12px;">Start Date</div>
                                        <div style="color: #EEE;">April 15, 2024</div>
                                    </div>
                                    <div>
                                        <div style="color: #AAA; font-size: 12px;">End Date</div>
                                        <div style="color: #EEE;">April 30, 2024</div>
                                    </div>
                                    <div>
                                        <div style="color: #AAA; font-size: 12px;">Messages Sent</div>
                                        <div style="color: #EEE;">68,230</div>
                                    </div>
                                    <div>
                                        <div style="color: #AAA; font-size: 12px;">Responses</div>
                                        <div style="color: #EEE;">5,467 (8.01%)</div>
                                    </div>
                                </div>
                            </div>
                            
                            <div style="flex: 1; background-color: #333; border-radius: 5px; padding: 15px;">
                                <div style="font-size: 16px; font-weight: bold; color: #EEE; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px;">Target Demographics</div>
                                
                                <div style="margin-bottom: 10px;">
                                    <div style="color: #AAA; font-size: 12px; margin-bottom: 3px;">Area Codes</div>
                                    <div style="color: #EEE; background-color: #252525; padding: 5px 8px; border-radius: 3px; font-size: 14px;">954, 754, 305, 786, 561 (Florida)</div>
                                </div>
                                
                                <div style="margin-bottom: 10px;">
                                    <div style="color: #AAA; font-size: 12px; margin-bottom: 3px;">Message Template</div>
                                    <div style="color: #EEE; background-color: #252525; padding: 5px 8px; border-radius: 3px; font-size: 14px;">Spring Promotion Template #3</div>
                                </div>
                                
                                <div style="margin-bottom: 10px;">
                                    <div style="color: #AAA; font-size: 12px; margin-bottom: 3px;">Schedule</div>
                                    <div style="color: #EEE; background-color: #252525; padding: 5px 8px; border-radius: 3px; font-size: 14px;">8:00 AM - 8:00 PM, Monday-Saturday</div>
                                </div>
                                
                                <div>
                                    <div style="color: #AAA; font-size: 12px; margin-bottom: 3px;">Image Variations</div>
                                    <div style="color: #EEE; background-color: #252525; padding: 5px 8px; border-radius: 3px; font-size: 14px;">8 variations enabled</div>
                                </div>
                            </div>
                        </div>
                        
                        <div style="background-color: #333; border-radius: 5px; padding: 15px; flex: 1; display: flex; flex-direction: column;">
                            <div style="font-size: 16px; font-weight: bold; color: #EEE; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                                <div>Recent Activity</div>
                                <button style="padding: 4px 8px; background-color: #444; color: white; border: none; border-radius: 3px; font-size: 12px; cursor: pointer;">Export</button>
                            </div>
                            
                            <div style="flex: 1; overflow-y: auto; font-family: monospace; font-size: 12px; color: #CCC; background-color: #1A1A1A; padding: 10px; border-radius: 3px;">
                                <div style="margin-bottom: 5px; padding-bottom: 5px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:32:18]</span> <span style="color: #5F5;">Sent 215 messages to area code 954</span>
                                </div>
                                <div style="margin-bottom: 5px; padding-bottom: 5px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:28:45]</span> <span style="color: #5F5;">Received 18 responses from batch #452</span>
                                </div>
                                <div style="margin-bottom: 5px; padding-bottom: 5px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:25:33]</span> <span style="color: #5F5;">Sent 187 messages to area code 305</span>
                                </div>
                                <div style="margin-bottom: 5px; padding-bottom: 5px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:22:17]</span> <span style="color: #FF5;">Throttling detected - adjusting send rate</span>
                                </div>
                                <div style="margin-bottom: 5px; padding-bottom: 5px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:20:05]</span> <span style="color: #5F5;">Sent 220 messages to area code 786</span>
                                </div>
                                <div style="margin-bottom: 5px; padding-bottom: 5px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:15:42]</span> <span style="color: #5F5;">Received 22 responses from batch #451</span>
                                </div>
                                <div style="margin-bottom: 5px; padding-bottom: 5px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:11:28]</span> <span style="color: #5F5;">Sent 195 messages to area code 754</span>
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
        '''
    )

@app.route('/manual_messaging')
def manual_messaging_page():
    """The manual messaging page where you can send messages from a list of numbers"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Manual Messaging",
        active_page="/manual_messaging",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; flex-direction: column; padding: 20px; flex: 1;">
                    <h1>Manual Messaging Page</h1>
                    <p>This page will allow sending messages manually from selected accounts.</p>
                </div>
            </div>
            
            <div class="app-footer">
                © ProgressBets™ | TextNow v1.0.0 | 5 Accounts Active
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
                <div style="display: flex; flex: 1; height: 100%;">
                    <div style="width: 280px; background-color: #252525; border-right: 1px solid #444; padding: 20px; display: flex; flex-direction: column;">
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE; border-bottom: 1px solid #444; padding-bottom: 10px;">
                            Message Monitor
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <input type="text" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px; margin-bottom: 8px;" placeholder="Search messages...">
                            
                            <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">
                                <option>All Messages</option>
                                <option selected>New Messages</option>
                                <option>Responded</option>
                                <option>Flagged</option>
                            </select>
                        </div>
                        
                        <div style="margin-bottom: 10px; display: flex; gap: 8px;">
                            <button style="flex: 1; padding: 6px; background-color: #FF6600; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">Auto-Reply</button>
                            <button style="flex: 1; padding: 6px; background-color: #555; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">Flag All</button>
                        </div>
                        
                        <div style="font-size: 14px; font-weight: bold; margin: 15px 0 10px; color: #CCC; padding-top: 5px; border-top: 1px solid #444;">
                            Incoming Messages
                        </div>
                        
                        <div style="flex: 1; overflow-y: auto; margin: -5px;">
                            <div style="padding: 10px; background-color: #333; margin: 5px; border-radius: 4px; cursor: pointer; border-left: 3px solid #FF6600;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">+1 (954) 555-1234</div>
                                    <div style="font-size: 12px; color: #AAA;">12:45 PM</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Hey, I saw your message about the...</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer; border-left: 3px solid #5F5;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">+1 (786) 555-7890</div>
                                    <div style="font-size: 12px; color: #AAA;">11:32 AM</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Thanks for the info. What time...</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">+1 (305) 555-4321</div>
                                    <div style="font-size: 12px; color: #AAA;">10:18 AM</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">I'm interested in learning more...</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">+1 (754) 555-9876</div>
                                    <div style="font-size: 12px; color: #AAA;">09:55 AM</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Where can I find more details...</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">+1 (561) 555-6543</div>
                                    <div style="font-size: 12px; color: #AAA;">09:22 AM</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">This sounds great! How do I...</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer; border-left: 3px solid #5F5;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">+1 (954) 555-8765</div>
                                    <div style="font-size: 12px; color: #AAA;">Yesterday</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">I can't wait for the event. Will...</div>
                            </div>
                        </div>
                    </div>
                    
                    <div style="flex: 1; display: flex; flex-direction: column; background-color: #1A1A1A;">
                        <div style="padding: 15px; background-color: #252525; border-bottom: 1px solid #444; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-weight: bold; color: #EEE;">+1 (954) 555-1234</div>
                                <div style="font-size: 12px; color: #AAA;">Michael Thompson • Online 5m ago</div>
                            </div>
                            <div>
                                <button style="padding: 6px 10px; background-color: #444; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; margin-left: 8px;">Blacklist</button>
                                <button style="padding: 6px 10px; background-color: #5F5; color: black; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; margin-left: 8px;">Auto-Reply</button>
                                <button style="padding: 6px 10px; background-color: #FF6600; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; margin-left: 8px;">Flag</button>
                            </div>
                        </div>
                        
                        <div style="flex: 1; padding: 15px; overflow-y: auto;">
                            <div style="margin-bottom: 20px;">
                                <div style="font-size: 12px; color: #AAA; margin-bottom: 5px; text-align: center;">Today, 10:30 AM</div>
                                
                                <div style="max-width: 75%; background-color: #333; padding: 10px 15px; border-radius: 15px; margin-left: auto; margin-bottom: 10px; color: #EEE;">
                                    <div style="font-size: 14px; margin-bottom: 5px;">Hey there! 👋 Ready for the biggest sports weekend? We've got exclusive offers waiting for you at PB Betting!</div>
                                    <div style="font-size: 12px; color: #AAA; text-align: right;">10:30 AM • Sent from (954) 678-9012</div>
                                </div>
                                
                                <div style="max-width: 75%; background-color: #283850; padding: 10px 15px; border-radius: 15px; margin-bottom: 10px; color: #EEE;">
                                    <div style="font-size: 14px; margin-bottom: 5px;">Hey, I saw your message about the sports weekend. What kind of offers are you talking about?</div>
                                    <div style="font-size: 12px; color: #AAA;">12:45 PM</div>
                                </div>
                            </div>
                            
                            <div style="font-size: 12px; color: #AAA; margin: 15px 0; text-align: center; border-bottom: 1px solid #333; line-height: 0.1em;"><span style="background-color: #1A1A1A; padding: 0 10px;">Account Info</span></div>
                            
                            <div style="background-color: #252525; border-radius: 5px; padding: 15px; margin-bottom: 15px;">
                                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; font-size: 13px;">
                                    <div>
                                        <div style="color: #AAA; margin-bottom: 3px;">Name</div>
                                        <div style="color: #EEE;">Michael Thompson</div>
                                    </div>
                                    <div>
                                        <div style="color: #AAA; margin-bottom: 3px;">TextNow Number</div>
                                        <div style="color: #EEE;">(954) 678-9012</div>
                                    </div>
                                    <div>
                                        <div style="color: #AAA; margin-bottom: 3px;">Location</div>
                                        <div style="color: #EEE;">Fort Lauderdale, FL</div>
                                    </div>
                                    <div>
                                        <div style="color: #AAA; margin-bottom: 3px;">Created</div>
                                        <div style="color: #EEE;">April 12, 2024</div>
                                    </div>
                                    <div>
                                        <div style="color: #AAA; margin-bottom: 3px;">Messages Sent</div>
                                        <div style="color: #EEE;">128</div>
                                    </div>
                                    <div>
                                        <div style="color: #AAA; margin-bottom: 3px;">Response Rate</div>
                                        <div style="color: #EEE;">8.5%</div>
                                    </div>
                                </div>
                            </div>
                            
                            <div style="font-size: 12px; color: #AAA; margin: 15px 0; text-align: center; border-bottom: 1px solid #333; line-height: 0.1em;"><span style="background-color: #1A1A1A; padding: 0 10px;">Opt-Out Management</span></div>
                            
                            <div style="background-color: #252525; border-radius: 5px; padding: 15px; margin-bottom: 15px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <div style="font-weight: bold; color: #EEE;">Opt-Out Status</div>
                                    <div style="display: flex; gap: 10px;">
                                        <button style="padding: 5px 10px; background-color: #444; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">Add Manually</button>
                                        <button style="padding: 5px 10px; background-color: #444; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">View Full List</button>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                        <div style="font-weight: bold; color: #EEE;">Auto-Detection</div>
                                        <div style="color: #5F5;">ENABLED</div>
                                    </div>
                                    <div style="font-size: 12px; color: #CCC;">System automatically detects opt-out messages like "STOP", "UNSUBSCRIBE", etc.</div>
                                </div>
                                
                                <div style="background-color: #333; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                        <div style="font-weight: bold; color: #EEE;">Current Number Status</div>
                                        <div style="color: #5F5;">NOT OPTED OUT</div>
                                    </div>
                                    <div style="font-size: 12px; color: #CCC;">This number (954) 555-1234 is not on the opt-out list.</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 10px; border-radius: 5px; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Opt-Out Keywords</div>
                                    <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                                        <div style="background-color: #333; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px;">STOP</div>
                                        <div style="background-color: #333; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px;">UNSUBSCRIBE</div>
                                        <div style="background-color: #333; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px;">CANCEL</div>
                                        <div style="background-color: #333; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px;">END</div>
                                        <div style="background-color: #333; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px;">QUIT</div>
                                        <div style="background-color: #333; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px;">+</div>
                                    </div>
                                </div>
                                
                                <div style="font-size: 12px; color: #AAA; margin-top: 10px;">Total opt-out list size: 3,842 numbers</div>
                            </div>
                        </div>
                        
                        <div style="padding: 15px; background-color: #252525; border-top: 1px solid #444;">
                            <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                                <button style="padding: 8px 12px; background-color: #333; color: #CCC; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">Template 1</button>
                                <button style="padding: 8px 12px; background-color: #333; color: #CCC; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">Template 2</button>
                                <button style="padding: 8px 12px; background-color: #333; color: #CCC; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">Template 3</button>
                                <button style="padding: 8px 12px; background-color: #333; color: #CCC; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">Images</button>
                            </div>
                            
                            <div style="display: flex; gap: 10px;">
                                <textarea style="flex: 1; padding: 10px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px; height: 80px; resize: none;" placeholder="Type your message here...">We've got 100% deposit match up to $500 for new users this weekend! Plus free bets on all major games. Want me to send you the signup link?</textarea>
                                
                                <div style="display: flex; flex-direction: column; justify-content: flex-end;">
                                    <button style="padding: 10px 15px; background-color: #FF6600; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold;">Send</button>
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
                <div style="display: flex; flex: 1;">
                    <div style="width: 280px; background-color: #252525; border-right: 1px solid #444; padding: 20px; display: flex; flex-direction: column;">
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE; border-bottom: 1px solid #444; padding-bottom: 10px;">
                            Image Library
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <button class="form-button" style="margin-bottom: 10px;">Import Images</button>
                            <button class="form-button secondary-button">Create Variation</button>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <input type="text" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px; margin-bottom: 8px;" placeholder="Search images...">
                            
                            <div style="display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 10px;">
                                <div style="background-color: #333; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px; cursor: pointer;">Sports</div>
                                <div style="background-color: #333; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px; cursor: pointer;">Betting</div>
                                <div style="background-color: #FF6600; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; cursor: pointer;">Promo</div>
                                <div style="background-color: #333; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px; cursor: pointer;">Events</div>
                            </div>
                        </div>
                        
                        <div style="flex: 1; overflow-y: auto; margin: -5px;">
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                <div style="background-color: #333; padding: 5px; border-radius: 4px; cursor: pointer; border: 2px solid #FF6600;">
                                    <div style="background-color: #2A2A2A; width: 100%; height: 80px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 10px;">PROMO-1.jpg</div>
                                    <div style="font-size: 10px; color: #CCC; padding: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Spring Promo</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 5px; border-radius: 4px; cursor: pointer;">
                                    <div style="background-color: #222; width: 100%; height: 80px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 10px;">PROMO-2.jpg</div>
                                    <div style="font-size: 10px; color: #CCC; padding: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Weekend Bonus</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 5px; border-radius: 4px; cursor: pointer;">
                                    <div style="background-color: #222; width: 100%; height: 80px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 10px;">EVENT-1.jpg</div>
                                    <div style="font-size: 10px; color: #CCC; padding: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">NBA Finals</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 5px; border-radius: 4px; cursor: pointer;">
                                    <div style="background-color: #222; width: 100%; height: 80px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 10px;">EVENT-2.jpg</div>
                                    <div style="font-size: 10px; color: #CCC; padding: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">MLB Season</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 5px; border-radius: 4px; cursor: pointer;">
                                    <div style="background-color: #222; width: 100%; height: 80px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 10px;">PROMO-3.jpg</div>
                                    <div style="font-size: 10px; color: #CCC; padding: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Welcome Bonus</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 5px; border-radius: 4px; cursor: pointer;">
                                    <div style="background-color: #222; width: 100%; height: 80px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 10px;">SPORTS-1.jpg</div>
                                    <div style="font-size: 10px; color: #CCC; padding: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Football Odds</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 5px; border-radius: 4px; cursor: pointer;">
                                    <div style="background-color: #222; width: 100%; height: 80px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 10px;">SPORTS-2.jpg</div>
                                    <div style="font-size: 10px; color: #CCC; padding: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Basketball Parlay</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 5px; border-radius: 4px; cursor: pointer;">
                                    <div style="background-color: #222; width: 100%; height: 80px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 10px;">BETTING-1.jpg</div>
                                    <div style="font-size: 10px; color: #CCC; padding: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Prop Bets</div>
                                </div>
                            </div>
                        </div>
                        
                        <div style="margin-top: 15px; font-size: 12px; color: #AAA; border-top: 1px solid #444; padding-top: 10px;">
                            Total Images: 32 • Variations: 128
                        </div>
                    </div>
                    
                    <div style="flex: 1; display: flex; flex-direction: column; padding: 20px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                            <div style="font-size: 20px; font-weight: bold; color: #EEE;">Spring Promotion Image</div>
                            <div>
                                <button style="padding: 8px 12px; background-color: #555; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Edit</button>
                                <button style="padding: 8px 12px; background-color: #5F5; color: black; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Generate Variation</button>
                                <button style="padding: 8px 12px; background-color: #FF6600; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Use in Campaign</button>
                            </div>
                        </div>
                        
                        <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                            <div style="flex: 2; background-color: #252525; border-radius: 5px; padding: 20px; display: flex; flex-direction: column; min-height: 300px;">
                                <div style="font-size: 16px; font-weight: bold; color: #EEE; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px;">
                                    Image Preview
                                </div>
                                
                                <div style="flex: 1; background-color: #333; display: flex; align-items: center; justify-content: center; color: #AAA; border-radius: 5px;">
                                    PROMO-1.jpg<br>(Preview would be displayed here)
                                </div>
                            </div>
                            
                            <div style="flex: 1; background-color: #252525; border-radius: 5px; padding: 20px;">
                                <div style="font-size: 16px; font-weight: bold; color: #EEE; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px;">
                                    Image Properties
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <div style="color: #AAA; font-size: 12px; margin-bottom: 3px;">Filename</div>
                                    <div style="color: #EEE; background-color: #333; padding: 5px 8px; border-radius: 3px; font-size: 14px;">PROMO-1.jpg</div>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <div style="color: #AAA; font-size: 12px; margin-bottom: 3px;">Size</div>
                                    <div style="color: #EEE; background-color: #333; padding: 5px 8px; border-radius: 3px; font-size: 14px;">1200 x 630 pixels (156 KB)</div>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <div style="color: #AAA; font-size: 12px; margin-bottom: 3px;">Category</div>
                                    <div style="color: #EEE; background-color: #333; padding: 5px 8px; border-radius: 3px; font-size: 14px;">Promo</div>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <div style="color: #AAA; font-size: 12px; margin-bottom: 3px;">Created</div>
                                    <div style="color: #EEE; background-color: #333; padding: 5px 8px; border-radius: 3px; font-size: 14px;">April 15, 2024</div>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <div style="color: #AAA; font-size: 12px; margin-bottom: 3px;">Usage Count</div>
                                    <div style="color: #EEE; background-color: #333; padding: 5px 8px; border-radius: 3px; font-size: 14px;">1,245 messages</div>
                                </div>
                                
                                <div>
                                    <div style="color: #AAA; font-size: 12px; margin-bottom: 3px;">Tags</div>
                                    <div style="display: flex; flex-wrap: wrap; gap: 5px; background-color: #333; padding: 5px 8px; border-radius: 3px;">
                                        <div style="background-color: #444; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px;">spring</div>
                                        <div style="background-color: #444; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px;">promo</div>
                                        <div style="background-color: #444; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px;">sports</div>
                                        <div style="background-color: #444; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px;">betting</div>
                                        <div style="background-color: #444; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px;">offer</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div style="background-color: #252525; border-radius: 5px; padding: 20px;">
                            <div style="font-size: 16px; font-weight: bold; color: #EEE; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                                <div>Image Variations (8)</div>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <label style="color: #CCC; font-size: 12px; font-weight: normal;">Number of variations:</label>
                                    <input type="number" style="width: 60px; padding: 5px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;" value="8" min="1" max="100">
                                    <button style="padding: 8px 15px; background-color: #FF6600; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: bold;">START</button>
                                </div>
                            </div>
                            
                            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">
                                <div style="background-color: #333; padding: 5px; border-radius: 4px; cursor: pointer; border: 2px solid #FF6600;">
                                    <div style="background-color: #2A2A2A; width: 100%; height: 100px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 12px;">Variation 1</div>
                                    <div style="font-size: 12px; color: #CCC; padding: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: center;">Original</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 5px; border-radius: 4px; cursor: pointer;">
                                    <div style="background-color: #222; width: 100%; height: 100px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 12px;">Variation 2</div>
                                    <div style="font-size: 12px; color: #CCC; padding: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: center;">Color Shift</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 5px; border-radius: 4px; cursor: pointer;">
                                    <div style="background-color: #222; width: 100%; height: 100px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 12px;">Variation 3</div>
                                    <div style="font-size: 12px; color: #CCC; padding: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: center;">Text Layout</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 5px; border-radius: 4px; cursor: pointer;">
                                    <div style="background-color: #222; width: 100%; height: 100px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 12px;">Variation 4</div>
                                    <div style="font-size: 12px; color: #CCC; padding: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: center;">Background</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 5px; border-radius: 4px; cursor: pointer;">
                                    <div style="background-color: #222; width: 100%; height: 100px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 12px;">Variation 5</div>
                                    <div style="font-size: 12px; color: #CCC; padding: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: center;">Font Change</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 5px; border-radius: 4px; cursor: pointer;">
                                    <div style="background-color: #222; width: 100%; height: 100px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 12px;">Variation 6</div>
                                    <div style="font-size: 12px; color: #CCC; padding: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: center;">Logo Position</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 5px; border-radius: 4px; cursor: pointer;">
                                    <div style="background-color: #222; width: 100%; height: 100px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 12px;">Variation 7</div>
                                    <div style="font-size: 12px; color: #CCC; padding: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: center;">Border Style</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 5px; border-radius: 4px; cursor: pointer;">
                                    <div style="background-color: #222; width: 100%; height: 100px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 12px;">Variation 8</div>
                                    <div style="font-size: 12px; color: #CCC; padding: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: center;">Composition</div>
                                </div>
                            </div>
                            
                            <div style="margin-top: 20px; padding: 15px; background-color: #2A2A2A; border-radius: 5px; border: 1px dashed #555;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <div style="font-weight: bold; color: #EEE;">Batch Image Upload</div>
                                    <div style="position: relative; overflow: hidden;">
                                        <button style="padding: 8px 12px; background-color: #FF6600; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: bold;">Choose Multiple Images</button>
                                        <input type="file" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;" multiple accept="image/*">
                                    </div>
                                </div>
                                <div style="font-size: 12px; color: #AAA; text-align: left;">
                                    Upload multiple images at once. The system will randomly select from your batch during message sending to avoid pattern detection while maintaining consistent message impact.
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
                <div style="display: flex; flex: 1;">
                    <div style="width: 280px; background-color: #252525; border-right: 1px solid #444; padding: 20px; display: flex; flex-direction: column;">
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE; border-bottom: 1px solid #444; padding-bottom: 10px;">
                            Account Health
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <button class="form-button" style="margin-bottom: 10px;">Run Health Check</button>
                            <button class="form-button secondary-button">Export Report</button>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <input type="text" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px; margin-bottom: 8px;" placeholder="Search accounts...">
                            
                            <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">
                                <option>All Accounts</option>
                                <option selected>Flagged Accounts</option>
                                <option>Healthy Accounts</option>
                                <option>Monitoring Accounts</option>
                            </select>
                        </div>
                        
                        <div style="font-size: 14px; font-weight: bold; margin: 15px 0 10px; color: #CCC; padding-top: 5px; border-top: 1px solid #444;">
                            Flagged Accounts
                        </div>
                        
                        <div style="flex: 1; overflow-y: auto; margin: -5px;">
                            <div style="padding: 10px; background-color: #333; margin: 5px; border-radius: 4px; cursor: pointer; border-left: 3px solid #F55;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">(954) 555-8765</div>
                                    <div style="font-size: 12px; color: #F55;">Critical</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">No response from account for 48 hours</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer; border-left: 3px solid #F55;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">(305) 555-4321</div>
                                    <div style="font-size: 12px; color: #F55;">Critical</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">Message delivery failure rate: 87%</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer; border-left: 3px solid #FA3;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">(786) 555-7890</div>
                                    <div style="font-size: 12px; color: #FA3;">Warning</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">Increasing delivery delay: 15+ minutes</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer; border-left: 3px solid #FA3;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">(561) 555-6543</div>
                                    <div style="font-size: 12px; color: #FA3;">Warning</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">Login failures: 3 consecutive attempts</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer; border-left: 3px solid #55F;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">(754) 555-9876</div>
                                    <div style="font-size: 12px; color: #55F;">Monitoring</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">High captcha challenge rate: 40%</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer; border-left: 3px solid #55F;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">(954) 555-1234</div>
                                    <div style="font-size: 12px; color: #55F;">Monitoring</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">Decreasing message delivery rate: 72%</div>
                            </div>
                        </div>
                        
                        <div style="margin-top: 15px; font-size: 12px; color: #AAA; border-top: 1px solid #444; padding-top: 10px;">
                            Last scan: 34 minutes ago • Auto-replace enabled
                        </div>
                    </div>
                    
                    <div style="flex: 1; display: flex; flex-direction: column; padding: 20px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                            <div style="font-size: 20px; font-weight: bold; color: #EEE;">Account Health Report</div>
                            <div>
                                <button style="padding: 8px 12px; background-color: #555; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">View Details</button>
                                <button style="padding: 8px 12px; background-color: #FF6600; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Auto-Replace</button>
                                <button style="padding: 8px 12px; background-color: #C33; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Blacklist</button>
                            </div>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                            <div style="background-color: #252525; border-radius: 5px; padding: 20px;">
                                <div style="font-size: 16px; font-weight: bold; color: #EEE; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px;">
                                    System Health Overview
                                </div>
                                
                                <div style="display: flex; flex-direction: column; gap: 15px;">
                                    <div>
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                            <div style="color: #CCC;">Overall System Health:</div>
                                            <div style="color: #5F5; font-weight: bold;">GOOD (96%)</div>
                                        </div>
                                        <div style="width: 100%; height: 8px; background-color: #444; border-radius: 4px; overflow: hidden;">
                                            <div style="height: 100%; background-color: #5F5; width: 96%;"></div>
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                            <div style="color: #CCC;">Active Accounts:</div>
                                            <div style="color: #EEE; font-weight: bold;">9,876 / 10,563 (93.5%)</div>
                                        </div>
                                        <div style="width: 100%; height: 8px; background-color: #444; border-radius: 4px; overflow: hidden;">
                                            <div style="height: 100%; background-color: #5F5; width: 93.5%;"></div>
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                            <div style="color: #CCC;">Average Message Delivery Rate:</div>
                                            <div style="color: #EEE; font-weight: bold;">98.3%</div>
                                        </div>
                                        <div style="width: 100%; height: 8px; background-color: #444; border-radius: 4px; overflow: hidden;">
                                            <div style="height: 100%; background-color: #5F5; width: 98.3%;"></div>
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                            <div style="color: #CCC;">Account Replacement Rate (7 days):</div>
                                            <div style="color: #EEE; font-weight: bold;">127 accounts (1.2%)</div>
                                        </div>
                                        <div style="width: 100%; height: 8px; background-color: #444; border-radius: 4px; overflow: hidden;">
                                            <div style="height: 100%; background-color: #5F5; width: 98.8%;"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div style="background-color: #252525; border-radius: 5px; padding: 20px;">
                                <div style="font-size: 16px; font-weight: bold; color: #EEE; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px;">
                                    Selected Account: (954) 555-8765
                                </div>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 13px;">
                                    <div>
                                        <div style="color: #AAA; margin-bottom: 3px;">Account Name</div>
                                        <div style="color: #EEE;">Jennifer Wilson</div>
                                    </div>
                                    <div>
                                        <div style="color: #AAA; margin-bottom: 3px;">Status</div>
                                        <div style="color: #F55;">CRITICAL</div>
                                    </div>
                                    <div>
                                        <div style="color: #AAA; margin-bottom: 3px;">Created</div>
                                        <div style="color: #EEE;">March 17, 2024 (39 days ago)</div>
                                    </div>
                                    <div>
                                        <div style="color: #AAA; margin-bottom: 3px;">Last Active</div>
                                        <div style="color: #EEE;">April 23, 2024 (2 days ago)</div>
                                    </div>
                                    <div>
                                        <div style="color: #AAA; margin-bottom: 3px;">Health Score</div>
                                        <div style="color: #F55;">12/100</div>
                                    </div>
                                    <div>
                                        <div style="color: #AAA; margin-bottom: 3px;">Messages Sent</div>
                                        <div style="color: #EEE;">1,452</div>
                                    </div>
                                </div>
                                
                                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #444;">
                                    <div style="color: #AAA; margin-bottom: 8px; font-size: 14px;">Critical Issues:</div>
                                    <div style="background-color: #332222; padding: 10px; border-radius: 5px; margin-bottom: 8px; border-left: 3px solid #F55; font-size: 13px; color: #EEE;">
                                        No response from TextNow servers for 48+ hours
                                    </div>
                                    <div style="background-color: #332222; padding: 10px; border-radius: 5px; margin-bottom: 8px; border-left: 3px solid #F55; font-size: 13px; color: #EEE;">
                                        API communication timeout on last 12 attempts
                                    </div>
                                    <div style="background-color: #332222; padding: 10px; border-radius: 5px; border-left: 3px solid #F55; font-size: 13px; color: #EEE;">
                                        Session token validation failed
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div style="background-color: #252525; border-radius: 5px; padding: 20px; flex: 1; display: flex; flex-direction: column;">
                            <div style="font-size: 16px; font-weight: bold; color: #EEE; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px; display: flex; justify-content: space-between;">
                                <div>Health Check Log</div>
                                <div style="font-size: 12px; color: #AAA;">Most recent checks shown first</div>
                            </div>
                            
                            <div style="flex: 1; overflow-y: auto; font-family: monospace; font-size: 12px; color: #CCC; background-color: #1A1A1A; padding: 10px; border-radius: 3px;">
                                <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:15:42]</span> <span style="color: #F55;">CRITICAL</span> <span style="color: #CCC;">(954) 555-8765 - API communication timeout. Session appears to be invalid.</span>
                                </div>
                                <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:15:41]</span> <span style="color: #FA3;">WARNING</span> <span style="color: #CCC;">(786) 555-7890 - Message delivery delay increased to 15.3 minutes.</span>
                                </div>
                                <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:15:38]</span> <span style="color: #5F5;">SUCCESS</span> <span style="color: #CCC;">(305) 789-1234 - All health checks passed. Score: 98/100.</span>
                                </div>
                                <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:15:36]</span> <span style="color: #5F5;">SUCCESS</span> <span style="color: #CCC;">(954) 123-4567 - All health checks passed. Score: 95/100.</span>
                                </div>
                                <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:15:32]</span> <span style="color: #5F5;">SUCCESS</span> <span style="color: #CCC;">(561) 234-5678 - All health checks passed. Score: 97/100.</span>
                                </div>
                                <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:15:28]</span> <span style="color: #F55;">CRITICAL</span> <span style="color: #CCC;">(305) 555-4321 - Message delivery failed. System reports flagged as spam.</span>
                                </div>
                                <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:15:25]</span> <span style="color: #55F;">INFO</span> <span style="color: #CCC;">(754) 555-9876 - CAPTCHA challenge detected and flagged for monitoring.</span>
                                </div>
                                <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:15:22]</span> <span style="color: #5F5;">SUCCESS</span> <span style="color: #CCC;">(786) 345-6789 - All health checks passed. Score: 99/100.</span>
                                </div>
                                <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:15:19]</span> <span style="color: #FA3;">WARNING</span> <span style="color: #CCC;">(561) 555-6543 - Login attempt failed. Will retry.</span>
                                </div>
                                <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #333;">
                                    <span style="color: #888;">[14:15:16]</span> <span style="color: #55F;">INFO</span> <span style="color: #CCC;">(954) 555-1234 - Message delivery rate decreasing. Adding to monitoring list.</span>
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
                <div style="display: flex; flex: 1;">
                    <div style="width: 280px; background-color: #252525; border-right: 1px solid #444; padding: 20px; display: flex; flex-direction: column;">
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE; border-bottom: 1px solid #444; padding-bottom: 10px;">
                            Voicemail Library
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <button class="form-button" style="margin-bottom: 10px; position: relative; overflow: hidden;">
                                Import Voicemails (Bulk)
                                <input type="file" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;" multiple accept=".mp3,.wav">
                            </button>
                            <button class="form-button secondary-button">Record New</button>
                        </div>
                        
                        <div style="margin-bottom: 15px; padding: 10px; background-color: #333; border-radius: 4px;">
                            <div style="font-weight: bold; color: #EEE; margin-bottom: 8px;">Batch Assignment</div>
                            <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #2A2A2A; color: #EEE; font-size: 14px; margin-bottom: 10px;">
                                <option selected>Change All Account Voicemails</option>
                                <option>Assign to Selected Accounts</option>
                                <option>Randomly Rotate Across Accounts</option>
                                <option>Reset to Default Voicemails</option>
                            </select>
                            <button class="form-button" style="width: 100%; background-color: #FF6600; color: white; font-weight: bold;">START</button>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <input type="text" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px; margin-bottom: 8px;" placeholder="Search voicemails...">
                            
                            <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">
                                <option>All Voicemails</option>
                                <option selected>Male Voice</option>
                                <option>Female Voice</option>
                                <option>Custom Recordings</option>
                                <option>Generated</option>
                            </select>
                        </div>
                        
                        <div style="font-size: 14px; font-weight: bold; margin: 15px 0 10px; color: #CCC; padding-top: 5px; border-top: 1px solid #444;">
                            Voicemail List
                        </div>
                        
                        <div style="flex: 1; overflow-y: auto; margin: -5px;">
                            <div style="padding: 10px; background-color: #333; margin: 5px; border-radius: 4px; cursor: pointer; border-left: 3px solid #FF6600;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">Standard Greeting 1</div>
                                    <div style="font-size: 12px; color: #AAA;">0:22</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">Male voice • Used 527 times</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">Standard Greeting 2</div>
                                    <div style="font-size: 12px; color: #AAA;">0:19</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">Female voice • Used 342 times</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">Business Greeting</div>
                                    <div style="font-size: 12px; color: #AAA;">0:25</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">Male voice • Used 198 times</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">Professional Greeting</div>
                                    <div style="font-size: 12px; color: #AAA;">0:31</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">Female voice • Used 156 times</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">Custom Recording 1</div>
                                    <div style="font-size: 12px; color: #AAA;">0:17</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">Male voice • Used 43 times</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">Generated Voice 1</div>
                                    <div style="font-size: 12px; color: #AAA;">0:24</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">AI Generated • Used 87 times</div>
                            </div>
                        </div>
                        
                        <div style="margin-top: 15px; font-size: 12px; color: #AAA; border-top: 1px solid #444; padding-top: 10px;">
                            Total Voicemails: 32 • Unique Variations: 128
                        </div>
                    </div>
                    
                    <div style="flex: 1; display: flex; flex-direction: column; padding: 20px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                            <div style="font-size: 20px; font-weight: bold; color: #EEE;">Standard Greeting 1</div>
                            <div>
                                <button style="padding: 8px 12px; background-color: #555; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Edit</button>
                                <button style="padding: 8px 12px; background-color: #5F5; color: black; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Generate Similar</button>
                                <button style="padding: 8px 12px; background-color: #FF6600; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Assign to Account</button>
                            </div>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: 3fr 2fr; gap: 20px; margin-bottom: 20px;">
                            <div style="background-color: #252525; border-radius: 5px; padding: 20px; display: flex; flex-direction: column;">
                                <div style="font-size: 16px; font-weight: bold; color: #EEE; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px;">
                                    Audio Player
                                </div>
                                
                                <div style="flex: 1; background-color: #333; padding: 20px; border-radius: 5px; display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 200px;">
                                    <div style="width: 220px; height: 220px; background-color: #252525; border-radius: 110px; display: flex; align-items: center; justify-content: center; margin-bottom: 20px;">
                                        <div style="width: 80px; height: 80px; background-color: #FF6600; border-radius: 40px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
                                            <div style="width: 0; height: 0; border-style: solid; border-width: 20px 0 20px 30px; border-color: transparent transparent transparent #FFFFFF; margin-left: 5px;"></div>
                                        </div>
                                    </div>
                                    
                                    <div style="width: 100%; height: 6px; background-color: #444; border-radius: 3px; overflow: hidden; margin-bottom: 10px;">
                                        <div style="height: 100%; background-color: #FF6600; width: 35%;"></div>
                                    </div>
                                    
                                    <div style="width: 100%; display: flex; justify-content: space-between; color: #CCC; font-size: 12px;">
                                        <div>0:08</div>
                                        <div>0:22</div>
                                    </div>
                                </div>
                            </div>
                            
                            <div style="background-color: #252525; border-radius: 5px; padding: 20px;">
                                <div style="font-size: 16px; font-weight: bold; color: #EEE; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px;">
                                    Voicemail Properties
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <div style="color: #AAA; font-size: 12px; margin-bottom: 3px;">Filename</div>
                                    <div style="color: #EEE; background-color: #333; padding: 5px 8px; border-radius: 3px; font-size: 14px;">standard_greeting_1.mp3</div>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <div style="color: #AAA; font-size: 12px; margin-bottom: 3px;">Duration</div>
                                    <div style="color: #EEE; background-color: #333; padding: 5px 8px; border-radius: 3px; font-size: 14px;">22 seconds</div>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <div style="color: #AAA; font-size: 12px; margin-bottom: 3px;">Voice Type</div>
                                    <div style="color: #EEE; background-color: #333; padding: 5px 8px; border-radius: 3px; font-size: 14px;">Male, Professional</div>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <div style="color: #AAA; font-size: 12px; margin-bottom: 3px;">Created</div>
                                    <div style="color: #EEE; background-color: #333; padding: 5px 8px; border-radius: 3px; font-size: 14px;">March 15, 2024</div>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <div style="color: #AAA; font-size: 12px; margin-bottom: 3px;">Usage Count</div>
                                    <div style="color: #EEE; background-color: #333; padding: 5px 8px; border-radius: 3px; font-size: 14px;">527 accounts</div>
                                </div>
                                
                                <div>
                                    <div style="color: #AAA; font-size: 12px; margin-bottom: 3px;">Tags</div>
                                    <div style="display: flex; flex-wrap: wrap; gap: 5px; background-color: #333; padding: 5px 8px; border-radius: 3px;">
                                        <div style="background-color: #444; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px;">standard</div>
                                        <div style="background-color: #444; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px;">male</div>
                                        <div style="background-color: #444; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px;">professional</div>
                                        <div style="background-color: #444; color: #CCC; padding: 3px 8px; border-radius: 3px; font-size: 12px;">clear</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div style="background-color: #252525; border-radius: 5px; padding: 20px; flex: 1;">
                            <div style="font-size: 16px; font-weight: bold; color: #EEE; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                                <div>Voicemail Transcript</div>
                                <button style="padding: 5px 10px; background-color: #444; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">Copy</button>
                            </div>
                            
                            <div style="font-size: 14px; color: #EEE; line-height: 1.6; background-color: #333; padding: 15px; border-radius: 5px;">
                                <p>"Hi, you've reached my voicemail. I'm not available to take your call right now. Please leave your name, number, and a brief message after the tone, and I'll get back to you as soon as possible. Thanks for calling."</p>
                            </div>
                            
                            <div style="margin-top: 20px;">
                                <div style="font-size: 16px; font-weight: bold; color: #EEE; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px;">
                                    Text-to-Speech Generator
                                </div>
                                
                                <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                                    <textarea style="flex: 1; padding: 10px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px; height: 100px; resize: none;" placeholder="Type or paste voicemail text here...">Hi, you've reached my voicemail. I'm not available to take your call right now. Please leave your name, number, and a brief message after the tone, and I'll get back to you as soon as possible. Thanks for calling.</textarea>
                                </div>
                                
                                <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                                    <div style="flex: 1;">
                                        <div style="color: #AAA; font-size: 12px; margin-bottom: 5px;">Voice Type</div>
                                        <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">
                                            <option>Male, Professional</option>
                                            <option>Male, Casual</option>
                                            <option>Female, Professional</option>
                                            <option>Female, Casual</option>
                                            <option>Custom Voice Model</option>
                                        </select>
                                    </div>
                                    <div style="flex: 1;">
                                        <div style="color: #AAA; font-size: 12px; margin-bottom: 5px;">Speed</div>
                                        <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">
                                            <option>Very Slow</option>
                                            <option>Slow</option>
                                            <option selected>Normal</option>
                                            <option>Fast</option>
                                            <option>Very Fast</option>
                                        </select>
                                    </div>
                                </div>
                                
                                <button style="width: 100%; padding: 10px 15px; background-color: #FF6600; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold;">Generate New Voicemail</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="app-footer">
                © ProgressBets™ | TextNow v1.0.0 | 5 Accounts Active
            </div>
        </div>
        '''
    )

@app.route('/campaign_schedule')
def campaign_schedule_route():
    """The campaign scheduling interface"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Schedule",
        active_page="/campaign_schedule",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; flex: 1;">
                    <div style="width: 280px; background-color: #252525; border-right: 1px solid #444; padding: 20px; display: flex; flex-direction: column;">
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE; border-bottom: 1px solid #444; padding-bottom: 10px;">
                            Schedule Manager
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <button class="form-button" style="margin-bottom: 10px;">Create Schedule</button>
                            <button class="form-button secondary-button">Import Template</button>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <input type="text" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px; margin-bottom: 8px;" placeholder="Search schedules...">
                            
                            <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">
                                <option>All Schedules</option>
                                <option selected>Active</option>
                                <option>Draft</option>
                                <option>Paused</option>
                                <option>Completed</option>
                            </select>
                        </div>
                        
                        <div style="font-size: 14px; font-weight: bold; margin: 15px 0 10px; color: #CCC; padding-top: 5px; border-top: 1px solid #444;">
                            Active Schedules
                        </div>
                        
                        <div style="flex: 1; overflow-y: auto; margin: -5px;">
                            <div style="padding: 10px; background-color: #333; margin: 5px; border-radius: 4px; cursor: pointer; border-left: 3px solid #FF6600;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">Spring Promotion</div>
                                    <div style="font-size: 12px; color: #5F5;">Active</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">10,000 accounts • 8am-8pm</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">Weekend Special</div>
                                    <div style="font-size: 12px; color: #5F5;">Active</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">5,000 accounts • 9am-9pm</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">NBA Finals Promo</div>
                                    <div style="font-size: 12px; color: #AAA;">Draft</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">7,500 accounts • Not scheduled</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">MLB Season Kickoff</div>
                                    <div style="font-size: 12px; color: #FA3;">Paused</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">3,200 accounts • 10am-6pm</div>
                            </div>
                            
                            <div style="padding: 10px; background-color: #2A2A2A; margin: 5px; border-radius: 4px; cursor: pointer;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div style="font-weight: bold; color: #EEE;">March Madness</div>
                                    <div style="font-size: 12px; color: #AAA;">Completed</div>
                                </div>
                                <div style="font-size: 12px; color: #CCC;">8,750 accounts • 8am-10pm</div>
                            </div>
                        </div>
                        
                        <div style="margin-top: 15px; font-size: 12px; color: #AAA; border-top: 1px solid #444; padding-top: 10px;">
                            Next execution: 23 minutes • 2 campaigns in progress
                        </div>
                    </div>
                    
                    <div style="flex: 1; display: flex; flex-direction: column; padding: 20px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                            <div style="font-size: 20px; font-weight: bold; color: #EEE;">Spring Promotion Schedule</div>
                            <div>
                                <button style="padding: 8px 12px; background-color: #555; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Edit</button>
                                <button style="padding: 8px 12px; background-color: #FA3; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Pause</button>
                                <button style="padding: 8px 12px; background-color: #FF6600; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; font-size: 12px;">Save Template</button>
                            </div>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                            <div style="background-color: #252525; border-radius: 5px; padding: 20px;">
                                <div style="font-size: 16px; font-weight: bold; color: #EEE; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px;">
                                    Active Hours
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <div style="font-weight: bold; color: #CCC; margin-bottom: 10px;">Daily Schedule</div>
                                    <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                                        <div style="flex: 1;">
                                            <div style="color: #AAA; font-size: 12px; margin-bottom: 5px;">Start Time</div>
                                            <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">
                                                <option>6:00 AM</option>
                                                <option>7:00 AM</option>
                                                <option selected>8:00 AM</option>
                                                <option>9:00 AM</option>
                                                <option>10:00 AM</option>
                                            </select>
                                        </div>
                                        <div style="flex: 1;">
                                            <div style="color: #AAA; font-size: 12px; margin-bottom: 5px;">End Time</div>
                                            <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">
                                                <option>6:00 PM</option>
                                                <option>7:00 PM</option>
                                                <option selected>8:00 PM</option>
                                                <option>9:00 PM</option>
                                                <option>10:00 PM</option>
                                            </select>
                                        </div>
                                    </div>
                                    
                                    <div style="font-weight: bold; color: #CCC; margin-bottom: 10px;">Days of Week</div>
                                    <div style="display: flex; gap: 5px; margin-bottom: 15px;">
                                        <div style="flex: 1; background-color: #333; color: #EEE; text-align: center; padding: 8px; border-radius: 4px; cursor: pointer;">Sun</div>
                                        <div style="flex: 1; background-color: #FF6600; color: white; text-align: center; padding: 8px; border-radius: 4px; cursor: pointer;">Mon</div>
                                        <div style="flex: 1; background-color: #FF6600; color: white; text-align: center; padding: 8px; border-radius: 4px; cursor: pointer;">Tue</div>
                                        <div style="flex: 1; background-color: #FF6600; color: white; text-align: center; padding: 8px; border-radius: 4px; cursor: pointer;">Wed</div>
                                        <div style="flex: 1; background-color: #FF6600; color: white; text-align: center; padding: 8px; border-radius: 4px; cursor: pointer;">Thu</div>
                                        <div style="flex: 1; background-color: #FF6600; color: white; text-align: center; padding: 8px; border-radius: 4px; cursor: pointer;">Fri</div>
                                        <div style="flex: 1; background-color: #FF6600; color: white; text-align: center; padding: 8px; border-radius: 4px; cursor: pointer;">Sat</div>
                                    </div>
                                    
                                    <div style="font-weight: bold; color: #CCC; margin-bottom: 10px;">Campaign Period</div>
                                    <div style="display: flex; gap: 10px;">
                                        <div style="flex: 1;">
                                            <div style="color: #AAA; font-size: 12px; margin-bottom: 5px;">Start Date</div>
                                            <div style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">April 15, 2024</div>
                                        </div>
                                        <div style="flex: 1;">
                                            <div style="color: #AAA; font-size: 12px; margin-bottom: 5px;">End Date</div>
                                            <div style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">April 30, 2024</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div style="background-color: #252525; border-radius: 5px; padding: 20px;">
                                <div style="font-size: 16px; font-weight: bold; color: #EEE; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px;">
                                    Distribution Settings
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <div style="font-weight: bold; color: #CCC; margin-bottom: 10px;">Message Distribution</div>
                                    <div style="margin-bottom: 15px;">
                                        <div style="color: #AAA; font-size: 12px; margin-bottom: 5px;">Pattern</div>
                                        <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">
                                            <option>Random (Unpredictable)</option>
                                            <option selected>Evenly Distributed</option>
                                            <option>Front-Loaded</option>
                                            <option>Peak Hours Focus</option>
                                            <option>Custom Pattern</option>
                                        </select>
                                    </div>
                                    
                                    <div style="margin-bottom: 15px;">
                                        <div style="color: #AAA; font-size: 12px; margin-bottom: 5px;">Daily Message Limit</div>
                                        <div style="display: flex; gap: 10px;">
                                            <input type="number" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;" value="100000">
                                            <select style="padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">
                                                <option selected>messages</option>
                                                <option>per account</option>
                                            </select>
                                        </div>
                                    </div>
                                    
                                    <div style="margin-bottom: 15px;">
                                        <div style="color: #AAA; font-size: 12px; margin-bottom: 5px;">Batch Size</div>
                                        <div style="display: flex; gap: 10px;">
                                            <input type="number" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;" value="10">
                                            <div style="padding: 8px; color: #AAA; font-size: 14px;">messages per round</div>
                                        </div>
                                    </div>
                                    
                                    <div style="margin-bottom: 15px;">
                                        <div style="color: #AAA; font-size: 12px; margin-bottom: 5px;">Throttling</div>
                                        <select style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #555; background-color: #333; color: #EEE; font-size: 14px;">
                                            <option>Aggressive (Maximum Speed)</option>
                                            <option selected>Balanced</option>
                                            <option>Conservative (Avoid Detection)</option>
                                            <option>Auto-Adjust</option>
                                        </select>
                                    </div>
                                    
                                    <div>
                                        <div style="color: #AAA; font-size: 12px; margin-bottom: 5px;">Smart Retry</div>
                                        <div style="display: flex; gap: 10px; align-items: center;">
                                            <div style="width: 50px; height: 26px; background-color: #FF6600; border-radius: 13px; position: relative; cursor: pointer;">
                                                <div style="width: 22px; height: 22px; background-color: white; border-radius: 11px; position: absolute; top: 2px; right: 2px;"></div>
                                            </div>
                                            <div style="color: #CCC; font-size: 14px;">Enabled (Auto-retry failed messages)</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div style="background-color: #252525; border-radius: 5px; padding: 20px; flex: 1; display: flex; flex-direction: column;">
                            <div style="font-size: 16px; font-weight: bold; color: #EEE; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px; display: flex; justify-content: space-between;">
                                <div>Distribution Visualization</div>
                                <div style="font-size: 12px; color: #AAA;">Estimated 100,000 messages per day</div>
                            </div>
                            
                            <div style="flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
                                <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 15px;">
                                    <div style="display: flex; justify-content: space-between; color: #CCC; font-size: 12px;">
                                        <div>8AM</div>
                                        <div>10AM</div>
                                        <div>12PM</div>
                                        <div>2PM</div>
                                        <div>4PM</div>
                                        <div>6PM</div>
                                        <div>8PM</div>
                                    </div>
                                    
                                    <div style="height: 150px; background-color: #333; border-radius: 5px; padding: 10px; position: relative;">
                                        <!-- Distribution graph bars -->
                                        <div style="position: absolute; bottom: 10px; left: 1%; width: 11%; height: 40%; background-color: #FF6600; border-radius: 3px 3px 0 0;"></div>
                                        <div style="position: absolute; bottom: 10px; left: 13%; width: 11%; height: 60%; background-color: #FF6600; border-radius: 3px 3px 0 0;"></div>
                                        <div style="position: absolute; bottom: 10px; left: 25%; width: 11%; height: 85%; background-color: #FF6600; border-radius: 3px 3px 0 0;"></div>
                                        <div style="position: absolute; bottom: 10px; left: 37%; width: 11%; height: 100%; background-color: #FF6600; border-radius: 3px 3px 0 0;"></div>
                                        <div style="position: absolute; bottom: 10px; left: 49%; width: 11%; height: 90%; background-color: #FF6600; border-radius: 3px 3px 0 0;"></div>
                                        <div style="position: absolute; bottom: 10px; left: 61%; width: 11%; height: 75%; background-color: #FF6600; border-radius: 3px 3px 0 0;"></div>
                                        <div style="position: absolute; bottom: 10px; left: 73%; width: 11%; height: 55%; background-color: #FF6600; border-radius: 3px 3px 0 0;"></div>
                                        <div style="position: absolute; bottom: 10px; left: 85%; width: 11%; height: 30%; background-color: #FF6600; border-radius: 3px 3px 0 0;"></div>
                                    </div>
                                </div>
                                
                                <div style="display: flex; gap: 20px;">
                                    <div style="flex: 1; background-color: #333; border-radius: 5px; padding: 15px;">
                                        <div style="font-weight: bold; color: #EEE; margin-bottom: 10px;">Daily Statistics</div>
                                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 13px;">
                                            <div>
                                                <div style="color: #AAA;">Messages per Hour:</div>
                                                <div style="color: #EEE;">~8,333</div>
                                            </div>
                                            <div>
                                                <div style="color: #AAA;">Messages per Minute:</div>
                                                <div style="color: #EEE;">~139</div>
                                            </div>
                                            <div>
                                                <div style="color: #AAA;">Messages per Account:</div>
                                                <div style="color: #EEE;">10</div>
                                            </div>
                                            <div>
                                                <div style="color: #AAA;">Active Accounts:</div>
                                                <div style="color: #EEE;">10,000</div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div style="flex: 1; background-color: #333; border-radius: 5px; padding: 15px;">
                                        <div style="font-weight: bold; color: #EEE; margin-bottom: 10px;">Campaign Progress</div>
                                        <div style="margin-bottom: 10px;">
                                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                                <div style="color: #CCC;">Completion:</div>
                                                <div style="color: #EEE; font-weight: bold;">68% (680,000 / 1,000,000)</div>
                                            </div>
                                            <div style="width: 100%; height: 8px; background-color: #444; border-radius: 4px; overflow: hidden;">
                                                <div style="height: 100%; background-color: #FF6600; width: 68%;"></div>
                                            </div>
                                        </div>
                                        <div style="color: #CCC; font-size: 12px;">
                                            Estimated completion: April 30, 2024
                                        </div>
                                    </div>
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
        '''
    )

@app.route('/nav-debug')
def nav_debug():
    """Debug page to examine navigation menu"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Navigation Debug",
        active_page="/nav-debug",
        content='''
        <div class="app-container">
            <div class="app-content" style="padding: 20px;">
                <h1>Navigation Menu Debug</h1>
                <div style="background-color: #252525; padding: 20px; border-radius: 5px; margin-top: 20px;">
                    <h2>Raw HTML:</h2>
                    <pre style="background-color: #333; padding: 15px; overflow: auto; max-height: 500px; color: #FFF; font-family: monospace; font-size: 12px; line-height: 1.5; border-radius: 3px;"></pre>
                </div>
            </div>
            
            <div class="app-footer">
                © ProgressBets™ | TextNow v1.0.0 | 5 Accounts Active
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
    print("PROGRESS GHOST CREATOR SERVER IS RUNNING")
    print("="*60)
    print("\nAccess the application in your web browser at: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server when you're done.")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)