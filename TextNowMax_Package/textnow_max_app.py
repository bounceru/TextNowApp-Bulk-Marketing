"""
TextNow Max - Account Creator & Campaign Manager

Advanced automation platform for TextNow messaging with account creation and campaign management.
"""

import os
import shutil
import importlib
import subprocess
import threading
import time
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template_string, send_from_directory, redirect, url_for, request, jsonify

app = Flask(__name__)

# Import database initialization
from init_database import init_database

# Initialize database
init_database()

# Initialize the account activity manager if available
try:
    from account_activity_manager import get_account_activity_manager
    account_activity_manager = get_account_activity_manager()
    # Auto-start account activity monitoring system
    account_activity_manager.start_monitoring()
    print("[INFO] Account activity monitoring system started")
except ImportError:
    print("[WARNING] Account activity manager module not found")
    account_activity_manager = None
except Exception as e:
    print(f"[ERROR] Failed to start account activity manager: {str(e)}")
    account_activity_manager = None

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
            print("Found logo at {}".format(logo_path))
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

# Helper function to format dates nicely
def format_date(date_str):
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_str

# Helper function to calculate days ago
def calculate_days_ago(date_str):
    if not date_str:
        return 0
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        delta = datetime.now() - dt
        return delta.days
    except:
        return 0

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('ghost_accounts.db')
    conn.row_factory = sqlite3.Row
    return conn

# Get statistics from database
def get_statistics():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Account statistics
        cursor.execute('''
            SELECT 
                COUNT(*) AS total_accounts,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_accounts
            FROM accounts
        ''')
        
        account_stats = cursor.fetchone()
        total_accounts = account_stats['total_accounts'] if account_stats and account_stats['total_accounts'] is not None else 0
        active_accounts = account_stats['active_accounts'] if account_stats and account_stats['active_accounts'] is not None else 0
        
        # Message statistics
        cursor.execute('''
            SELECT 
                COUNT(*) AS total_messages,
                SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) AS delivered_messages
            FROM messages
        ''')
        
        message_stats = cursor.fetchone()
        total_messages = message_stats['total_messages'] if message_stats and message_stats['total_messages'] is not None else 0
        delivered_messages = message_stats['delivered_messages'] if message_stats and message_stats['delivered_messages'] is not None else 0
        
        # Calculate success rate
        success_rate = 0
        if total_messages > 0:
            success_rate = round((delivered_messages / total_messages) * 100, 1)
            
        conn.close()
        
        return {
            'total_accounts': total_accounts,
            'active_accounts': active_accounts,
            'total_messages': total_messages,
            'success_rate': success_rate
        }
        
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {
            'total_accounts': 0,
            'active_accounts': 0,
            'total_messages': 0,
            'success_rate': 0
        }

# Get account details from database
def get_accounts(limit=10, offset=0, filters=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query based on filters
        query = '''
            SELECT 
                id,
                phone_number,
                username,
                email,
                password,
                first_name,
                last_name,
                area_code,
                created_at,
                last_activity,
                status,
                health_score,
                device_fingerprint,
                session_data
            FROM accounts
        '''
        
        params = []
        
        # Apply filters if provided
        if filters:
            conditions = []
            
            if 'status' in filters and filters['status'] != 'all':
                conditions.append("status = ?")
                params.append(filters['status'])
            
            if 'area_code' in filters and filters['area_code'] != 'all':
                conditions.append("area_code = ?")
                params.append(filters['area_code'])
            
            if 'search' in filters and filters['search']:
                search_term = "%{}%".format(filters['search'])
                conditions.append("(phone_number LIKE ? OR email LIKE ? OR username LIKE ? OR first_name LIKE ? OR last_name LIKE ?)")
                params.extend([search_term, search_term, search_term, search_term, search_term])
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        # Add ordering and limit
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        accounts = cursor.fetchall()
        
        # Convert to list of dictionaries for easier handling
        result = []
        for account in accounts:
            # Try to extract IP and proxy from session data
            import json
            session_data = {}
            ip_address = "Unknown"
            proxy_used = "None"
            
            if account['session_data']:
                try:
                    session_data = json.loads(account['session_data'])
                    ip_address = session_data.get('ip_address', "Unknown")
                    proxy_used = session_data.get('proxy', "None")
                except:
                    pass
            
            result.append({
                'id': account['id'],
                'phone_number': account['phone_number'] or "No Number",
                'username': account['username'] or "",
                'email': account['email'] or "",
                'first_name': account['first_name'] or "",
                'last_name': account['last_name'] or "",
                'area_code': account['area_code'] or "",
                'created_at': format_date(account['created_at']),
                'created_days_ago': calculate_days_ago(account['created_at']),
                'last_activity': format_date(account['last_activity']),
                'last_activity_days_ago': calculate_days_ago(account['last_activity']),
                'status': account['status'] or "unknown",
                'health_score': account['health_score'] or 0,
                'device_fingerprint': account['device_fingerprint'] or "",
                'ip_address': ip_address,
                'proxy_used': proxy_used
            })
            
        # Get total count for pagination
        cursor.execute('SELECT COUNT(*) FROM accounts')
        total_count = cursor.fetchone()[0]
            
        conn.close()
        
        return {
            'accounts': result,
            'total': total_count
        }
        
    except Exception as e:
        print("Error getting accounts: {}".format(e))
        return {
            'accounts': [],
            'total': 0
        }

# Get area codes from database
def get_area_codes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT area_code FROM area_codes ORDER BY area_code')
        area_codes = [row['area_code'] for row in cursor.fetchall()]
            
        conn.close()
        
        return area_codes
        
    except Exception as e:
        print(f"Error getting area codes: {e}")
        return []

# Get campaigns from database
def get_campaigns(limit=10, offset=0):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                id,
                name,
                description,
                start_date,
                end_date,
                status,
                created_at
            FROM campaigns
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        campaigns = cursor.fetchall()
        
        # Convert to list of dictionaries
        result = []
        for campaign in campaigns:
            result.append({
                'id': campaign['id'],
                'name': campaign['name'] or "",
                'description': campaign['description'] or "",
                'start_date': format_date(campaign['start_date']),
                'end_date': format_date(campaign['end_date']),
                'status': campaign['status'] or "draft",
                'created_at': format_date(campaign['created_at'])
            })
        
        # Get total count for pagination
        cursor.execute('SELECT COUNT(*) FROM campaigns')
        total_count = cursor.fetchone()[0]
            
        conn.close()
        
        return {
            'campaigns': result,
            'total': total_count
        }
        
    except Exception as e:
        print(f"Error getting campaigns: {e}")
        return {
            'campaigns': [],
            'total': 0
        }

# Get recent messages from database
def get_recent_messages(limit=10):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                m.id,
                m.recipient,
                m.content,
                m.sent_at,
                m.status,
                a.phone_number as sender
            FROM messages m
            LEFT JOIN accounts a ON m.account_id = a.id
            ORDER BY m.sent_at DESC
            LIMIT ?
        ''', (limit,))
        
        messages = cursor.fetchall()
        
        # Convert to list of dictionaries
        result = []
        for message in messages:
            result.append({
                'id': message['id'],
                'sender': message['sender'] or "Unknown",
                'recipient': message['recipient'] or "",
                'content': message['content'] or "",
                'sent_at': format_date(message['sent_at']),
                'status': message['status'] or "unknown"
            })
            
        conn.close()
        
        return result
        
    except Exception as e:
        print(f"Error getting recent messages: {e}")
        return []

# Base HTML template with fixed navigation
BASE_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>TextNow Max - {{ title }}</title>
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
            cursor: pointer;
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
            margin-top: 95px; /* Increased to make room for both nav and status bars */
            min-height: calc(100vh - 95px);
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
            height: calc(100vh - 135px);
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
        
        /* Status messages for clickable feedback */
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
        
        /* Toggle Switch */
        .switch {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 24px;
        }
        
        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #444;
            transition: .4s;
        }
        
        .slider:before {
            position: absolute;
            content: "";
            height: 16px;
            width: 16px;
            left: 4px;
            bottom: 4px;
            background-color: #CCC;
            transition: .4s;
        }
        
        input:checked + .slider {
            background-color: #FF6600;
        }
        
        input:checked + .slider:before {
            transform: translateX(26px);
            background-color: white;
        }
        
        .slider.round {
            border-radius: 24px;
        }
        
        .slider.round:before {
            border-radius: 50%;
        }
        
        /* Empty states */
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #AAA;
        }
        
        .empty-state-icon {
            font-size: 40px;
            margin-bottom: 20px;
            color: #555;
        }
        
        .empty-state-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #CCC;
        }
        
        .empty-state-text {
            font-size: 14px;
            max-width: 400px;
            margin: 0 auto 20px auto;
            color: #999;
        }
    </style>
    <script>
        // This makes all buttons clickable with visual feedback
        document.addEventListener('DOMContentLoaded', function() {
            // Add click handler to all buttons and interactive elements
            document.querySelectorAll('button, .form-button, .tab, input[type="submit"], .secondary-button').forEach(function(element) {
                element.addEventListener('click', function(e) {
                    // Don't prevent default for form submissions
                    if (this.type !== 'submit') {
                        e.preventDefault();
                    }
                    
                    // Visual feedback
                    this.style.transform = 'scale(0.97)';
                    setTimeout(() => {
                        this.style.transform = 'scale(1)';
                    }, 100);
                    
                    // Show message
                    if (this.textContent.trim()) {
                        showStatusMessage('Clicked: ' + this.textContent.trim(), 'success');
                    }
                    
                    // Handle details button in account dashboard
                    if (this.textContent.trim() === 'Details') {
                        var row = this.closest('tr');
                        var accountId = row.getAttribute('data-account-id');
                        var detailsRow = row.nextElementSibling;
                        
                        // Toggle details row visibility
                        if (detailsRow && detailsRow.classList.contains('account-details')) {
                            if (detailsRow.style.display === 'none' || !detailsRow.style.display) {
                                detailsRow.style.display = 'table-row';
                                showStatusMessage('Expanded account details', 'success');
                            } else {
                                detailsRow.style.display = 'none';
                                showStatusMessage('Collapsed account details', 'success');
                            }
                        }
                    }
                    
                    // Handle hide details button in account details panel
                    if (this.textContent.trim() === 'Hide Details') {
                        var detailsRow = this.closest('tr');
                        if (detailsRow && detailsRow.classList.contains('account-details')) {
                            detailsRow.style.display = 'none';
                            showStatusMessage('Collapsed account details', 'success');
                        }
                    }
                    
                    // Handle tab selection in anti-detection page
                    if (this.classList.contains('tab')) {
                        var tabContainer = this.closest('.tabs');
                        if (tabContainer) {
                            // Deactivate all tabs
                            tabContainer.querySelectorAll('.tab').forEach(function(tab) {
                                tab.classList.remove('active');
                            });
                            // Activate clicked tab
                            this.classList.add('active');
                            
                            // Get tab name
                            var tabName = this.getAttribute('data-tab');
                            if (tabName) {
                                // Hide all tab content sections
                                document.querySelectorAll('.tab-content').forEach(function(content) {
                                    content.style.display = 'none';
                                });
                                
                                // Show selected tab content
                                var selectedContent = document.getElementById('tab-' + tabName);
                                if (selectedContent) {
                                    selectedContent.style.display = 'block';
                                }
                            }
                            
                            showStatusMessage('Selected tab: ' + this.textContent.trim(), 'success');
                        }
                    }
                });
            });
            
            // Make navigation links work (don't intercept normal navigation)
            document.querySelectorAll('.nav-link').forEach(function(element) {
                if (!element.getAttribute('href')) {
                    element.addEventListener('click', function(e) {
                        e.preventDefault();
                        showStatusMessage('Clicked: ' + this.textContent.trim(), 'success');
                    });
                }
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
        
        // Handle area code preset selection
        function selectAreaCodePreset(presetName) {
            // These would be loaded from the database in a complete version
            const presets = {
                'northeast': '201, 203, 207, 212, 215, 401, 413, 508, 516',
                'southeast': '239, 305, 321, 404, 561, 704, 754, 786, 813, 850, 904, 954',
                'midwest': '216, 248, 312, 317, 414, 517, 614, 616, 630, 734',
                'southwest': '214, 281, 469, 512, 602, 623, 713, 817, 832, 915, 972',
                'west': '213, 310, 323, 408, 415, 503, 510, 530, 619, 626, 650, 707, 714, 818, 858, 909, 925, 949'
            };
            
            const areaCodeInput = document.getElementById('area-codes-input');
            if (areaCodeInput && presets[presetName]) {
                areaCodeInput.value = presets[presetName];
                showStatusMessage('Selected area code preset: ' + presetName, 'success');
            }
        }
        
        // Device status polling
        function pollDeviceStatus() {
            fetch('/api/device/status')
                .then(response => response.json())
                .then(data => {
                    const statusElement = document.getElementById('device-status');
                    if (statusElement) {
                        if (data.connected) {
                            statusElement.innerHTML = `<span class="status-badge status-active">Connected</span> IP: ${data.ip}`;
                        } else {
                            statusElement.innerHTML = `<span class="status-badge status-danger">Disconnected</span>`;
                        }
                    }
                })
                .catch(error => {
                    console.error('Error checking device status:', error);
                })
                .finally(() => {
                    // Poll again after 10 seconds
                    setTimeout(pollDeviceStatus, 10000);
                });
        }
        
        // Start polling when the document is ready
        document.addEventListener('DOMContentLoaded', function() {
            pollDeviceStatus();
        });
    </script>
    <div id="navigation" class="nav-bar">
        <img src="/static/progress_logo.png" alt="Logo" class="nav-logo">
        <div class="nav-menu">
            <a href="/" class="nav-link {{ 'active' if active_page == '/' else '' }}">Home</a>
            <a href="/creator" class="nav-link {{ 'active' if active_page == '/creator' else '' }}">Account Creator</a>
            <a href="/dashboard" class="nav-link {{ 'active' if active_page == '/dashboard' else '' }}">Account Dashboard</a>
            <a href="/campaigns" class="nav-link {{ 'active' if active_page == '/campaigns' else '' }}">Campaigns</a>
            <a href="/manual-messaging" class="nav-link {{ 'active' if active_page == '/manual-messaging' else '' }}">Manual Messaging</a>
            <a href="/message-dashboard" class="nav-link {{ 'active' if active_page == '/message-dashboard' else '' }}">Message Dashboard</a>
            <a href="/media-dashboard" class="nav-link {{ 'active' if active_page == '/media-dashboard' else '' }}">Media</a>
            <a href="/voicemail-manager" class="nav-link {{ 'active' if active_page == '/voicemail-manager' else '' }}">Voicemail</a>
            <a href="/account-health" class="nav-link {{ 'active' if active_page == '/account-health' else '' }}">Account Health</a>
            <a href="/campaign-schedule" class="nav-link {{ 'active' if active_page == '/campaign-schedule' else '' }}">Scheduler</a>
        </div>
        <div style="margin-left: auto; display: flex; align-items: center; gap: 15px;">
            <div id="device-status">
                <span class="status-badge status-neutral">Checking...</span>
            </div>
        </div>
    </div>
</head>
<body>
    <div class="content-wrapper">
        {{ content | safe }}
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    """Display the TextNow Max application homepage with real data"""
    process_assets()
    
    # Get statistics
    stats = get_statistics()
    
    # Get recent messages for the activity feed
    recent_messages = get_recent_messages(5)
    
    # Build activity feed HTML
    activity_feed_html = ''
    if recent_messages:
        for message in recent_messages:
            status_class = 'status-active' if message['status'] == 'delivered' else 'status-neutral'
            
            activity_feed_html += f'''
            <div style="padding: 10px; border-bottom: 1px solid #444;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <div style="font-weight: bold;">{message['sender']} → {message['recipient']}</div>
                    <div style="font-size: 12px; color: #AAA;">{message['sent_at']}</div>
                </div>
                <div style="margin-bottom: 5px;">{message['content'][:50]}{'...' if len(message['content']) > 50 else ''}</div>
                <div><span class="status-badge {status_class}">{message['status'].capitalize()}</span></div>
            </div>
            '''
    else:
        activity_feed_html = '''
        <div class="empty-state">
            <div class="empty-state-icon">📭</div>
            <div class="empty-state-title">No Messages Yet</div>
            <div class="empty-state-text">Start sending messages to see your activity here.</div>
        </div>
        '''
    
    return render_template_string(
        BASE_HTML,
        title="Home",
        active_page="/",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%;">
                    <div style="max-width: 1000px; width: 100%;">
                        <h1 style="font-size: 32px; margin-bottom: 20px; color: #FF6600; text-align: center;">TextNow Max</h1>
                        <p style="text-align: center;">The ultimate TextNow account management and automation platform. Create, manage, and utilize ghost accounts with sophisticated distribution, voicemail setup, and mass messaging capabilities.</p>
                        
                        <div style="display: flex; justify-content: center; gap: 15px; margin: 30px 0;">
                            <a href="/creator" class="form-button">Create Accounts</a>
                            <a href="/dashboard" class="form-button">Manage Accounts</a>
                            <a href="/campaigns" class="form-button">Run Campaigns</a>
                        </div>
                        
                        <div style="display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; margin-top: 30px;">
                            <div style="background-color: #252525; padding: 20px; border-radius: 6px; min-width: 180px; text-align: center;">
                                <div style="font-size: 24px; font-weight: bold; color: #FF6600;">{stats['total_accounts']}</div>
                                <div style="color: #AAA; margin-top: 5px;">Total Accounts</div>
                            </div>
                            <div style="background-color: #252525; padding: 20px; border-radius: 6px; min-width: 180px; text-align: center;">
                                <div style="font-size: 24px; font-weight: bold; color: #FF6600;">{stats['active_accounts']}</div>
                                <div style="color: #AAA; margin-top: 5px;">Active Accounts</div>
                            </div>
                            <div style="background-color: #252525; padding: 20px; border-radius: 6px; min-width: 180px; text-align: center;">
                                <div style="font-size: 24px; font-weight: bold; color: #FF6600;">{stats['total_messages']}</div>
                                <div style="color: #AAA; margin-top: 5px;">Messages Sent</div>
                            </div>
                            <div style="background-color: #252525; padding: 20px; border-radius: 6px; min-width: 180px; text-align: center;">
                                <div style="font-size: 24px; font-weight: bold; color: #FF6600;">{stats['success_rate']}%</div>
                                <div style="color: #AAA; margin-top: 5px;">Success Rate</div>
                            </div>
                        </div>
                        
                        <div style="margin-top: 40px;">
                            <div style="display: flex; gap: 20px;">
                                <div style="flex: 1; background-color: #252525; padding: 20px; border-radius: 6px;">
                                    <h2 style="font-size: 18px; margin-top: 0; margin-bottom: 15px; color: #EEE;">Recent Activity</h2>
                                    <div style="max-height: 300px; overflow-y: auto;">
                                        {activity_feed_html}
                                    </div>
                                </div>
                                
                                <div style="flex: 1; background-color: #252525; padding: 20px; border-radius: 6px;">
                                    <h2 style="font-size: 18px; margin-top: 0; margin-bottom: 15px; color: #EEE;">Quick Actions</h2>
                                    <div style="display: flex; flex-direction: column; gap: 10px;">
                                        <a href="/creator" class="form-button">Create New Accounts</a>
                                        <a href="/dashboard" class="form-button">Manage Existing Accounts</a>
                                        <a href="/campaigns" class="form-button">Create Campaign</a>
                                        <a href="/manual-messaging" class="form-button">Send Manual Messages</a>
                                        <a href="/media-dashboard" class="form-button">Manage Media</a>
                                        <a href="/account-health" class="form-button">Check Account Health</a>
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

@app.route('/creator')
def creator_page():
    """The main account creator page with area code input and start button"""
    process_assets()
    
    # Get area codes from database
    area_codes = get_area_codes()
    area_codes_str = ", ".join(area_codes[:6]) if area_codes else ""
    
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
                            <input type="number" class="form-input" value="10" min="1" max="10000">
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label class="form-label">Registration Details</label>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <button class="form-button secondary-button" style="flex: 1; position: relative; overflow: hidden;">
                                    Upload File
                                    <input type="file" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;" accept=".txt,.csv,.xlsx,.xls,.doc,.docx">
                                </button>
                                <span style="color: #CCC; font-size: 12px;">No file</span>
                            </div>
                            <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                Upload a document with names, birthdays, and emails for registration.
                                If no file is uploaded, details will be randomly generated.
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label class="form-label">Creation Duration</label>
                            <select class="form-select">
                                <option>Auto</option>
                                <option>1 Hour</option>
                                <option>2 Hours</option>
                                <option>4 Hours</option>
                                <option selected>8 Hours</option>
                                <option>12 Hours</option>
                                <option>24 Hours</option>
                            </select>
                            <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                Maximum time allowed for account creation
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label class="form-label">Proxidize Mode</label>
                            <select class="form-select">
                                <option selected>Standard Connection (HTTP)</option>
                                <option>High Security (SOCKS5)</option>
                                <option>HTTPS Connection</option>
                            </select>
                            <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                TextNow Max uses Proxidize exclusively for IP management and rotation
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label class="form-label">Area Codes</label>
                            <input type="text" id="area-codes-input" class="form-input" value="{area_codes_str}" placeholder="Enter area codes separated by commas">
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
                            
                            <div style="margin-bottom: 10px;">
                                <select id="preset-category" class="form-select" onchange="
                                    const value = this.value;
                                    document.querySelectorAll('.preset-group').forEach(group => {
                                        group.style.display = 'none';
                                    });
                                    document.getElementById(value + '-presets').style.display = 'flex';
                                ">
                                    <option value="regions">US Regions</option>
                                    <option value="states">States (All 50)</option>
                                    <option value="cities">Major Cities</option>
                                    <option value="florida-specific">Florida Only</option>
                                </select>
                            </div>
                            
                            <!-- Regions Presets -->
                            <div id="regions-presets" class="preset-group" style="display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 10px;">
                                <button class="form-button secondary-button" onclick="selectAreaCodePreset('northeast')">Northeast</button>
                                <button class="form-button secondary-button" onclick="selectAreaCodePreset('southeast')">Southeast</button>
                                <button class="form-button secondary-button" onclick="selectAreaCodePreset('midwest')">Midwest</button>
                                <button class="form-button secondary-button" onclick="selectAreaCodePreset('southwest')">Southwest</button>
                                <button class="form-button secondary-button" onclick="selectAreaCodePreset('west')">West</button>
                            </div>
                            
                            <!-- Other preset groups (initially hidden) -->
                            <div id="states-presets" class="preset-group" style="display: none; gap: 5px; flex-wrap: wrap; margin-bottom: 10px; max-height: 150px; overflow-y: auto;">
                                <!-- State buttons would be populated from database -->
                                <button class="form-button secondary-button">Florida</button>
                                <button class="form-button secondary-button">California</button>
                                <button class="form-button secondary-button">Texas</button>
                                <!-- etc. -->
                            </div>
                            
                            <div id="cities-presets" class="preset-group" style="display: none; gap: 5px; flex-wrap: wrap; margin-bottom: 10px; max-height: 150px; overflow-y: auto;">
                                <!-- City buttons would be populated from database -->
                                <button class="form-button secondary-button">Miami</button>
                                <button class="form-button secondary-button">Los Angeles</button>
                                <button class="form-button secondary-button">New York</button>
                                <!-- etc. -->
                            </div>
                            
                            <div id="florida-specific-presets" class="preset-group" style="display: none; gap: 5px; flex-wrap: wrap; margin-bottom: 10px;">
                                <!-- Florida area codes would be populated from database -->
                                <button class="form-button secondary-button">305 (Miami)</button>
                                <button class="form-button secondary-button">954 (Ft. Lauderdale)</button>
                                <button class="form-button secondary-button">561 (West Palm)</button>
                                <!-- etc. -->
                            </div>
                        </div>
                        
                        <button class="form-button" style="width: 100%;">Start Creation</button>
                    </div>
                    
                    <!-- Main Display -->
                    <div style="flex: 1; display: flex; flex-direction: column;">
                        <div class="form-panel">
                            <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE;">Emulator Status</div>
                            
                            <div style="display: flex; gap: 15px; margin-bottom: 15px;">
                                <button class="form-button">Start Emulator</button>
                                <button class="form-button secondary-button">Stop Emulator</button>
                                <button class="form-button">Install TextNow APK</button>
                            </div>
                            
                            <div style="display: flex; gap: 15px; align-items: center;">
                                <div>Status: <span class="status-badge status-neutral">Not Running</span></div>
                                <div>TextNow APK: <span class="status-badge status-neutral">Not Installed</span></div>
                            </div>
                        </div>
                        
                        <div class="form-panel" style="flex: 1; overflow: auto;">
                            <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE;">Creation Log</div>
                            
                            <div style="margin-bottom: 15px;">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: 0%;"></div>
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #AAA;">
                                    <span>0 of 0 accounts created</span>
                                    <span>0%</span>
                                </div>
                            </div>
                            
                            <div class="empty-state">
                                <div class="empty-state-icon">⚙️</div>
                                <div class="empty-state-title">Ready to Create Accounts</div>
                                <div class="empty-state-text">Configure your settings and click "Start Creation" to begin creating TextNow accounts.</div>
                                <button class="form-button">Start Creation</button>
                            </div>
                            
                            <!-- Log output would appear here when active -->
                            <div style="font-family: monospace; background-color: #1a1a1a; padding: 10px; border-radius: 4px; max-height: 300px; overflow-y: auto; display: none;">
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
    """The account management dashboard page with real data"""
    process_assets()
    
    # Get accounts from database
    account_data = get_accounts(limit=10)
    accounts = account_data['accounts']
    total_accounts = account_data['total']
    
    # Get area codes for filter
    area_codes = get_area_codes()
    
    # Build area code options HTML
    area_code_options_html = '<option value="all">All Area Codes</option>'
    for area_code in area_codes:
        area_code_options_html += f'<option value="{area_code}">{area_code}</option>'
    
    # Build the account rows HTML
    account_rows_html = ''
    for account in accounts:
        status_class = ''
        if account['status'] == 'active':
            status_class = 'status-active'
        elif account['status'] == 'banned':
            status_class = 'status-danger'
        elif account['status'] == 'flagged':
            status_class = 'status-warning'
        elif account['status'] == 'pending' or account['status'] == 'new':
            status_class = 'status-neutral'
        else:
            status_class = 'status-neutral'
        
        # Format phone number nicely if it exists
        phone_display = account['phone_number']
        if phone_display and phone_display != "No Number" and len(phone_display) >= 10:
            # Ensure it's at least 10 digits
            digits = ''.join(filter(str.isdigit, phone_display))
            if len(digits) >= 10:
                phone_display = f"({digits[:3]}) {digits[3:6]}-{digits[6:10]}"
        
        # Create the main account row
        account_rows_html += f'''
            <tr data-account-id="{account['id']}">
                <td><input type="checkbox"></td>
                <td>{phone_display}</td>
                <td>{account['email']}<br><span style="font-size: 12px; color: #999;">{account['first_name']} {account['last_name']}</span></td>
                <td>{account['area_code']}</td>
                <td>{account['created_at']}<br><span style="font-size: 12px; color: #999;">{account['created_days_ago']} days ago</span></td>
                <td>{account['last_activity']}<br><span style="font-size: 12px; color: #999;">{account['last_activity_days_ago']} days ago</span></td>
                <td><span class="status-badge {status_class}">{account['status'].capitalize()}</span></td>
                <td>
                    <button class="form-button secondary-button">Details</button>
                    <button class="form-button secondary-button">Login</button>
                </td>
            </tr>
            <tr class="account-details" style="display: none;">
                <td colspan="8">
                    <div style="padding: 15px; background-color: #2A2A2A; border-radius: 4px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <h3 style="margin: 0; color: #EEE;">Account Details: {phone_display}</h3>
                            <button class="form-button secondary-button">Hide Details</button>
                        </div>
                        
                        <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                            <div style="flex: 1;">
                                <div style="margin-bottom: 15px;">
                                    <div style="font-size: 12px; color: #AAA; margin-bottom: 3px;">Username:</div>
                                    <div>{account['username']}</div>
                                </div>
                                <div style="margin-bottom: 15px;">
                                    <div style="font-size: 12px; color: #AAA; margin-bottom: 3px;">Full Name:</div>
                                    <div>{account['first_name']} {account['last_name']}</div>
                                </div>
                                <div style="margin-bottom: 15px;">
                                    <div style="font-size: 12px; color: #AAA; margin-bottom: 3px;">Email:</div>
                                    <div>{account['email']}</div>
                                </div>
                                <div style="margin-bottom: 15px;">
                                    <div style="font-size: 12px; color: #AAA; margin-bottom: 3px;">Phone:</div>
                                    <div>{phone_display}</div>
                                </div>
                            </div>
                            
                            <div style="flex: 1;">
                                <div style="margin-bottom: 15px;">
                                    <div style="font-size: 12px; color: #AAA; margin-bottom: 3px;">Created:</div>
                                    <div>{account['created_at']} ({account['created_days_ago']} days ago)</div>
                                </div>
                                <div style="margin-bottom: 15px;">
                                    <div style="font-size: 12px; color: #AAA; margin-bottom: 3px;">Last Activity:</div>
                                    <div>{account['last_activity']} ({account['last_activity_days_ago']} days ago)</div>
                                </div>
                                <div style="margin-bottom: 15px;">
                                    <div style="font-size: 12px; color: #AAA; margin-bottom: 3px;">Status:</div>
                                    <div><span class="status-badge {status_class}">{account['status'].capitalize()}</span></div>
                                </div>
                                <div style="margin-bottom: 15px;">
                                    <div style="font-size: 12px; color: #AAA; margin-bottom: 3px;">Health Score:</div>
                                    <div>
                                        <div class="progress-bar" style="width: 150px;">
                                            <div class="progress-fill" style="width: {account['health_score']}%;"></div>
                                        </div>
                                        <div style="font-size: 12px;">{account['health_score']}/100</div>
                                    </div>
                                </div>
                            </div>
                            
                            <div style="flex: 1;">
                                <div style="margin-bottom: 15px;">
                                    <div style="font-size: 12px; color: #AAA; margin-bottom: 3px;">Device Fingerprint:</div>
                                    <div style="font-size: 12px; word-break: break-all;">{account['device_fingerprint']}</div>
                                </div>
                                <div style="margin-bottom: 15px;">
                                    <div style="font-size: 12px; color: #AAA; margin-bottom: 3px;">Last Known IP:</div>
                                    <div>{account['ip_address']}</div>
                                </div>
                                <div style="margin-bottom: 15px;">
                                    <div style="font-size: 12px; color: #AAA; margin-bottom: 3px;">Proxy Used:</div>
                                    <div>{account['proxy_used']}</div>
                                </div>
                            </div>
                        </div>
                        
                        <div style="display: flex; gap: 10px;">
                            <button class="form-button secondary-button">Messages</button>
                            <button class="form-button secondary-button">Login History</button>
                            <button class="form-button secondary-button">Activity Log</button>
                            <button class="form-button secondary-button">Edit</button>
                            <button class="form-button secondary-button" style="margin-left: auto;">Delete</button>
                        </div>
                    </div>
                </td>
            </tr>
        '''
    
    # If no accounts found, show empty state
    if not accounts:
        account_rows_html = '''
            <tr>
                <td colspan="8">
                    <div class="empty-state">
                        <div class="empty-state-icon">👤</div>
                        <div class="empty-state-title">No Accounts Found</div>
                        <div class="empty-state-text">Create your first TextNow account to get started.</div>
                        <a href="/creator" class="form-button">Create New Account</a>
                    </div>
                </td>
            </tr>
        '''
    
    # Get account statistics
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get various account counts
        cursor.execute('''
            SELECT 
                COUNT(*) AS total_accounts,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_accounts,
                SUM(CASE WHEN status = 'banned' THEN 1 ELSE 0 END) AS banned_accounts,
                SUM(CASE WHEN created_at >= datetime('now', '-1 day') THEN 1 ELSE 0 END) AS new_today
            FROM accounts
        ''')
        
        stats = cursor.fetchone()
        
        total_accounts = stats['total_accounts'] if stats and stats['total_accounts'] is not None else 0
        active_accounts = stats['active_accounts'] if stats and stats['active_accounts'] is not None else 0
        banned_accounts = stats['banned_accounts'] if stats and stats['banned_accounts'] is not None else 0
        new_today = stats['new_today'] if stats and stats['new_today'] is not None else 0
        
        conn.close()
        
    except Exception as e:
        print(f"Error getting account statistics: {e}")
        total_accounts = 0
        active_accounts = 0
        banned_accounts = 0
        new_today = 0
    
    return render_template_string(
        BASE_HTML,
        title="Account Dashboard",
        active_page="/dashboard",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                    <div class="form-panel" style="flex: 1;">
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE;">Account Statistics</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                            <div>
                                <div style="font-size: 12px; color: #AAA;">Total Accounts</div>
                                <div style="font-size: 24px; font-weight: bold; color: #FF6600;">{total_accounts}</div>
                            </div>
                            <div>
                                <div style="font-size: 12px; color: #AAA;">Active Accounts</div>
                                <div style="font-size: 24px; font-weight: bold; color: #FF6600;">{active_accounts}</div>
                            </div>
                            <div>
                                <div style="font-size: 12px; color: #AAA;">Banned Accounts</div>
                                <div style="font-size: 24px; font-weight: bold; color: #F44336;">{banned_accounts}</div>
                            </div>
                            <div>
                                <div style="font-size: 12px; color: #AAA;">New Today</div>
                                <div style="font-size: 24px; font-weight: bold; color: #4CAF50;">{new_today}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-panel" style="flex: 1;">
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE;">Search & Filter</div>
                        <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                            <input type="text" id="search-input" class="form-input" placeholder="Search by number, email, name..." style="flex: 1;">
                            <button id="search-button" class="form-button">Search</button>
                        </div>
                        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                            <select id="status-filter" class="form-select" style="width: auto;">
                                <option value="all">All Statuses</option>
                                <option value="active">Active</option>
                                <option value="banned">Banned</option>
                                <option value="flagged">Flagged</option>
                                <option value="new">New</option>
                            </select>
                            <select id="area-code-filter" class="form-select" style="width: auto;">
                                {area_code_options_html}
                            </select>
                            <select id="age-filter" class="form-select" style="width: auto;">
                                <option value="all">All Ages</option>
                                <option value="new">New (< 7 days)</option>
                                <option value="week">7-30 days</option>
                                <option value="month">30-90 days</option>
                                <option value="old">> 90 days</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <div class="form-panel">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <div style="font-size: 16px; font-weight: bold; color: #EEE;">Account List</div>
                        <div>
                            <button class="form-button secondary-button">Export CSV</button>
                            <button class="form-button secondary-button">Bulk Actions</button>
                            <a href="/creator" class="form-button">Create New</a>
                        </div>
                    </div>
                    
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th style="width: 20px;"><input type="checkbox"></th>
                                <th>Phone Number</th>
                                <th>User Info</th>
                                <th>Area Code</th>
                                <th>Created</th>
                                <th>Last Activity</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="accounts-table-body">
                            {account_rows_html}
                        </tbody>
                    </table>
                    
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px;">
                        <div style="color: #CCC; font-size: 14px;">Showing {len(accounts)} of {total_accounts} accounts</div>
                        <div>
                            <button class="form-button secondary-button" disabled>Previous</button>
                            <button class="form-button secondary-button">Next</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <script>
            // Add filter functionality
            document.addEventListener('DOMContentLoaded', function() {
                const searchButton = document.getElementById('search-button');
                const searchInput = document.getElementById('search-input');
                const statusFilter = document.getElementById('status-filter');
                const areaCodeFilter = document.getElementById('area-code-filter');
                const ageFilter = document.getElementById('age-filter');
                
                if (searchButton) {
                    searchButton.addEventListener('click', function() {
                        // In a complete version, this would make an AJAX request to fetch filtered accounts
                        const searchTerm = searchInput.value;
                        const status = statusFilter.value;
                        const areaCode = areaCodeFilter.value;
                        const age = ageFilter.value;
                        
                        showStatusMessage(`Searching for: "${searchTerm}" (Status: ${status}, Area: ${areaCode}, Age: ${age})`, 'success');
                    });
                }
            });
        </script>
        '''
    )

@app.route('/campaigns')
def campaigns_page():
    """The campaigns management page with real data"""
    process_assets()
    
    # Get campaigns from database
    campaign_data = get_campaigns(limit=10)
    campaigns = campaign_data['campaigns']
    total_campaigns = campaign_data['total']
    
    # Build the campaign rows HTML
    campaign_rows_html = ''
    for campaign in campaigns:
        status_class = ''
        if campaign['status'] == 'active':
            status_class = 'status-active'
        elif campaign['status'] == 'completed':
            status_class = 'status-neutral'
        elif campaign['status'] == 'paused':
            status_class = 'status-warning'
        elif campaign['status'] == 'draft':
            status_class = 'status-neutral'
        elif campaign['status'] == 'error':
            status_class = 'status-danger'
        else:
            status_class = 'status-neutral'
        
        campaign_rows_html += f'''
            <tr data-campaign-id="{campaign['id']}">
                <td>{campaign['name']}</td>
                <td>{campaign['description'][:50]}{'...' if len(campaign['description'] or '') > 50 else ''}</td>
                <td>{campaign['start_date']}</td>
                <td>{campaign['end_date']}</td>
                <td><span class="status-badge {status_class}">{campaign['status'].capitalize()}</span></td>
                <td>
                    <button class="form-button secondary-button">Edit</button>
                    <button class="form-button secondary-button">Clone</button>
                    <button class="form-button">View Results</button>
                </td>
            </tr>
        '''
    
    # If no campaigns found, show empty state
    if not campaigns:
        campaign_rows_html = '''
            <tr>
                <td colspan="6">
                    <div class="empty-state">
                        <div class="empty-state-icon">🚀</div>
                        <div class="empty-state-title">No Campaigns Yet</div>
                        <div class="empty-state-text">Create your first campaign to start sending messages at scale.</div>
                        <button class="form-button">Create Campaign</button>
                    </div>
                </td>
            </tr>
        '''
    
    return render_template_string(
        BASE_HTML,
        title="Campaigns",
        active_page="/campaigns",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div class="form-panel">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <div style="font-size: 16px; font-weight: bold; color: #EEE;">Campaign Management</div>
                        <div>
                            <button class="form-button">Create New Campaign</button>
                        </div>
                    </div>
                    
                    <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 20px;">
                        <div style="background-color: #333; padding: 15px; border-radius: 6px; min-width: 180px; text-align: center;">
                            <div style="font-size: 22px; font-weight: bold; color: #FF6600;">{total_campaigns}</div>
                            <div style="color: #AAA; margin-top: 5px;">Total Campaigns</div>
                        </div>
                        
                        <div style="background-color: #333; padding: 15px; border-radius: 6px; min-width: 180px; text-align: center;">
                            <div style="font-size: 22px; font-weight: bold; color: #4CAF50;">0</div>
                            <div style="color: #AAA; margin-top: 5px;">Active</div>
                        </div>
                        
                        <div style="background-color: #333; padding: 15px; border-radius: 6px; min-width: 180px; text-align: center;">
                            <div style="font-size: 22px; font-weight: bold; color: #FFC107;">0</div>
                            <div style="color: #AAA; margin-top: 5px;">Scheduled</div>
                        </div>
                        
                        <div style="background-color: #333; padding: 15px; border-radius: 6px; min-width: 180px; text-align: center;">
                            <div style="font-size: 22px; font-weight: bold; color: #CCC;">0</div>
                            <div style="color: #AAA; margin-top: 5px;">Completed</div>
                        </div>
                    </div>
                </div>
                
                <div class="form-panel">
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th>Campaign Name</th>
                                <th>Description</th>
                                <th>Start Date</th>
                                <th>End Date</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {campaign_rows_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        '''
    )

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/api/device/status')
def device_status():
    """Mock API for device status - would be replaced with real Proxidize integration"""
    # In a real implementation, this would query Proxidize for actual status
    return jsonify({
        'connected': False,
        'ip': 'N/A',
        'country': 'Unknown',
        'region': 'Unknown',
        'proxy_type': 'None',
        'last_rotation': 'N/A'
    })

if __name__ == '__main__':
    # Make sure static directory exists
    os.makedirs('static', exist_ok=True)
    
    # Process assets
    process_assets()
    
    print("============================================================")
    print("TEXTNOW MAX - ACCOUNT CREATOR & CAMPAIGN MANAGER")
    print("============================================================")
    print("Access the application in your web browser at: http://localhost:5000")
    print("Advanced automation platform for TextNow messaging with account creation")
    print("and campaign management for 100,000+ messages in 8am-8pm window.")
    print("============================================================")
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)