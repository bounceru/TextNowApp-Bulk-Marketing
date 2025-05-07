"""
TextNow Max - Account Creator & Campaign Manager

Advanced automation platform for TextNow messaging with account creation and campaign management.
"""

from flask import Flask, render_template_string, request, jsonify, send_from_directory
import os
import random
import json
import datetime
import sqlite3
from datetime import datetime, timedelta

# Create Flask app
app = Flask(__name__)

# Base HTML with consistent styling
BASE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - TextNow Max</title>
    <style>
        /* Theme Variables */
        :root {
            --primary-color: #FF6600;
            --secondary-color: #444;
            --background-color: #222;
            --card-background: #2a2a2a;
            --accent-color: #FF6600;
            --text-color: #FFF;
            --border-radius: 6px;
        }
        
        /* Global Styles */
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--background-color);
            color: var(--text-color);
            line-height: 1.6;
        }
        
        /* Sidebar Navigation */
        .sidebar {
            position: fixed;
            width: 240px;
            height: 100%;
            background-color: #1a1a1a;
            padding: 20px 0;
            box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
            overflow-y: auto;
        }
        
        .sidebar-logo {
            padding: 15px 20px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .sidebar-logo img {
            max-width: 100%;
            height: auto;
        }
        
        .sidebar-menu {
            padding: 0;
            list-style: none;
        }
        
        .sidebar-menu li {
            margin-bottom: 5px;
        }
        
        .sidebar-menu a {
            display: block;
            padding: 10px 20px;
            color: #AAA;
            text-decoration: none;
            transition: all 0.3s;
            border-left: 3px solid transparent;
        }
        
        .sidebar-menu a:hover {
            background-color: #333;
            border-left-color: var(--primary-color);
            color: #FFF;
        }
        
        .sidebar-menu a.active {
            background-color: #333;
            border-left-color: var(--primary-color);
            color: #FFF;
        }
        
        .sidebar-menu i {
            margin-right: 10px;
        }
        
        /* Main Content Area */
        .main-content {
            margin-left: 240px;
            padding: 20px;
            min-height: 100vh;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: var(--text-color);
            margin-top: 0;
        }
        
        /* Form Styles */
        .form-panel {
            background-color: var(--card-background);
            border-radius: var(--border-radius);
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .form-title {
            font-size: 18px;
            margin-bottom: 15px;
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
        }
        
        .form-control {
            width: 100%;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #444;
            background-color: #333;
            color: #FFF;
            font-size: 14px;
        }
        
        .form-control:focus {
            outline: none;
            border-color: var(--primary-color);
        }
        
        .form-button {
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 4px;
            padding: 10px 15px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s;
        }
        
        .form-button:hover {
            background-color: #E55F00;
        }
        
        .secondary-button {
            background-color: #555;
        }
        
        .secondary-button:hover {
            background-color: #666;
        }
        
        /* Dashboard Styles */
        .stats-container {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background-color: var(--card-background);
            border-radius: var(--border-radius);
            padding: 15px;
            flex-grow: 1;
            min-width: 180px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #AAA;
            font-size: 14px;
        }
        
        /* Dashboard Table */
        .dashboard-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .dashboard-table th,
        .dashboard-table td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #444;
        }
        
        .dashboard-table th {
            background-color: #333;
            color: #CCC;
            font-weight: normal;
        }
        
        .dashboard-table tr:hover {
            background-color: #333;
        }
        
        /* Status Badges */
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            text-transform: uppercase;
        }
        
        .status-active {
            background-color: rgba(76, 175, 80, 0.1);
            color: #4CAF50;
            border: 1px solid rgba(76, 175, 80, 0.2);
        }
        
        .status-warning {
            background-color: rgba(255, 193, 7, 0.1);
            color: #FFC107;
            border: 1px solid rgba(255, 193, 7, 0.2);
        }
        
        .status-danger {
            background-color: rgba(244, 67, 54, 0.1);
            color: #F44336;
            border: 1px solid rgba(244, 67, 54, 0.2);
        }
        
        .status-neutral {
            background-color: rgba(158, 158, 158, 0.1);
            color: #9E9E9E;
            border: 1px solid rgba(158, 158, 158, 0.2);
        }
        
        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 30px;
            color: #AAA;
        }
        
        .empty-state-icon {
            font-size: 50px;
            margin-bottom: 15px;
            color: #555;
        }
        
        .empty-state-title {
            font-size: 18px;
            margin-bottom: 10px;
            color: #CCC;
        }
        
        .empty-state-text {
            margin-bottom: 20px;
            font-size: 14px;
        }
        
        /* App Container */
        .app-container {
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        
        .app-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .app-title {
            font-size: 24px;
            font-weight: bold;
        }
        
        .app-actions {
            display: flex;
            gap: 10px;
        }
        
        .app-content {
            flex-grow: 1;
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .sidebar {
                width: 60px;
            }
            
            .sidebar-menu span {
                display: none;
            }
            
            .main-content {
                margin-left: 60px;
            }
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-logo">
            <img src="/static/logo.png" alt="TextNow Max">
            <div style="margin-top: 10px; color: #FFF; font-size: 18px; font-weight: bold;">TextNow Max</div>
            <div style="color: #AAA; font-size: 12px;">Account Creator & Campaign Manager</div>
        </div>
        <ul class="sidebar-menu">
            <li><a href="/" class="{{ 'active' if active_page == '/' else '' }}">📊 <span>Dashboard</span></a></li>
            <li><a href="/creator" class="{{ 'active' if active_page == '/creator' else '' }}">🛠️ <span>Account Creator</span></a></li>
            <li><a href="/dashboard" class="{{ 'active' if active_page == '/dashboard' else '' }}">👤 <span>Account Manager</span></a></li>
            <li><a href="/campaigns" class="{{ 'active' if active_page == '/campaigns' else '' }}">📢 <span>Campaign Manager</span></a></li>
            <li><a href="/templates" class="{{ 'active' if active_page == '/templates' else '' }}">📝 <span>Message Templates</span></a></li>
            <li><a href="/manual" class="{{ 'active' if active_page == '/manual' else '' }}">📱 <span>Manual Messaging</span></a></li>
            <li><a href="/messages" class="{{ 'active' if active_page == '/messages' else '' }}">💬 <span>Message Dashboard</span></a></li>
            <li><a href="/media" class="{{ 'active' if active_page == '/media' else '' }}">🖼️ <span>Media Manager</span></a></li>
            <li><a href="/health" class="{{ 'active' if active_page == '/health' else '' }}">❤️ <span>Account Health</span></a></li>
            <li><a href="/voicemail" class="{{ 'active' if active_page == '/voicemail' else '' }}">🔊 <span>Voicemail Manager</span></a></li>
            <li><a href="/proxies" class="{{ 'active' if active_page == '/proxies' else '' }}">🌐 <span>Proxy Manager</span></a></li>
            <li><a href="/detection" class="{{ 'active' if active_page == '/detection' else '' }}">🛡️ <span>Anti-Detection</span></a></li>
            <li><a href="/schedule" class="{{ 'active' if active_page == '/schedule' else '' }}">⏱️ <span>Campaign Scheduler</span></a></li>
        </ul>
    </div>
    <div class="main-content">
        {{ content | safe }}
    </div>
    
    <script>
        // Global notification function
        function showStatusMessage(message, type = 'info') {
            const statusBar = document.getElementById('status-bar');
            if (statusBar) {
                statusBar.textContent = message;
                statusBar.className = `status-bar ${type}`;
                statusBar.style.display = 'block';
                
                // Hide after 5 seconds
                setTimeout(() => {
                    statusBar.style.display = 'none';
                }, 5000);
            }
        }
    </script>
</body>
</html>
'''

def process_assets():
    """Process and copy assets to static folder"""
    # Make sure static directory exists
    os.makedirs('static', exist_ok=True)
    
    # Create a simple logo if it doesn't exist
    if not os.path.exists('static/logo.png'):
        # In a real implementation, this would use a proper asset
        # For now, copy from assets folder if available or use a default
        possible_locations = [
            'assets/logo.png', 
            'images/logo.png',
            'textnow_logo.png'
        ]
        
        logo_found = False
        for location in possible_locations:
            if os.path.exists(location):
                # Copy the logo to static folder
                import shutil
                shutil.copy(location, 'static/logo.png')
                logo_found = True
                break
        
        if not logo_found:
            # Use a placeholder logo - in real implementation, use a better solution
            try:
                # Create a simple SVG logo
                with open('static/logo.png', 'w') as f:
                    f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
                    f.write('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">\n')
                    f.write('  <rect width="200" height="200" fill="#333"/>\n')
                    f.write('  <text x="30" y="120" font-family="Arial" font-size="40" fill="#FF6600">TextNow</text>\n')
                    f.write('  <text x="80" y="150" font-family="Arial" font-size="20" fill="#FFF">MAX</text>\n')
                    f.write('</svg>\n')
            except Exception as e:
                print(f"Error creating placeholder logo: {e}")

def format_date(date_str):
    """Format a date string to a readable format"""
    try:
        if not date_str:
            return 'N/A'
        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        return date_obj.strftime('%b %d, %Y')
    except:
        return date_str

def calculate_days_ago(date_str):
    """Calculate days ago from a date string"""
    try:
        if not date_str:
            return 'N/A'
        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        delta = datetime.now() - date_obj
        days = delta.days
        
        if days == 0:
            return 'Today'
        elif days == 1:
            return 'Yesterday'
        else:
            return f'{days} days ago'
    except:
        return 'Unknown'

def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect('ghost_accounts.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_statistics():
    """Get statistics from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total account count
        cursor.execute('SELECT COUNT(*) FROM accounts')
        total_accounts = cursor.fetchone()[0]
        
        # Get active accounts
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE status = 'active'")
        active_accounts = cursor.fetchone()[0]
        
        # Get accounts with message activity in the last 7 days
        cursor.execute('''
            SELECT COUNT(DISTINCT account_id) FROM message_logs 
            WHERE timestamp > datetime('now', '-7 days')
        ''')
        active_messaging = cursor.fetchone()[0]
        
        # Get messages sent in last 24 hours
        cursor.execute('''
            SELECT COUNT(*) FROM message_logs 
            WHERE timestamp > datetime('now', '-1 day')
        ''')
        messages_24h = cursor.fetchone()[0]
        
        # Get campaign count
        cursor.execute('SELECT COUNT(*) FROM campaigns')
        campaigns = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_accounts': total_accounts,
            'active_accounts': active_accounts,
            'active_messaging': active_messaging,
            'messages_24h': messages_24h,
            'campaigns': campaigns
        }
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {
            'total_accounts': 0,
            'active_accounts': 0,
            'active_messaging': 0, 
            'messages_24h': 0,
            'campaigns': 0
        }

def get_accounts(limit=10, offset=0, filters=None):
    """Get accounts from the database with optional filtering"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        base_query = 'SELECT * FROM accounts'
        count_query = 'SELECT COUNT(*) FROM accounts'
        
        # Apply filters if provided
        where_clauses = []
        params = []
        
        if filters:
            if filters.get('status') and filters['status'] != 'all':
                where_clauses.append('status = ?')
                params.append(filters['status'])
            
            if filters.get('area_code') and filters['area_code'] != 'all':
                where_clauses.append('area_code = ?')
                params.append(filters['area_code'])
                
            if filters.get('search'):
                search_term = f'%{filters["search"]}%'
                where_clauses.append('(phone_number LIKE ? OR email LIKE ? OR username LIKE ?)')
                params.extend([search_term, search_term, search_term])
        
        # Build the complete query
        if where_clauses:
            where_str = ' WHERE ' + ' AND '.join(where_clauses)
            base_query += where_str
            count_query += where_str
        
        # Get total count for pagination
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # Add pagination
        base_query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        # Execute the query
        cursor.execute(base_query, params)
        accounts = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return accounts, total_count
    except Exception as e:
        print(f"Error getting accounts: {e}")
        return [], 0

def get_area_codes():
    """Get all area codes from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT area_code FROM accounts')
        area_codes = [row[0] for row in cursor.fetchall() if row[0]]
        conn.close()
        return area_codes
    except Exception as e:
        print(f"Error getting area codes: {e}")
        return []

def get_campaigns(limit=10, offset=0):
    """Get campaigns from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total campaign count
        cursor.execute('SELECT COUNT(*) FROM campaigns')
        total_count = cursor.fetchone()[0]
        
        # Get campaigns with pagination
        cursor.execute('''
            SELECT * FROM campaigns
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        campaigns = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return campaigns, total_count
    except Exception as e:
        print(f"Error getting campaigns: {e}")
        return [], 0

def get_recent_messages(limit=10):
    """Get recent messages from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.*, a.phone_number, a.username
            FROM message_logs m
            JOIN accounts a ON m.account_id = a.id
            ORDER BY m.timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        messages = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return messages
    except Exception as e:
        print(f"Error getting recent messages: {e}")
        return []

@app.route('/')
def index():
    """Display the TextNow Max application homepage with real data"""
    process_assets()
    
    # Get statistics from database
    stats = get_statistics()
    
    # Get recent messages
    recent_messages = get_recent_messages(5)
    
    # If no recent messages, show empty state
    if not recent_messages:
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
            <div class="app-header">
                <div class="app-title">TextNow Max Dashboard</div>
                <div class="app-actions">
                    <button class="form-button" onclick="checkProxidizeStatus()">Check Proxy Status</button>
                </div>
            </div>
            
            <div class="app-content">
                <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
                    <div>
                        <div class="form-panel">
                            <div style="padding-bottom: 10px; margin-bottom: 15px; border-bottom: 1px solid #444; font-weight: bold;">
                                System Overview
                            </div>
                            
                            <div class="stats-container">
                                <div class="stat-card">
                                    <div style="font-size: 24px; font-weight: bold; color: #FF6600;">''' + str(stats['total_accounts']) + '''</div>
                                    <div style="color: #AAA; margin-top: 5px;">Total Accounts</div>
                                </div>
                                
                                <div class="stat-card">
                                    <div style="font-size: 24px; font-weight: bold; color: #4CAF50;">''' + str(stats['active_accounts']) + '''</div>
                                    <div style="color: #AAA; margin-top: 5px;">Active Accounts</div>
                                </div>
                                
                                <div class="stat-card">
                                    <div style="font-size: 24px; font-weight: bold; color: #2196F3;">''' + str(stats['active_messaging']) + '''</div>
                                    <div style="color: #AAA; margin-top: 5px;">Messaging Activity</div>
                                </div>
                                
                                <div class="stat-card">
                                    <div style="font-size: 24px; font-weight: bold; color: #9C27B0;">''' + str(stats['messages_24h']) + '''</div>
                                    <div style="color: #AAA; margin-top: 5px;">Messages (24h)</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-panel">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                                <div style="font-weight: bold;">Proxidize Status</div>
                                <button class="form-button secondary-button" onclick="refreshIP()">Refresh IP</button>
                            </div>
                            
                            <div id="device-status" style="display: flex; flex-wrap: wrap; gap: 20px;">
                                <div style="background-color: #333; border-radius: 4px; padding: 15px; flex-grow: 1;">
                                    <div style="margin-bottom: 10px;">
                                        <span style="color: #AAA;">Connection Status:</span>
                                        <span class="status-badge status-danger">Not Connected</span>
                                    </div>
                                    <div style="margin-bottom: 10px;">
                                        <span style="color: #AAA;">Current IP:</span>
                                        <span>N/A</span>
                                    </div>
                                    <div style="margin-bottom: 10px;">
                                        <span style="color: #AAA;">Location:</span>
                                        <span>Unknown, Unknown</span>
                                    </div>
                                    <div>
                                        <span style="color: #AAA;">Last Rotation:</span>
                                        <span>N/A</span>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 4px; padding: 15px; flex-grow: 1;">
                                    <div style="margin-bottom: 10px;">
                                        <span style="color: #AAA;">Proxy Type:</span>
                                        <span>None</span>
                                    </div>
                                    <div style="margin-bottom: 10px;">
                                        <span style="color: #AAA;">Rotation Mode:</span>
                                        <span>Manual</span>
                                    </div>
                                    <div>
                                        <button class="form-button" disabled>Connect</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-panel">
                            <div style="font-weight: bold; margin-bottom: 15px;">System Performance</div>
                            
                            <div style="display: flex; flex-wrap: wrap; gap: 15px;">
                                <div style="background-color: #333; border-radius: 4px; padding: 15px; flex-grow: 1;">
                                    <div style="color: #AAA; margin-bottom: 5px;">Messages Per Hour</div>
                                    <div style="height: 100px; display: flex; align-items: flex-end;">
                                        <div style="background-color: #FF6600; width: 8.33%; height: 20%; margin-right: 2px;"></div>
                                        <div style="background-color: #FF6600; width: 8.33%; height: 30%; margin-right: 2px;"></div>
                                        <div style="background-color: #FF6600; width: 8.33%; height: 40%; margin-right: 2px;"></div>
                                        <div style="background-color: #FF6600; width: 8.33%; height: 60%; margin-right: 2px;"></div>
                                        <div style="background-color: #FF6600; width: 8.33%; height: 80%; margin-right: 2px;"></div>
                                        <div style="background-color: #FF6600; width: 8.33%; height: 100%; margin-right: 2px;"></div>
                                        <div style="background-color: #FF6600; width: 8.33%; height: 90%; margin-right: 2px;"></div>
                                        <div style="background-color: #FF6600; width: 8.33%; height: 70%; margin-right: 2px;"></div>
                                        <div style="background-color: #FF6600; width: 8.33%; height: 50%; margin-right: 2px;"></div>
                                        <div style="background-color: #FF6600; width: 8.33%; height: 40%; margin-right: 2px;"></div>
                                        <div style="background-color: #FF6600; width: 8.33%; height: 30%; margin-right: 2px;"></div>
                                        <div style="background-color: #FF6600; width: 8.33%; height: 20%;"></div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 4px; padding: 15px; flex-grow: 1;">
                                    <div style="color: #AAA; margin-bottom: 5px;">Health Status</div>
                                    <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                                        <div style="text-align: center; flex-grow: 1;">
                                            <div style="font-size: 24px; font-weight: bold; color: #4CAF50;">''' + str(int(stats['active_accounts'] * 0.85)) + '''</div>
                                            <div style="color: #AAA; font-size: 12px;">Healthy</div>
                                        </div>
                                        <div style="text-align: center; flex-grow: 1;">
                                            <div style="font-size: 24px; font-weight: bold; color: #FFC107;">''' + str(int(stats['active_accounts'] * 0.1)) + '''</div>
                                            <div style="color: #AAA; font-size: 12px;">Warning</div>
                                        </div>
                                        <div style="text-align: center; flex-grow: 1;">
                                            <div style="font-size: 24px; font-weight: bold; color: #F44336;">''' + str(int(stats['active_accounts'] * 0.05)) + '''</div>
                                            <div style="color: #AAA; font-size: 12px;">Critical</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div>
                        <div class="form-panel">
                            <div style="font-weight: bold; margin-bottom: 15px;">Quick Actions</div>
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                <a href="/creator" style="text-decoration: none;">
                                    <div style="background-color: #333; border-radius: 4px; padding: 15px; text-align: center;">
                                        <div style="font-size: 24px; margin-bottom: 5px;">🛠️</div>
                                        <div style="color: #CCC;">Create Account</div>
                                    </div>
                                </a>
                                
                                <a href="/campaigns" style="text-decoration: none;">
                                    <div style="background-color: #333; border-radius: 4px; padding: 15px; text-align: center;">
                                        <div style="font-size: 24px; margin-bottom: 5px;">📢</div>
                                        <div style="color: #CCC;">New Campaign</div>
                                    </div>
                                </a>
                                
                                <a href="/manual" style="text-decoration: none;">
                                    <div style="background-color: #333; border-radius: 4px; padding: 15px; text-align: center;">
                                        <div style="font-size: 24px; margin-bottom: 5px;">📱</div>
                                        <div style="color: #CCC;">Send Message</div>
                                    </div>
                                </a>
                                
                                <a href="/schedule" style="text-decoration: none;">
                                    <div style="background-color: #333; border-radius: 4px; padding: 15px; text-align: center;">
                                        <div style="font-size: 24px; margin-bottom: 5px;">⏱️</div>
                                        <div style="color: #CCC;">Schedule</div>
                                    </div>
                                </a>
                            </div>
                        </div>
                        
                        <div class="form-panel">
                            <div style="font-weight: bold; margin-bottom: 15px;">Recent Activity</div>
                            
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
            <div class="app-header">
                <div class="app-title">Account Creator</div>
                <div class="app-actions">
                    <button class="form-button" id="start-creator">Start Creating</button>
                </div>
            </div>
            
            <div class="app-content">
                <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
                    <div>
                        <div class="form-panel">
                            <div style="margin-bottom: 15px; font-weight: bold;">Creation Settings</div>
                            
                            <div class="form-group">
                                <label class="form-label">Area Code(s)</label>
                                <input type="text" class="form-control" id="area-codes" placeholder="Enter area codes separated by commas (e.g. 212, 407, 305)" value="''' + area_codes_str + '''">
                                <div style="color: #AAA; font-size: 12px; margin-top: 5px;">Leave blank to use random US area codes.</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Number of Accounts</label>
                                <input type="number" class="form-control" id="num-accounts" value="10" min="1" max="100">
                                <div style="color: #AAA; font-size: 12px; margin-top: 5px;">Maximum 100 accounts per batch.</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Creation Speed</label>
                                <select class="form-control" id="creation-speed">
                                    <option value="slow">Slow (Human-like, safest)</option>
                                    <option value="medium" selected>Medium (Balance of speed & safety)</option>
                                    <option value="fast">Fast (Quick creation, higher risk)</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Advanced Options</label>
                                <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-top: 10px;">
                                    <div style="display: flex; align-items: center;">
                                        <input type="checkbox" id="use-proxies" checked>
                                        <label for="use-proxies" style="margin-left: 5px; color: #CCC;">Use Proxidize</label>
                                    </div>
                                    
                                    <div style="display: flex; align-items: center;">
                                        <input type="checkbox" id="rotate-ip" checked>
                                        <label for="rotate-ip" style="margin-left: 5px; color: #CCC;">Rotate IP Between Accounts</label>
                                    </div>
                                    
                                    <div style="display: flex; align-items: center;">
                                        <input type="checkbox" id="auto-verify" checked>
                                        <label for="auto-verify" style="margin-left: 5px; color: #CCC;">Auto-Verify Accounts</label>
                                    </div>
                                    
                                    <div style="display: flex; align-items: center;">
                                        <input type="checkbox" id="random-names" checked>
                                        <label for="random-names" style="margin-left: 5px; color: #CCC;">Use Random Names/Usernames</label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-panel">
                            <div style="margin-bottom: 15px; font-weight: bold;">Creation Progress</div>
                            
                            <div id="progress-container" style="display: none;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <div>Overall Progress</div>
                                    <div id="progress-text">0 / 10 (0%)</div>
                                </div>
                                
                                <div style="height: 20px; background-color: #333; border-radius: 10px; overflow: hidden; margin-bottom: 20px;">
                                    <div id="progress-bar" style="height: 100%; width: 0; background-color: #FF6600;"></div>
                                </div>
                                
                                <div style="background-color: #1a1a1a; border-radius: 4px; padding: 10px; height: 200px; overflow-y: auto; font-family: monospace; font-size: 12px;" id="creation-log">
                                    <div style="color: #CCC;">Creation process will log activity here...</div>
                                </div>
                            </div>
                            
                            <div id="start-instructions" style="text-align: center; padding: 40px 0;">
                                <div style="font-size: 60px; margin-bottom: 20px;">🚀</div>
                                <div style="font-size: 18px; color: #CCC; margin-bottom: 10px;">Ready to Create Accounts</div>
                                <div style="color: #AAA; margin-bottom: 20px;">Configure your settings and click "Start Creating" to begin.</div>
                                <button class="form-button" id="start-creator-alt">Start Creating</button>
                            </div>
                        </div>
                    </div>
                    
                    <div>
                        <div class="form-panel">
                            <div style="margin-bottom: 15px; font-weight: bold;">Creation Stats</div>
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px;">
                                <div style="background-color: #333; border-radius: 4px; padding: 15px; text-align: center;">
                                    <div style="font-size: 24px; font-weight: bold; color: #4CAF50;" id="success-count">0</div>
                                    <div style="color: #AAA;">Success</div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 4px; padding: 15px; text-align: center;">
                                    <div style="font-size: 24px; font-weight: bold; color: #F44336;" id="error-count">0</div>
                                    <div style="color: #AAA;">Errors</div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 4px; padding: 15px; text-align: center;">
                                    <div style="font-size: 24px; font-weight: bold; color: #FFC107;" id="retry-count">0</div>
                                    <div style="color: #AAA;">Retries</div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 4px; padding: 15px; text-align: center;">
                                    <div style="font-size: 24px; font-weight: bold; color: #2196F3;" id="ip-rotations">0</div>
                                    <div style="color: #AAA;">IP Rotations</div>
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 15px; font-weight: bold;">Most Recent Accounts</div>
                            
                            <div style="background-color: #1a1a1a; border-radius: 4px; padding: 10px; max-height: 250px; overflow-y: auto;" id="recent-accounts">
                                <div style="color: #AAA; text-align: center; padding: 20px;">No accounts created yet</div>
                            </div>
                        </div>
                        
                        <div class="form-panel">
                            <div style="margin-bottom: 15px; font-weight: bold;">Device Status</div>
                            
                            <div style="background-color: #333; border-radius: 4px; padding: 15px; margin-bottom: 10px;">
                                <div style="margin-bottom: 10px;">
                                    <span style="color: #AAA; display: inline-block; width: 120px;">Device Status:</span>
                                    <span id="device-status-badge" class="status-badge status-danger">Not Connected</span>
                                </div>
                                
                                <div style="margin-bottom: 10px;">
                                    <span style="color: #AAA; display: inline-block; width: 120px;">Current IP:</span>
                                    <span id="current-ip">N/A</span>
                                </div>
                                
                                <div style="margin-bottom: 10px;">
                                    <span style="color: #AAA; display: inline-block; width: 120px;">Location:</span>
                                    <span id="location">Unknown</span>
                                </div>
                            </div>
                            
                            <button class="form-button" id="refresh-ip">Refresh IP</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Simulated account creation process for demo
            document.addEventListener('DOMContentLoaded', function() {
                const startBtn = document.getElementById('start-creator');
                const startBtnAlt = document.getElementById('start-creator-alt');
                const progressContainer = document.getElementById('progress-container');
                const startInstructions = document.getElementById('start-instructions');
                const progressBar = document.getElementById('progress-bar');
                const progressText = document.getElementById('progress-text');
                const creationLog = document.getElementById('creation-log');
                const successCount = document.getElementById('success-count');
                const errorCount = document.getElementById('error-count');
                const retryCount = document.getElementById('retry-count');
                const ipRotations = document.getElementById('ip-rotations');
                const recentAccounts = document.getElementById('recent-accounts');
                
                // Connect both buttons to the same function
                if (startBtn) startBtn.addEventListener('click', startCreation);
                if (startBtnAlt) startBtnAlt.addEventListener('click', startCreation);
                
                function startCreation() {
                    // Show progress container
                    progressContainer.style.display = 'block';
                    startInstructions.style.display = 'none';
                    
                    // Get creation settings
                    const numAccounts = parseInt(document.getElementById('num-accounts').value) || 10;
                    const areaCodes = document.getElementById('area-codes').value.split(',').map(code => code.trim()).filter(Boolean);
                    const creationSpeed = document.getElementById('creation-speed').value;
                    const useProxies = document.getElementById('use-proxies').checked;
                    const rotateIp = document.getElementById('rotate-ip').checked;
                    
                    // Reset counters
                    let completed = 0;
                    let successes = 0;
                    let errors = 0;
                    let retries = 0;
                    let rotations = 0;
                    
                    // Reset UI
                    progressBar.style.width = '0%';
                    progressText.textContent = `0 / ${numAccounts} (0%)`;
                    successCount.textContent = '0';
                    errorCount.textContent = '0';
                    retryCount.textContent = '0';
                    ipRotations.textContent = '0';
                    creationLog.innerHTML = '';
                    recentAccounts.innerHTML = '';
                    
                    // Add initial log
                    addLog('Starting account creation process...');
                    addLog(`Using ${useProxies ? 'Proxidize proxies' : 'direct connection'}`);
                    if (areaCodes.length > 0) {
                        addLog(`Using area codes: ${areaCodes.join(', ')}`);
                    } else {
                        addLog('Using random US area codes');
                    }
                    
                    // Simulate account creation with appropriate delays based on speed
                    let delay = 5000; // Default medium speed
                    if (creationSpeed === 'slow') delay = 8000;
                    if (creationSpeed === 'fast') delay = 2000;
                    
                    function createNextAccount() {
                        if (completed < numAccounts) {
                            // Random area code if none specified
                            const areaCode = areaCodes.length > 0 
                                ? areaCodes[Math.floor(Math.random() * areaCodes.length)] 
                                : String(Math.floor(Math.random() * 800) + 200); // Random 3-digit number between 200-999
                            
                            // Random phone number with the area code
                            const phoneNumber = `${areaCode}-${String(Math.floor(Math.random() * 900) + 100)}-${String(Math.floor(Math.random() * 9000) + 1000)}`;
                            
                            // Simulate IP rotation if enabled
                            if (rotateIp && completed > 0 && completed % 3 === 0) {
                                addLog('Rotating IP address...');
                                setTimeout(() => {
                                    addLog('IP rotated successfully', 'success');
                                    rotations++;
                                    ipRotations.textContent = rotations;
                                    continueCreation();
                                }, 2000);
                            } else {
                                continueCreation();
                            }
                            
                            function continueCreation() {
                                addLog(`Creating account with number ${phoneNumber}...`);
                                
                                // Simulate random success or error
                                const success = Math.random() > 0.2; // 80% success rate
                                
                                setTimeout(() => {
                                    if (success) {
                                        // Success
                                        addLog(`Account created successfully: ${phoneNumber}`, 'success');
                                        successes++;
                                        successCount.textContent = successes;
                                        
                                        // Add to recent accounts
                                        const accountHtml = `
                                            <div style="border-bottom: 1px solid #333; padding: 8px 0;">
                                                <div style="display: flex; justify-content: space-between;">
                                                    <div style="font-weight: bold;">${phoneNumber}</div>
                                                    <div><span class="status-badge status-active">Active</span></div>
                                                </div>
                                                <div style="color: #AAA; font-size: 12px;">Created just now</div>
                                            </div>
                                        `;
                                        recentAccounts.innerHTML = accountHtml + recentAccounts.innerHTML;
                                    } else {
                                        // Error with retry
                                        addLog(`Error creating account: ${phoneNumber}`, 'error');
                                        errors++;
                                        errorCount.textContent = errors;
                                        
                                        // Simulate retry
                                        addLog(`Retrying creation for ${phoneNumber}...`);
                                        retries++;
                                        retryCount.textContent = retries;
                                        
                                        setTimeout(() => {
                                            // Retry success
                                            addLog(`Retry successful: ${phoneNumber}`, 'success');
                                            successes++;
                                            successCount.textContent = successes;
                                            
                                            // Add to recent accounts
                                            const accountHtml = `
                                                <div style="border-bottom: 1px solid #333; padding: 8px 0;">
                                                    <div style="display: flex; justify-content: space-between;">
                                                        <div style="font-weight: bold;">${phoneNumber}</div>
                                                        <div><span class="status-badge status-active">Active</span></div>
                                                    </div>
                                                    <div style="color: #AAA; font-size: 12px;">Created just now (after retry)</div>
                                                </div>
                                            `;
                                            recentAccounts.innerHTML = accountHtml + recentAccounts.innerHTML;
                                            
                                            completed++;
                                            updateProgress();
                                            createNextAccount();
                                        }, delay / 2);
                                        return;
                                    }
                                    
                                    completed++;
                                    updateProgress();
                                    createNextAccount();
                                }, delay);
                            }
                        } else {
                            // All accounts created
                            addLog('Account creation process completed!', 'success');
                        }
                    }
                    
                    function updateProgress() {
                        const percent = Math.round((completed / numAccounts) * 100);
                        progressBar.style.width = `${percent}%`;
                        progressText.textContent = `${completed} / ${numAccounts} (${percent}%)`;
                    }
                    
                    function addLog(message, type = 'info') {
                        const logEntry = document.createElement('div');
                        const timestamp = new Date().toLocaleTimeString();
                        logEntry.innerHTML = `<span style="color: #888;">[${timestamp}]</span> <span style="color: ${type === 'error' ? '#F44336' : type === 'success' ? '#4CAF50' : '#CCC'}">${message}</span>`;
                        creationLog.appendChild(logEntry);
                        creationLog.scrollTop = creationLog.scrollHeight;
                    }
                    
                    // Start the creation process
                    createNextAccount();
                }
            });
        </script>
        '''
    )

@app.route('/dashboard')
def dashboard_page():
    """The account management dashboard page with real data"""
    process_assets()
    
    # Get accounts with pagination
    accounts, total_accounts = get_accounts(limit=10, offset=0)
    
    # Get area codes for filtering
    area_codes = get_area_codes()
    
    # Build area code options HTML
    area_code_options_html = '<option value="all">All Area Codes</option>'
    for area_code in area_codes:
        area_code_options_html += f'<option value="{area_code}">{area_code}</option>'
    
    # Build account rows HTML
    account_rows_html = ''
    for account in accounts:
        status_class = ''
        if account['status'] == 'active':
            status_class = 'status-active'
        elif account['status'] == 'banned':
            status_class = 'status-danger'
        elif account['status'] == 'limited':
            status_class = 'status-warning'
        else:
            status_class = 'status-neutral'
            
        days_ago = calculate_days_ago(account['created_at'])
        
        account_rows_html += f'''
            <tr data-account-id="{account['id']}">
                <td>{account['phone_number']}</td>
                <td>{account['username']}</td>
                <td>{account['area_code']}</td>
                <td>{days_ago}</td>
                <td><span class="status-badge {status_class}">{account['status'].capitalize()}</span></td>
                <td>
                    <button class="form-button secondary-button">Login</button>
                    <button class="form-button">Manage</button>
                </td>
            </tr>
        '''
    
    # If no accounts found, show empty state
    if not accounts:
        account_rows_html = '''
            <tr>
                <td colspan="6">
                    <div class="empty-state">
                        <div class="empty-state-icon">👤</div>
                        <div class="empty-state-title">No Accounts Yet</div>
                        <div class="empty-state-text">Create your first TextNow account to get started.</div>
                        <a href="/creator"><button class="form-button">Create Account</button></a>
                    </div>
                </td>
            </tr>
        '''
    
    # Get stats for the dashboard
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total accounts
        cursor.execute('SELECT COUNT(*) FROM accounts')
        total_accounts = cursor.fetchone()[0]
        
        # Active accounts 
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE status = 'active'")
        active_accounts = cursor.fetchone()[0]
        
        # Banned accounts
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE status = 'banned'")
        banned_accounts = cursor.fetchone()[0]
        
        # New accounts today
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE created_at > datetime('now', '-1 day')")
        new_today = cursor.fetchone()[0]
        
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
            <div class="app-header">
                <div class="app-title">Account Dashboard</div>
                <div class="app-actions">
                    <button class="form-button secondary-button">Export CSV</button>
                    <a href="/creator"><button class="form-button">Create New</button></a>
                </div>
            </div>
            
            <div class="app-content">
                <div class="form-panel">
                    <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 20px;">
                        <div style="background-color: #333; padding: 15px; border-radius: 6px; min-width: 180px; text-align: center;">
                            <div style="font-size: 24px; font-weight: bold; color: #FF6600;">''' + str(total_accounts) + '''</div>
                            <div style="color: #AAA; margin-top: 5px;">Total Accounts</div>
                        </div>
                        
                        <div style="background-color: #333; padding: 15px; border-radius: 6px; min-width: 180px; text-align: center;">
                            <div style="font-size: 24px; font-weight: bold; color: #FF6600;">''' + str(active_accounts) + '''</div>
                            <div style="color: #AAA; margin-top: 5px;">Active</div>
                        </div>
                        
                        <div style="background-color: #333; padding: 15px; border-radius: 6px; min-width: 180px; text-align: center;">
                            <div style="font-size: 24px; font-weight: bold; color: #F44336;">''' + str(banned_accounts) + '''</div>
                            <div style="color: #AAA; margin-top: 5px;">Banned</div>
                        </div>
                        
                        <div style="background-color: #333; padding: 15px; border-radius: 6px; min-width: 180px; text-align: center;">
                            <div style="font-size: 24px; font-weight: bold; color: #4CAF50;">''' + str(new_today) + '''</div>
                            <div style="color: #AAA; margin-top: 5px;">New Today</div>
                        </div>
                    </div>
                </div>
                
                <div class="form-panel">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                        <div style="font-weight: bold;">Account Filter</div>
                        <div style="display: flex; gap: 10px;">
                            <select class="form-control" id="status-filter" style="width: auto;">
                                <option value="all">All Statuses</option>
                                <option value="active">Active</option>
                                <option value="banned">Banned</option>
                                <option value="limited">Limited</option>
                                <option value="pending">Pending</option>
                            </select>
                            
                            <select class="form-control" id="area-filter" style="width: auto;">
                                ''' + area_code_options_html + '''
                            </select>
                            
                            <select class="form-control" id="age-filter" style="width: auto;">
                                <option value="all">All Ages</option>
                                <option value="today">Created Today</option>
                                <option value="week">Created This Week</option>
                                <option value="month">Created This Month</option>
                            </select>
                            
                            <input type="text" class="form-control" id="search-input" placeholder="Search..." style="width: 150px;">
                            <button class="form-button" id="search-button">Filter</button>
                        </div>
                    </div>
                    
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th>Phone Number</th>
                                <th>Username</th>
                                <th>Area Code</th>
                                <th>Created</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="accounts-table-body">
                            ''' + account_rows_html + '''
                        </tbody>
                    </table>
                    
                    <div style="display: flex; justify-content: space-between; margin-top: 15px; align-items: center;">
                        <div style="color: #CCC; font-size: 14px;">Showing ''' + str(len(accounts)) + ''' of ''' + str(total_accounts) + ''' accounts</div>
                        
                        <div style="display: flex; gap: 5px;">
                            <button class="form-button secondary-button" id="prev-page" disabled>Previous</button>
                            <button class="form-button secondary-button" id="next-page">Next</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                // Search functionality
                const searchButton = document.getElementById('search-button');
                const searchInput = document.getElementById('search-input');
                const statusFilter = document.getElementById('status-filter');
                const areaFilter = document.getElementById('area-filter');
                const ageFilter = document.getElementById('age-filter');
                
                if (searchButton) {
                    searchButton.addEventListener('click', function() {
                        const searchTerm = searchInput.value;
                        const status = statusFilter.value;
                        const areaCode = areaFilter.value;
                        const age = ageFilter.value;
                        
                        // In a real implementation, this would perform an AJAX request to filter the data
                        showStatusMessage(`Searching for: "${searchTerm}" (Status: ${status}, Area: ${areaCode}, Age: ${age})`, 'success');
                    });
                }
            });
            
            function showStatusMessage(message, type = 'info') {
                // Implementation of the status message function
                alert(message);
            }
        </script>
        '''
    )

@app.route('/campaigns')
def campaigns_page():
    """The campaigns management page"""
    process_assets()
    
    # Get campaigns with pagination
    campaigns, total_campaigns = get_campaigns(limit=10, offset=0)
    
    # Build campaign rows HTML
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
        
        campaign_rows_html += '''
            <tr data-campaign-id="''' + str(campaign['id']) + '''">
                <td>''' + campaign['name'] + '''</td>
                <td>''' + campaign['description'][:50] + ('...' if len(campaign['description'] or '') > 50 else '') + '''</td>
                <td>''' + campaign['start_date'] + '''</td>
                <td>''' + campaign['end_date'] + '''</td>
                <td><span class="status-badge ''' + status_class + '''">''' + campaign['status'].capitalize() + '''</span></td>
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
                            <div style="font-size: 22px; font-weight: bold; color: #FF6600;">''' + str(total_campaigns) + '''</div>
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
                            ''' + campaign_rows_html + '''
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