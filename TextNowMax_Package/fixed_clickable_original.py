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
import datetime
from flask import Flask, render_template_string, send_from_directory, redirect, url_for, request, jsonify
from api_routes import api

app = Flask(__name__)

# Register the API blueprint
app.register_blueprint(api, url_prefix='/api')

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

# Database connection helper
def get_db_connection():
    """Get database connection"""
    conn = None
    try:
        # Check if the database file exists
        if not os.path.exists('ghost_accounts.db'):
            print(f"Database file 'ghost_accounts.db' does not exist. Creating initial database.")
            # Create a new database with minimal structure
            conn = sqlite3.connect('ghost_accounts.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Create necessary tables if they don't exist
            # Accounts table with minimum required fields
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    username TEXT,
                    area_code TEXT,
                    email TEXT,
                    password TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    health_score INTEGER DEFAULT 100,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_login TEXT,
                    fingerprint TEXT,
                    login_cookie TEXT
                )
            ''')
            
            # Basic area codes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS area_codes (
                    area_code TEXT PRIMARY KEY,
                    state TEXT,
                    region TEXT,
                    city TEXT,
                    timezone TEXT,
                    available INTEGER DEFAULT 1,
                    popularity INTEGER DEFAULT 0
                )
            ''')
            
            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    recipient TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sent_time TEXT,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            ''')
            
            # Campaigns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    status TEXT DEFAULT 'draft',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print(f"Created initial database structure")
            return conn
        else:
            # Normal connection to existing database
            conn = sqlite3.connect('ghost_accounts.db')
            conn.row_factory = sqlite3.Row
    except Exception as e:
        print(f"Database error: {e}")
    return conn

# Helper function to format dates nicely
def format_date(date_str):
    if not date_str:
        return ""
    try:
        dt = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_str

# Helper function to calculate days ago
def calculate_days_ago(date_str):
    if not date_str:
        return 0
    try:
        dt = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        delta = datetime.datetime.now() - dt
        return delta.days
    except:
        return 0
        
# Get statistics from database
def get_statistics():
    try:
        conn = get_db_connection()
        if not conn:
            raise Exception("Could not connect to the database")
            
        cursor = conn.cursor()
        
        # Account statistics
        cursor.execute('''
            SELECT 
                COUNT(*) AS total_accounts,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_accounts,
                SUM(CASE WHEN status = 'banned' THEN 1 ELSE 0 END) AS banned_accounts
            FROM accounts
        ''')
        
        account_stats = cursor.fetchone()
        if not account_stats:
            account_stats = {'total_accounts': 0, 'active_accounts': 0, 'banned_accounts': 0}
            
        total_accounts = account_stats['total_accounts'] if 'total_accounts' in account_stats.keys() else 0
        active_accounts = account_stats['active_accounts'] if 'active_accounts' in account_stats.keys() else 0
        banned_accounts = account_stats['banned_accounts'] if 'banned_accounts' in account_stats.keys() else 0
        
        # New accounts in last 24 hours
        cursor.execute('''
            SELECT COUNT(*) AS new_accounts
            FROM accounts
            WHERE created_at >= datetime('now', '-1 day')
        ''')
        result = cursor.fetchone()
        new_today = result['new_accounts'] if result and 'new_accounts' in result.keys() else 0
        
        # Message statistics - handle the case where the table may not exist or have different structure
        try:
            cursor.execute('''
                SELECT 
                    COUNT(*) AS total_messages,
                    SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) AS delivered_messages
                FROM messages
            ''')
            
            message_stats = cursor.fetchone()
            if not message_stats:
                message_stats = {'total_messages': 0, 'delivered_messages': 0}
                
            total_messages = message_stats['total_messages'] if 'total_messages' in message_stats.keys() else 0
            delivered_messages = message_stats['delivered_messages'] if 'delivered_messages' in message_stats.keys() else 0
        except:
            # If there's any error with the messages table
            total_messages = 0
            delivered_messages = 0
        
        # Calculate success rate
        success_rate = 0
        if total_messages > 0:
            success_rate = round((delivered_messages / total_messages) * 100, 1)
            
        conn.close()
        
        return {
            'total_accounts': total_accounts,
            'active_accounts': active_accounts,
            'banned_accounts': banned_accounts,
            'new_today': new_today,
            'total_messages': total_messages,
            'delivered_messages': delivered_messages,
            'success_rate': success_rate
        }
        
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {
            'total_accounts': 0,
            'active_accounts': 0,
            'banned_accounts': 0,
            'new_today': 0,
            'total_messages': 0,
            'delivered_messages': 0,
            'success_rate': 0
        }

# Get accounts from database
def get_accounts(limit=10, offset=0, filters=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query based on filters and match the actual database schema
        query = '''
            SELECT 
                id,
                phone_number,
                username,
                email,
                password,
                name,
                '' as last_name,
                area_code,
                created_at,
                last_login as last_activity,
                status,
                health_score,
                fingerprint as device_fingerprint,
                login_cookie as session_data
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
                search_term = f"%{filters['search']}%"
                conditions.append("(phone_number LIKE ? OR email LIKE ? OR username LIKE ? OR name LIKE ?)")
                params.extend([search_term, search_term, search_term, search_term])
            
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
            # Split the name into first/last name for display purposes
            name_parts = (account['name'] or "").split(" ", 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            result.append({
                'id': account['id'],
                'phone_number': account['phone_number'] or "No Number",
                'username': account['username'] or "",
                'email': account['email'] or "",
                'first_name': first_name,
                'last_name': last_name,
                'area_code': account['area_code'] or "",
                'created_at': format_date(account['created_at']),
                'created_days_ago': calculate_days_ago(account['created_at']),
                'last_activity': format_date(account['last_activity']),
                'last_activity_days_ago': calculate_days_ago(account['last_activity']),
                'status': account['status'] or "unknown",
                'health_score': account['health_score'] or 0,
                'device_fingerprint': account['device_fingerprint'] or ""
            })
            
        # Get total count for pagination
        cursor.execute('SELECT COUNT(*) as count FROM accounts')
        total_count = cursor.fetchone()['count']
            
        conn.close()
        
        return {
            'accounts': result,
            'total': total_count
        }
        
    except Exception as e:
        print(f"Error getting accounts: {e}")
        return {
            'accounts': [],
            'total': 0
        }

# Get area codes from database
def get_area_codes():
    try:
        conn = get_db_connection()
        if not conn:
            raise Exception("Could not connect to the database")
            
        cursor = conn.cursor()
        
        # Check if area_codes table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='area_codes'")
        if not cursor.fetchone():
            print("Area codes table does not exist yet")
            conn.close()
            return []
            
        try:
            cursor.execute('SELECT area_code FROM area_codes ORDER BY area_code')
            area_codes = [row['area_code'] for row in cursor.fetchall()]
                
            conn.close()
            
            return area_codes
        except Exception as e:
            print(f"Error in area codes query: {e}")
            conn.close()
            return []
        
    except Exception as e:
        print(f"Error getting area codes: {e}")
        return []

# Get campaigns from database
def get_campaigns(limit=10, offset=0):
    try:
        conn = get_db_connection()
        if not conn:
            raise Exception("Could not connect to the database")
            
        cursor = conn.cursor()
        
        # Check if campaigns table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='campaigns'")
        if not cursor.fetchone():
            print("Campaigns table does not exist yet")
            conn.close()
            return {
                'campaigns': [],
                'total': 0
            }
            
        # Get campaigns with safe column selection
        try:
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
            cursor.execute('SELECT COUNT(*) as count FROM campaigns')
            total_count = cursor.fetchone()['count']
                
            conn.close()
            
            return {
                'campaigns': result,
                'total': total_count
            }
        except Exception as e:
            print(f"Error in campaigns query: {e}")
            conn.close()
            return {
                'campaigns': [],
                'total': 0
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
        if not conn:
            raise Exception("Could not connect to the database")
            
        cursor = conn.cursor()
        
        # Check if the table has sent_time or sent_at column
        try:
            cursor.execute("PRAGMA table_info(messages)")
            columns = [column['name'] for column in cursor.fetchall()]
            
            sent_column = "sent_time"
            if "sent_at" in columns:
                sent_column = "sent_at"
            elif "sent_time" in columns:
                sent_column = "sent_time"
            
            # Use the correct column name in the query
            cursor.execute(f'''
                SELECT 
                    m.id,
                    m.recipient,
                    m.content,
                    m.{sent_column} as sent_timestamp,
                    m.status,
                    a.phone_number as sender
                FROM messages m
                LEFT JOIN accounts a ON m.account_id = a.id
                ORDER BY m.{sent_column} DESC
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
                    'sent_at': format_date(message['sent_timestamp']),
                    'status': message['status'] or "unknown"
                })
                
            conn.close()
            
            return result
            
        except Exception as e:
            print(f"Error in message query: {e}")
            # Return empty demo data as fallback
            conn.close()
            return []
    
    except Exception as e:
        print(f"Error getting recent messages: {e}")
        return []

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
    </style>
    <script>
        // This makes all buttons clickable with visual feedback
        document.addEventListener('DOMContentLoaded', function() {
            // Add click handler to all buttons and interactive elements
            document.querySelectorAll('button, .form-button, .tab, input[type="submit"], .secondary-button').forEach(function(element) {
                element.addEventListener('click', function(e) {
                    // Skip special functional buttons
                    if (this.id === 'rotate-ip-btn' || this.id === 'check-connection-btn') {
                        // Just visual feedback for these special buttons
                        this.style.transform = 'scale(0.97)';
                        setTimeout(() => {
                            this.style.transform = 'scale(1)';
                        }, 100);
                        return; // Let the actual function handle it
                    }
                    
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
                    showStatusMessage('Clicked: ' + this.textContent.trim(), 'success');
                    
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
                    if (msgElement.parentNode) {
                        document.body.removeChild(msgElement);
                    }
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
            <a href="/media-dashboard" class="nav-link {{ 'active' if active_page == '/media-dashboard' else '' }}">Media Manager</a>
            <a href="/account-health" class="nav-link {{ 'active' if active_page == '/account-health' else '' }}">Account Health</a>
            <a href="/voicemail-manager" class="nav-link {{ 'active' if active_page == '/voicemail-manager' else '' }}">Voicemail Manager</a>
            <a href="/campaign-schedule" class="nav-link {{ 'active' if active_page == '/campaign-schedule' else '' }}">Schedule</a>
            <a href="/proxy-manager" class="nav-link {{ 'active' if active_page == '/proxy-manager' else '' }}">Proxy Manager</a>
            <a href="/anti-detection" class="nav-link {{ 'active' if active_page == '/anti-detection' else '' }}">Anti-Detection</a>
        </div>
    </div>
    
    <!-- Proxidize Status Bar -->
    <div class="device-status-bar">
        <style>
            .device-status-bar {
                background-color: #FF6600; /* Bright orange color to make it stand out */
                padding: 8px 20px;
                display: flex;
                align-items: center;
                justify-content: flex-start;
                border-bottom: 1px solid #333;
                font-size: 13px;
                position: fixed;
                top: 60px; /* Position below the nav bar */
                left: 0;
                right: 0;
                z-index: 100;
                color: white;
            }
            
            .device-status-item {
                display: flex;
                align-items: center;
                margin-right: 20px;
                padding-right: 20px;
                border-right: 1px solid rgba(255, 255, 255, 0.3);
            }
            
            .device-status-item:last-child {
                border-right: none;
                margin-right: 0;
            }
            
            .device-status-icon {
                margin-right: 8px;
                font-size: 16px;
            }
            
            .device-status-text {
                color: white;
                font-weight: normal;
            }
            
            .device-status-text strong {
                color: white;
                margin-left: 5px;
                font-weight: bold;
            }
            
            .device-status-connected {
                color: white;
                text-shadow: 0 0 5px #4CAF50;
            }
            
            .device-status-disconnected {
                color: white;
                text-shadow: 0 0 5px #F44336;
            }
            
            .device-status-ip {
                color: white;
                text-shadow: 0 0 5px #2196F3;
            }
            
            .refresh-ip-button {
                background-color: white;
                color: #FF6600;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                font-weight: bold;
                transition: all 0.2s;
            }
            
            .refresh-ip-button:hover {
                background-color: #333;
                color: white;
                transform: scale(1.05);
            }
        </style>
        <div class="device-status-item">
            <div class="device-status-icon device-status-connected">●</div>
            <div class="device-status-text">Proxidize Status: <strong>Loading...</strong></div>
        </div>
        <div class="device-status-item">
            <div class="device-status-icon device-status-ip">✓</div>
            <div class="device-status-text">Current IP: <strong>Loading...</strong></div>
        </div>
        <div class="device-status-item">
            <div class="device-status-text">Proxy Server: <strong>Loading...</strong></div>
        </div>
        <div class="device-status-item">
            <div class="device-status-text">Last IP Change: <strong>Loading...</strong></div>
        </div>
        <div class="device-status-item" style="border-right: none;">
            <button class="refresh-ip-button" id="refresh-ip-btn">Rotate IP</button>
        </div>
    </div>
    
    <!-- Page Content -->
    <div class="content-wrapper">
        {{ content|safe }}
    </div>
    
    <!-- Device Status JavaScript -->
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Device Status Bar - IP Refresh Button
            const refreshIpButton = document.getElementById('refresh-ip-btn');
            if (refreshIpButton) {
                refreshIpButton.addEventListener('click', function() {
                    // Disable button during refresh
                    this.disabled = true;
                    this.innerText = 'Refreshing...';
                    
                    // Make API call to backend to rotate IP via Proxidize
                    fetch('/api/device/refresh-ip', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    })
                    .then(response => response.json())
                    .then(data => {
                        // Update IP display
                        const ipElement = document.querySelector('.device-status-item:nth-child(2) .device-status-text strong');
                        const timeElement = document.querySelector('.device-status-item:nth-child(4) .device-status-text strong');
                        
                        if (data.success) {
                            if (ipElement) ipElement.innerText = data.new_ip || '192.168.1.1';
                            if (timeElement) timeElement.innerText = 'Just now';
                            
                            // Visual feedback - flash green
                            const ipIcon = document.querySelector('.device-status-ip');
                            if (ipIcon) {
                                ipIcon.style.transition = 'color 0.3s';
                                ipIcon.style.color = '#4CAF50';
                                setTimeout(() => {
                                    ipIcon.style.color = '#2196F3';
                                }, 1500);
                            }
                        } else {
                            // Show error feedback
                            if (ipElement) ipElement.innerHTML = '<span style="color: #F44336;">Error refreshing</span>';
                        }
                        
                        // Re-enable button
                        this.disabled = false;
                        this.innerText = 'Refresh IP';
                    })
                    .catch(error => {
                        console.error('Error refreshing IP:', error);
                        // Show error and re-enable button
                        const ipElement = document.querySelector('.device-status-item:nth-child(2) .device-status-text strong');
                        if (ipElement) ipElement.innerHTML = '<span style="color: #F44336;">Connection error</span>';
                        
                        this.disabled = false;
                        this.innerText = 'Retry';
                    });
                });
            }
            
            // Periodically check device connection status
            function updateDeviceStatus() {
                fetch('/api/device/status')
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log("Device status data:", data);
                        
                        // Update connection status
                        const statusIcon = document.querySelector('.device-status-connected');
                        const statusText = document.querySelector('.device-status-item:first-child .device-status-text strong');
                        
                        // Update IP address
                        const ipElement = document.querySelector('.device-status-item:nth-child(2) .device-status-text strong');
                        
                        // Update proxy server
                        const proxyElement = document.querySelector('.device-status-item:nth-child(3) .device-status-text strong');
                        
                        // Update last rotation time
                        const timeElement = document.querySelector('.device-status-item:nth-child(4) .device-status-text strong');
                        
                        if (data.success) {
                            // Connection status
                            if (data.connected) {
                                if (statusIcon) statusIcon.style.color = '#4CAF50';
                                if (statusText) statusText.innerText = 'Connected';
                            } else {
                                if (statusIcon) statusIcon.style.color = '#F44336';
                                if (statusText) statusText.innerText = 'Disconnected';
                            }
                            
                            // Update IP address
                            if (ipElement && data.network_info && data.network_info.current_ip) {
                                ipElement.innerText = data.network_info.current_ip;
                            }
                            
                            // Update proxy server
                            if (proxyElement && data.proxy_info && data.proxy_info.server) {
                                proxyElement.innerText = data.proxy_info.server;
                            }
                            
                            // Update last rotation time
                            if (timeElement && data.network_info && data.network_info.last_rotation) {
                                timeElement.innerText = data.network_info.last_rotation;
                            }
                        } else {
                            // Show error status
                            if (statusIcon) statusIcon.style.color = '#F44336';
                            if (statusText) statusText.innerText = 'Error';
                            if (ipElement) ipElement.innerHTML = '<span style="color: #F44336;">Unavailable</span>';
                        }
                    })
                    .catch(error => {
                        console.error('Error checking device status:', error);
                        
                        // Show error status in UI
                        const statusIcon = document.querySelector('.device-status-connected');
                        const statusText = document.querySelector('.device-status-item:first-child .device-status-text strong');
                        
                        if (statusIcon) statusIcon.style.color = '#F44336';
                        if (statusText) statusText.innerHTML = '<span style="color: #F44336;">Error</span>';
                    });
            }
            
            // Check status every 30 seconds
            setInterval(updateDeviceStatus, 30000);
            
            // Initial status check
            updateDeviceStatus();
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Display real-time data for the TextNow Max application"""
    process_assets()
    
    # Get real statistics from database
    stats = get_statistics()
    
    # Extract statistics
    total_accounts = stats['total_accounts']
    active_accounts = stats['active_accounts']
    banned_accounts = stats['banned_accounts']
    new_today = stats['new_today']
    total_messages = stats['total_messages']
    delivered_messages = stats['delivered_messages']
    success_rate = stats['success_rate']
    
    # Get recent messages for display
    recent_messages = get_recent_messages(limit=5)
    
    return render_template_string(
        BASE_HTML,
        title="Home",
        active_page="/",
        content=f'''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%;">
                    <div style="max-width: 800px; text-align: center;">
                        <h1 style="font-size: 32px; margin-bottom: 20px; color: #FF6600;">TextNow Max</h1>
                        <p>The ultimate TextNow account management and automation platform. Create, manage, and utilize ghost accounts with sophisticated distribution, voicemail setup, and mass messaging capabilities.</p>
                        
                        <div style="display: flex; justify-content: center; gap: 15px; margin: 30px 0;">
                            <a href="/creator" class="form-button">Create Accounts</a>
                            <a href="/dashboard" class="form-button">Manage Accounts</a>
                            <a href="/campaigns" class="form-button">Run Campaigns</a>
                        </div>
                        
                        <div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; margin-top: 30px;">
                            <div style="background-color: #252525; padding: 20px; border-radius: 6px; min-width: 160px; text-align: center;">
                                <div style="font-size: 24px; font-weight: bold; color: #FF6600;">{total_accounts}</div>
                                <div style="color: #AAA; margin-top: 5px;">Total Accounts</div>
                            </div>
                            <div style="background-color: #252525; padding: 20px; border-radius: 6px; min-width: 160px; text-align: center;">
                                <div style="font-size: 24px; font-weight: bold; color: #FF6600;">{active_accounts}</div>
                                <div style="color: #AAA; margin-top: 5px;">Active Accounts</div>
                            </div>
                            <div style="background-color: #252525; padding: 20px; border-radius: 6px; min-width: 160px; text-align: center;">
                                <div style="font-size: 24px; font-weight: bold; color: #FF6600;">{total_messages}</div>
                                <div style="color: #AAA; margin-top: 5px;">Messages Sent</div>
                            </div>
                            <div style="background-color: #252525; padding: 20px; border-radius: 6px; min-width: 160px; text-align: center;">
                                <div style="font-size: 24px; font-weight: bold; color: #FF6600;">{success_rate}%</div>
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
                            
                            <div style="margin-bottom: 10px;">
                                <select id="preset-category" class="form-select">
                                    <option value="regions">US Regions</option>
                                    <option value="states">States (All 50)</option>
                                    <option value="cities">Major Cities</option>
                                    <option value="florida-specific">Florida Only</option>
                                </select>
                            </div>
                            
                            <!-- Regions Presets -->
                            <div id="regions-presets" style="display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 10px;">
                                <button class="form-button secondary-button" data-preset="northeast">Northeast</button>
                                <button class="form-button secondary-button" data-preset="southeast">Southeast</button>
                                <button class="form-button secondary-button" data-preset="midwest">Midwest</button>
                                <button class="form-button secondary-button" data-preset="southwest">Southwest</button>
                                <button class="form-button secondary-button" data-preset="west">West</button>
                            </div>
                            
                            <!-- States Presets (Initially Hidden) -->
                            <div id="states-presets" style="display: none; gap: 5px; flex-wrap: wrap; margin-bottom: 10px; max-height: 150px; overflow-y: auto;">
                                <button class="form-button secondary-button" data-preset="alabama_all">Alabama</button>
                                <button class="form-button secondary-button" data-preset="alaska_all">Alaska</button>
                                <button class="form-button secondary-button" data-preset="arizona_all">Arizona</button>
                                <button class="form-button secondary-button" data-preset="arkansas_all">Arkansas</button>
                                <button class="form-button secondary-button" data-preset="california_all">California</button>
                                <button class="form-button secondary-button" data-preset="colorado_all">Colorado</button>
                                <button class="form-button secondary-button" data-preset="connecticut_all">Connecticut</button>
                                <button class="form-button secondary-button" data-preset="delaware_all">Delaware</button>
                                <button class="form-button secondary-button" data-preset="district_of_columbia_all">DC</button>
                                <button class="form-button secondary-button" data-preset="florida_all">Florida</button>
                                <button class="form-button secondary-button" data-preset="georgia_all">Georgia</button>
                                <button class="form-button secondary-button" data-preset="hawaii_all">Hawaii</button>
                                <button class="form-button secondary-button" data-preset="idaho_all">Idaho</button>
                                <button class="form-button secondary-button" data-preset="illinois_all">Illinois</button>
                                <button class="form-button secondary-button" data-preset="indiana_all">Indiana</button>
                                <button class="form-button secondary-button" data-preset="iowa_all">Iowa</button>
                                <button class="form-button secondary-button" data-preset="kansas_all">Kansas</button>
                                <button class="form-button secondary-button" data-preset="kentucky_all">Kentucky</button>
                                <button class="form-button secondary-button" data-preset="louisiana_all">Louisiana</button>
                                <button class="form-button secondary-button" data-preset="maine_all">Maine</button>
                                <button class="form-button secondary-button" data-preset="maryland_all">Maryland</button>
                                <button class="form-button secondary-button" data-preset="massachusetts_all">Massachusetts</button>
                                <button class="form-button secondary-button" data-preset="michigan_all">Michigan</button>
                                <button class="form-button secondary-button" data-preset="minnesota_all">Minnesota</button>
                                <button class="form-button secondary-button" data-preset="mississippi_all">Mississippi</button>
                                <button class="form-button secondary-button" data-preset="missouri_all">Missouri</button>
                                <button class="form-button secondary-button" data-preset="montana_all">Montana</button>
                                <button class="form-button secondary-button" data-preset="nebraska_all">Nebraska</button>
                                <button class="form-button secondary-button" data-preset="nevada_all">Nevada</button>
                                <button class="form-button secondary-button" data-preset="new_hampshire_all">New Hampshire</button>
                                <button class="form-button secondary-button" data-preset="new_jersey_all">New Jersey</button>
                                <button class="form-button secondary-button" data-preset="new_mexico_all">New Mexico</button>
                                <button class="form-button secondary-button" data-preset="new_york_all">New York</button>
                                <button class="form-button secondary-button" data-preset="north_carolina_all">North Carolina</button>
                                <button class="form-button secondary-button" data-preset="north_dakota_all">North Dakota</button>
                                <button class="form-button secondary-button" data-preset="ohio_all">Ohio</button>
                                <button class="form-button secondary-button" data-preset="oklahoma_all">Oklahoma</button>
                                <button class="form-button secondary-button" data-preset="oregon_all">Oregon</button>
                                <button class="form-button secondary-button" data-preset="pennsylvania_all">Pennsylvania</button>
                                <button class="form-button secondary-button" data-preset="rhode_island_all">Rhode Island</button>
                                <button class="form-button secondary-button" data-preset="south_carolina_all">South Carolina</button>
                                <button class="form-button secondary-button" data-preset="south_dakota_all">South Dakota</button>
                                <button class="form-button secondary-button" data-preset="tennessee_all">Tennessee</button>
                                <button class="form-button secondary-button" data-preset="texas_all">Texas</button>
                                <button class="form-button secondary-button" data-preset="utah_all">Utah</button>
                                <button class="form-button secondary-button" data-preset="vermont_all">Vermont</button>
                                <button class="form-button secondary-button" data-preset="virginia_all">Virginia</button>
                                <button class="form-button secondary-button" data-preset="washington_all">Washington</button>
                                <button class="form-button secondary-button" data-preset="west_virginia_all">West Virginia</button>
                                <button class="form-button secondary-button" data-preset="wisconsin_all">Wisconsin</button>
                                <button class="form-button secondary-button" data-preset="wyoming_all">Wyoming</button>
                            </div>
                            
                            <!-- Cities Presets (Initially Hidden) -->
                            <div id="cities-presets" style="display: none; gap: 5px; flex-wrap: wrap; margin-bottom: 10px;">
                                <button class="form-button secondary-button" data-preset="major_cities">Major Cities</button>
                                <button class="form-button secondary-button">NYC</button>
                                <button class="form-button secondary-button">LA</button>
                                <button class="form-button secondary-button">Chicago</button>
                                <button class="form-button secondary-button">Houston</button>
                                <button class="form-button secondary-button">Phoenix</button>
                                <button class="form-button secondary-button">Philadelphia</button>
                                <button class="form-button secondary-button">San Antonio</button>
                                <button class="form-button secondary-button">San Diego</button>
                                <button class="form-button secondary-button">Dallas</button>
                            </div>
                            
                            <!-- Florida Presets (Initially Hidden) -->
                            <div id="florida-presets" style="display: none; gap: 5px; flex-wrap: wrap; margin-bottom: 10px;">
                                <button class="form-button secondary-button" data-preset="florida_south">South FL</button>
                                <button class="form-button secondary-button" data-preset="florida_central">Central FL</button>
                                <button class="form-button secondary-button" data-preset="florida_north">North FL</button>
                                <button class="form-button secondary-button" data-preset="florida_all">All Florida</button>
                            </div>
                        </div>
                        
                        <script>
                            document.addEventListener('DOMContentLoaded', function() {
                                const presetSelect = document.getElementById('preset-category');
                                const presetsContainers = {
                                    regions: document.getElementById('regions-presets'),
                                    states: document.getElementById('states-presets'),
                                    cities: document.getElementById('cities-presets'),
                                    'florida-specific': document.getElementById('florida-presets')
                                };
                                
                                // Handle category selection
                                presetSelect.addEventListener('change', function() {
                                    const selectedCategory = this.value;
                                    
                                    // Hide all preset containers
                                    for (const key in presetsContainers) {
                                        presetsContainers[key].style.display = 'none';
                                    }
                                    
                                    // Show selected category
                                    presetsContainers[selectedCategory].style.display = 'flex';
                                });
                                
                                // Handle preset button clicks
                                const areaCodeInput = document.querySelector('input[placeholder="Enter area codes separated by commas"]');
                                const presetButtons = document.querySelectorAll('.form-button[data-preset]');
                                
                                presetButtons.forEach(button => {
                                    button.addEventListener('click', function() {
                                        const presetName = this.getAttribute('data-preset');
                                        // In a real implementation, this would fetch the area codes from the server
                                        // For now, we'll just set a placeholder value
                                        if (presetName === 'florida_south') {
                                            areaCodeInput.value = '954, 754, 305, 786, 561';
                                        } else if (presetName === 'major_cities') {
                                            areaCodeInput.value = '212, 332, 646, 718, 917, 929, 213, 310, 323, 424, 312, 773, 872, 713, 281, 832';
                                        } else {
                                            // This would be replaced with an API call in the real implementation
                                            areaCodeInput.value = 'Selected preset: ' + presetName;
                                        }
                                        
                                        showStatusMessage('Selected area code preset: ' + this.textContent.trim(), 'success');
                                    });
                                });
                            });
                        </script>
                        
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
    
    # Get real account data and statistics from database
    stats = get_statistics()
    
    # Get accounts with pagination
    account_data = get_accounts(limit=25)
    accounts = account_data['accounts']
    total_accounts = account_data['total']
    
    # Get area codes for the filter dropdown
    area_codes = get_area_codes()
    
    # Build area code options HTML
    area_code_options_html = '<option value="all">All Area Codes</option>'
    for area_code in area_codes:
        area_code_options_html += f'<option value="{area_code}">{area_code}</option>'
    
    # Build account rows HTML
    account_rows_html = ''
    for account in accounts:
        status_class = 'status-neutral'
        if account['status'] == 'active':
            status_class = 'status-active'
        elif account['status'] == 'banned':
            status_class = 'status-danger'
        elif account['status'] == 'flagged':
            status_class = 'status-warning'
        
        account_rows_html += f'''
            <tr data-account-id="{account['id']}">
                <td><input type="checkbox"></td>
                <td>{account['phone_number']}</td>
                <td>
                    <div>{account['username']}</div>
                    <div style="font-size: 12px; color: #AAA;">{account['email']}</div>
                </td>
                <td>{account['area_code']}</td>
                <td>
                    <div>{account['created_at']}</div>
                    <div style="font-size: 12px; color: #AAA;">{account['created_days_ago']} days ago</div>
                </td>
                <td>
                    <div>{account['last_activity']}</div>
                    <div style="font-size: 12px; color: #AAA;">{account['last_activity_days_ago']} days ago</div>
                </td>
                <td><span class="status-badge {status_class}">{account['status'].capitalize()}</span></td>
                <td>
                    <button class="form-button secondary-button">Login</button>
                    <button class="form-button secondary-button">Edit</button>
                </td>
            </tr>
        '''
    
    # If no accounts found, show empty state
    if not accounts:
        account_rows_html = '''
            <tr>
                <td colspan="8" style="text-align: center; padding: 30px 0;">
                    <div style="font-size: 18px; margin-bottom: 10px;">No Accounts Found</div>
                    <div style="color: #AAA; margin-bottom: 20px;">Start creating TextNow accounts to see them here</div>
                    <a href="/creator" class="form-button">Create First Account</a>
                </td>
            </tr>
        '''
    
    return render_template_string(
        BASE_HTML,
        title="Account Dashboard",
        active_page="/dashboard",
        content=f'''
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
                                <th>IP Address</th>
                                <th>Status</th>
                                <th>Last Used</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr data-account-id="1">
                                <td>(954) 123-4567</td>
                                <td>John Smith</td>
                                <td>954</td>
                                <td>192.168.1.24</td>
                                <td><span class="status-badge status-active">Active</span></td>
                                <td>Today, 2:30 PM</td>
                                <td>
                                    <button class="form-button secondary-button">Details</button>
                                    <button class="form-button secondary-button">Login</button>
                                </td>
                            </tr>
                            <tr class="account-details" style="display: none;">
                                <td colspan="7" style="padding: 0;">
                                    <div style="padding: 20px; background-color: #1A1A1A;">
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                                            <h3 style="margin: 0; color: #FF6600;">Account Details</h3>
                                            <div>
                                                <button class="form-button secondary-button">Edit Account</button>
                                                <button class="form-button secondary-button">Hide Details</button>
                                            </div>
                                        </div>
                                        
                                        <div style="display: flex; gap: 20px;">
                                            <!-- Account Info -->
                                            <div style="flex: 1;">
                                                <h4 style="margin: 0 0 10px 0; color: #CCC;">Account Information</h4>
                                                <div style="background-color: #252525; padding: 15px; border-radius: 4px;">
                                                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                                        <div style="color: #AAA;">Phone Number:</div>
                                                        <div style="color: #EEE;">(954) 123-4567</div>
                                                    </div>
                                                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                                        <div style="color: #AAA;">Name:</div>
                                                        <div style="color: #EEE;">John Smith</div>
                                                    </div>
                                                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                                        <div style="color: #AAA;">Email:</div>
                                                        <div style="color: #EEE;">john.smith82@example.com</div>
                                                    </div>
                                                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                                        <div style="color: #AAA;">Password:</div>
                                                        <div style="color: #EEE;">••••••••••</div>
                                                    </div>
                                                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                                        <div style="color: #AAA;">IP Address:</div>
                                                        <div style="color: #EEE;">192.168.1.24</div>
                                                    </div>
                                                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                                        <div style="color: #AAA;">IP Family:</div>
                                                        <div style="color: #EEE;">IPv4</div>
                                                    </div>
                                                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                                        <div style="color: #AAA;">Date Created:</div>
                                                        <div style="color: #EEE;">April 12, 2025</div>
                                                    </div>
                                                    <div style="display: flex; justify-content: space-between;">
                                                        <div style="color: #AAA;">Health Score:</div>
                                                        <div style="color: #4CAF50;">95/100</div>
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            <!-- Mini Sender -->
                                            <div style="flex: 1;">
                                                <h4 style="margin: 0 0 10px 0; color: #CCC;">Send Message</h4>
                                                <div style="background-color: #252525; padding: 15px; border-radius: 4px;">
                                                    <div style="margin-bottom: 10px;">
                                                        <label class="form-label">To</label>
                                                        <input type="text" class="form-input" placeholder="Enter number">
                                                    </div>
                                                    <div style="margin-bottom: 10px;">
                                                        <label class="form-label">Message</label>
                                                        <textarea class="form-input" style="height: 80px; resize: vertical;" placeholder="Type your message here..."></textarea>
                                                    </div>
                                                    <div style="margin-bottom: 10px;">
                                                        <label class="form-label">Media (optional)</label>
                                                        <div style="display: flex; gap: 10px;">
                                                            <button class="form-button secondary-button" style="flex: 1; position: relative; overflow: hidden;">
                                                                Upload Media
                                                                <input type="file" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;" accept="image/*,video/*,audio/*">
                                                            </button>
                                                            <button class="form-button secondary-button" style="flex: 1;">From Library</button>
                                                        </div>
                                                    </div>
                                                    <div style="text-align: right; margin-top: 15px;">
                                                        <button class="form-button">Send Message</button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </td>
                            </tr>
                            <tr data-account-id="2">
                                <td>(786) 987-6543</td>
                                <td>Jane Doe</td>
                                <td>786</td>
                                <td>68.175.89.142</td>
                                <td><span class="status-badge status-active">Active</span></td>
                                <td>Today, 1:15 PM</td>
                                <td>
                                    <button class="form-button secondary-button">Details</button>
                                    <button class="form-button secondary-button">Login</button>
                                </td>
                            </tr>
                            <tr data-account-id="3">
                                <td>(305) 456-7890</td>
                                <td>Robert Johnson</td>
                                <td>305</td>
                                <td>104.28.212.80</td>
                                <td><span class="status-badge status-warning">Warning</span></td>
                                <td>Yesterday, 5:45 PM</td>
                                <td>
                                    <button class="form-button secondary-button">Details</button>
                                    <button class="form-button secondary-button">Login</button>
                                </td>
                            </tr>
                            <tr data-account-id="4">
                                <td>(754) 321-0987</td>
                                <td>Sarah Williams</td>
                                <td>754</td>
                                <td>185.167.98.54</td>
                                <td><span class="status-badge status-danger">Flagged</span></td>
                                <td>3 days ago</td>
                                <td>
                                    <button class="form-button secondary-button">Details</button>
                                    <button class="form-button secondary-button">Replace</button>
                                </td>
                            </tr>
                            <tr data-account-id="5">
                                <td>(561) 555-1212</td>
                                <td>Michael Brown</td>
                                <td>561</td>
                                <td>72.14.185.19</td>
                                <td><span class="status-badge status-active">Active</span></td>
                                <td>Today, 10:20 AM</td>
                                <td>
                                    <button class="form-button secondary-button">Details</button>
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
                                <label class="form-label">Message Variations</label>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <button class="form-button secondary-button" style="flex: 1; position: relative; overflow: hidden;">
                                        Upload Document
                                        <input type="file" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;" accept=".txt,.csv,.xlsx,.xls,.doc,.docx">
                                    </button>
                                    <span style="color: #CCC; font-size: 12px;">No file</span>
                                </div>
                                <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                    Upload a document with up to 10,000+ message variations
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Target Numbers</label>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <button class="form-button secondary-button" style="flex: 1; position: relative; overflow: hidden;">
                                        Upload File
                                        <input type="file" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;" accept=".txt,.csv,.xlsx,.xls">
                                    </button>
                                    <span style="color: #CCC; font-size: 12px;">0 numbers</span>
                                </div>
                                <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                    Upload txt, csv, or excel file with target numbers
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
                                <label class="form-label">Date Range</label>
                                <div style="display: flex; gap: 10px; align-items: center;">
                                    <input type="text" class="form-input" placeholder="YYYY-MM-DD" style="flex: 1;">
                                    <span style="color: #CCC;">to</span>
                                    <input type="text" class="form-input" placeholder="YYYY-MM-DD" style="flex: 1;">
                                </div>
                                <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                    Leave blank for continuous operation
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Campaign Duration</label>
                                <select class="form-select">
                                    <option selected>Auto</option>
                                    <option>1 Hour</option>
                                    <option>2 Hours</option>
                                    <option>4 Hours</option>
                                    <option>8 Hours</option>
                                    <option>12 Hours</option>
                                    <option>24 Hours</option>
                                </select>
                                <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                    Auto duration distributes across date range
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Daily Message Limit</label>
                                <input type="number" class="form-input" value="100" style="width: 100%;">
                                <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                    Maximum messages sent per day
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
                                    10,000 targets • 35% complete • Started: Today, 1:30 PM
                                </div>
                                <div style="color: #CCC; margin-bottom: 10px; font-size: 14px;">
                                    Schedule: Apr 25-Apr 27 • 8am-8pm • 100 msgs/day
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
                                    5,000 targets • 42% complete • Started: Yesterday
                                </div>
                                <div style="color: #CCC; margin-bottom: 10px; font-size: 14px;">
                                    Schedule: Apr 24-Apr 30 • 9am-9pm • 80 msgs/day • 8 Hour Duration
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
                                <div style="color: #CCC; margin-bottom: 10px; font-size: 14px;">
                                    Campaign Results: 87% Delivery Rate • 12% Response Rate
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
                            
                            <div style="margin-bottom: 15px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <label class="form-label">Message Variations</label>
                                    <button class="form-button secondary-button" style="position: relative; overflow: hidden;">
                                        Import Variations
                                        <input type="file" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;" accept=".txt,.csv,.xlsx,.xls,.doc,.docx">
                                    </button>
                                </div>
                                <div style="font-size: 12px; color: #AAA; margin-bottom: 10px;">
                                    Upload a document (txt, csv, excel) containing message variations (up to 10,000+)
                                </div>
                                <div style="background-color: #333; padding: 10px; border-radius: 4px; margin-bottom: 10px; font-size: 12px; color: #CCC;">
                                    No document loaded. Using single message variation.
                                </div>
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
                                <div style="margin-top: 10px; display: flex; gap: 10px; align-items: center;">
                                    <button class="form-button secondary-button" style="position: relative; overflow: hidden;">
                                        Import Variables
                                        <input type="file" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;" accept=".txt,.csv,.xlsx,.xls">
                                    </button>
                                    <div style="font-size: 12px; color: #AAA;">
                                        Upload an Excel/CSV with variables
                                    </div>
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 20px;">
                                <label class="form-label">Media (Optional)</label>
                                <div style="display: flex; gap: 15px; align-items: center;">
                                    <div style="width: 100px; height: 100px; background-color: #333; border-radius: 4px; display: flex; justify-content: center; align-items: center; color: #777;">No Media</div>
                                    <div style="flex: 1;">
                                        <button class="form-button secondary-button" style="width: 100%; margin-bottom: 10px; position: relative; overflow: hidden;">
                                            Upload Media
                                            <input type="file" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;" accept="image/*,video/*,audio/*">
                                        </button>
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
                                <select class="form-select" id="account-selector">
                                    <option value="1">(954) 123-4567 - John Smith</option>
                                    <option value="2">(786) 987-6543 - Jane Doe</option>
                                    <option value="3">(305) 456-7890 - Robert Johnson</option>
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
                                <input type="text" class="form-input" id="recipient-number" placeholder="Enter recipient number">
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
                                <textarea id="message-content" class="form-input" style="height: 200px; resize: vertical;" placeholder="Type your message here..."></textarea>
                            </div>
                            
                            <div style="margin-bottom: 20px;">
                                <label class="form-label">Media (Optional)</label>
                                <div style="display: flex; gap: 10px;">
                                    <button class="form-button secondary-button" style="flex: 1; position: relative; overflow: hidden;">
                                        Upload Media
                                        <input type="file" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;" accept="image/*,video/*,audio/*">
                                    </button>
                                    <button class="form-button secondary-button" style="flex: 1;">Select from Library</button>
                                </div>
                            </div>
                            
                            <div style="display: flex; justify-content: space-between; margin-top: 20px;">
                                <button class="form-button secondary-button">Save as Draft</button>
                                <button id="send-message-btn" class="form-button">Send Message</button>
                            </div>
                            <div id="message-status" style="margin-top: 15px; padding: 10px; border-radius: 4px; display: none;"></div>
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

@app.route('/media-dashboard')
def media_dashboard_route():
    """The media management dashboard interface"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Media Manager",
        active_page="/media-dashboard",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <div style="font-size: 20px; font-weight: bold; color: #EEE;">Media Manager</div>
                    <div>
                        <button class="form-button secondary-button" style="position: relative; overflow: hidden;">
                            Import Media
                            <input type="file" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;" multiple accept="image/*,video/*,audio/*">
                        </button>
                        <button class="form-button" style="position: relative; overflow: hidden;">
                            Upload New
                            <input type="file" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;" accept="image/*,video/*,audio/*">
                        </button>
                    </div>
                </div>
                
                <div style="display: flex; gap: 20px; height: calc(100% - 60px);">
                    <!-- Media Categories Panel -->
                    <div style="width: 250px;">
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px; height: 100%;">
                            <div style="font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #EEE;">
                                Categories
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <input type="text" class="form-input" placeholder="Search media...">
                            </div>
                            
                            <div style="margin-top: 10px;">
                                <button class="form-button secondary-button" style="width: 100%; margin-bottom: 10px;">
                                    Delete Selected
                                </button>
                            </div>
                            
                            <div style="margin-top: 20px;">
                                <div style="background-color: #333; padding: 10px; border-radius: 4px; margin-bottom: 8px; cursor: pointer; border-left: 3px solid #FF6600;">
                                    <div style="font-weight: bold; color: #EEE;">All Media</div>
                                    <div style="font-size: 12px; color: #CCC;">120 files</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-bottom: 8px; cursor: pointer;">
                                    <div style="font-weight: bold; color: #EEE;">Sports</div>
                                    <div style="font-size: 12px; color: #CCC;">45 files</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-bottom: 8px; cursor: pointer;">
                                    <div style="font-weight: bold; color: #EEE;">Promotions</div>
                                    <div style="font-size: 12px; color: #CCC;">32 files</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-bottom: 8px; cursor: pointer;">
                                    <div style="font-weight: bold; color: #EEE;">Profile Pictures</div>
                                    <div style="font-size: 12px; color: #CCC;">28 files</div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-bottom: 8px; cursor: pointer;">
                                    <div style="font-weight: bold; color: #EEE;">Uncategorized</div>
                                    <div style="font-size: 12px; color: #CCC;">15 files</div>
                                </div>
                                
                                <button class="form-button secondary-button" style="width: 100%; margin-top: 15px;">Add Category</button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Media Gallery Panel -->
                    <div style="flex: 1;">
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px; height: 100%;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                                <div style="font-size: 16px; font-weight: bold; color: #EEE;">All Media (120)</div>
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
                                    <div style="height: 120px; background-color: #444; display: flex; justify-content: center; align-items: center; color: #777;">Media 1</div>
                                    <div style="padding: 10px;">
                                        <div style="font-size: 14px; color: #EEE; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">sports_promo_1.jpg</div>
                                        <div style="font-size: 12px; color: #AAA;">Used: 24 times</div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 6px; overflow: hidden; cursor: pointer;">
                                    <div style="height: 120px; background-color: #444; display: flex; justify-content: center; align-items: center; color: #777;">Media 2</div>
                                    <div style="padding: 10px;">
                                        <div style="font-size: 14px; color: #EEE; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">basketball_odds.jpg</div>
                                        <div style="font-size: 12px; color: #AAA;">Used: 18 times</div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 6px; overflow: hidden; cursor: pointer;">
                                    <div style="height: 120px; background-color: #444; display: flex; justify-content: center; align-items: center; color: #777;">Media 3</div>
                                    <div style="padding: 10px;">
                                        <div style="font-size: 14px; color: #EEE; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">football_special.jpg</div>
                                        <div style="font-size: 12px; color: #AAA;">Used: 12 times</div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 6px; overflow: hidden; cursor: pointer;">
                                    <div style="height: 120px; background-color: #444; display: flex; justify-content: center; align-items: center; color: #777;">Media 4</div>
                                    <div style="padding: 10px;">
                                        <div style="font-size: 14px; color: #EEE; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">welcome_bonus.jpg</div>
                                        <div style="font-size: 12px; color: #AAA;">Used: 31 times</div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 6px; overflow: hidden; cursor: pointer;">
                                    <div style="height: 120px; background-color: #444; display: flex; justify-content: center; align-items: center; color: #777;">Media 5</div>
                                    <div style="padding: 10px;">
                                        <div style="font-size: 14px; color: #EEE; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">profile_pic_1.jpg</div>
                                        <div style="font-size: 12px; color: #AAA;">Used: 8 times</div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 6px; overflow: hidden; cursor: pointer;">
                                    <div style="height: 120px; background-color: #444; display: flex; justify-content: center; align-items: center; color: #777;">Media 6</div>
                                    <div style="padding: 10px;">
                                        <div style="font-size: 14px; color: #EEE; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">baseball_odds.jpg</div>
                                        <div style="font-size: 12px; color: #AAA;">Used: 15 times</div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 6px; overflow: hidden; cursor: pointer;">
                                    <div style="height: 120px; background-color: #444; display: flex; justify-content: center; align-items: center; color: #777;">Media 7</div>
                                    <div style="padding: 10px;">
                                        <div style="font-size: 14px; color: #EEE; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">profile_pic_2.jpg</div>
                                        <div style="font-size: 12px; color: #AAA;">Used: 7 times</div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #333; border-radius: 6px; overflow: hidden; cursor: pointer;">
                                    <div style="height: 120px; background-color: #444; display: flex; justify-content: center; align-items: center; color: #777;">Media 8</div>
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
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px; background-color: #FF4136;">Delete</button>
                                    </div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-bottom: 10px; cursor: pointer;">
                                    <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Male_Greeting_2.mp3</div>
                                    <div style="font-size: 12px; color: #CCC; margin-bottom: 5px;">Duration: 10s • Used: 24 times</div>
                                    <div style="display: flex; gap: 5px;">
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px;">▶ Play</button>
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px;">Assign</button>
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px; background-color: #FF4136;">Delete</button>
                                    </div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-bottom: 10px; cursor: pointer;">
                                    <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Male_Business_1.mp3</div>
                                    <div style="font-size: 12px; color: #CCC; margin-bottom: 5px;">Duration: 15s • Used: 18 times</div>
                                    <div style="display: flex; gap: 5px;">
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px;">▶ Play</button>
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px;">Assign</button>
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px; background-color: #FF4136;">Delete</button>
                                    </div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; padding: 10px; border-radius: 4px; margin-bottom: 10px; cursor: pointer;">
                                    <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Male_Casual_1.mp3</div>
                                    <div style="font-size: 12px; color: #CCC; margin-bottom: 5px;">Duration: 8s • Used: 15 times</div>
                                    <div style="display: flex; gap: 5px;">
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px;">▶ Play</button>
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px;">Assign</button>
                                        <button class="form-button secondary-button" style="font-size: 12px; padding: 5px 10px; background-color: #FF4136;">Delete</button>
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

@app.route('/proxy-manager')
def proxy_manager_route():
    """The Proxidize proxy management page"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Proxy Manager",
        active_page="/proxy-manager",
        content='''
        <div class="app-container">
            <div class="app-header">
                <h2>Proxidize Proxy Manager</h2>
                <p>Configure and monitor your Proxidize PGS proxy connection for IP rotation.</p>
            </div>
            
            <div class="app-content">
                <!-- Proxy Status Panel -->
                <div class="panel" id="proxy-status-panel">
                    <h3>Proxy Status</h3>
                    <div style="display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px;">
                        <div style="flex: 1; min-width: 200px;">
                            <div class="status-item">
                                <span class="status-label">Connection Status:</span>
                                <span class="status-value" id="proxy-connection-status">Checking...</span>
                            </div>
                            <div class="status-item">
                                <span class="status-label">Current IP Address:</span>
                                <span class="status-value" id="proxy-current-ip">Checking...</span>
                            </div>
                            <div class="status-item">
                                <span class="status-label">Last Rotation:</span>
                                <span class="status-value" id="proxy-last-rotation">Unknown</span>
                            </div>
                        </div>
                        <div style="flex: 1; min-width: 200px;">
                            <div class="status-item">
                                <span class="status-label">Proxy Server:</span>
                                <span class="status-value" id="proxy-server">nae2.proxi.es:2148</span>
                            </div>
                            <div class="status-item">
                                <span class="status-label">Proxy Type:</span>
                                <span class="status-value">Proxidize PGS Mobile Proxy</span>
                            </div>
                            <div class="status-item">
                                <span class="status-label">Total Rotations:</span>
                                <span class="status-value" id="rotation-count">0</span>
                            </div>
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 10px; margin-top: 10px;">
                        <button class="form-button" id="check-connection-btn">Check Connection</button>
                        <button class="form-button" id="rotate-ip-btn">Rotate IP Address</button>
                    </div>
                </div>
                
                <!-- Proxy Configuration Panel -->
                <div class="panel" style="margin-top: 20px;">
                    <h3>Proxy Configuration</h3>
                    <form id="proxy-config-form">
                        <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                            <div style="flex: 1; min-width: 300px;">
                                <div class="form-group">
                                    <label>HTTP Proxy (host:port)</label>
                                    <input type="text" class="form-control" id="http-proxy" value="nae2.proxi.es:2148">
                                </div>
                                <div class="form-group">
                                    <label>SOCKS Proxy (host:port)</label>
                                    <input type="text" class="form-control" id="socks-proxy" value="nae2.proxi.es:2149">
                                </div>
                            </div>
                            <div style="flex: 1; min-width: 300px;">
                                <div class="form-group">
                                    <label>Username</label>
                                    <input type="text" class="form-control" id="proxy-username" value="proxidize-4XauY">
                                </div>
                                <div class="form-group">
                                    <label>Password</label>
                                    <input type="password" class="form-control" id="proxy-password" value="4mhm9">
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label>IP Rotation URL</label>
                            <input type="text" class="form-control" id="rotation-url" value="https://api.proxidize.com/api/v1/modem-token-command/rotate-modem-ip/c0e684189bcd2697f0831fb47759e005/">
                        </div>
                        
                        <div style="margin-top: 20px; text-align: right;">
                            <button type="button" class="form-button secondary-button" id="test-config-btn" style="margin-right: 10px;">Test Configuration</button>
                            <button type="button" class="form-button" id="save-config-btn">Save Configuration</button>
                        </div>
                    </form>
                </div>
                
                <!-- IP Rotation Settings Panel -->
                <div class="panel" style="margin-top: 20px;">
                    <h3>IP Rotation Settings</h3>
                    
                    <div class="form-group">
                        <label>Auto-Rotation Strategy</label>
                        <select class="form-control" id="rotation-strategy">
                            <option value="none">Manual Only</option>
                            <option value="messages">Every X Messages</option>
                            <option value="time">Time-Based Rotation</option>
                        </select>
                    </div>
                    
                    <div id="messages-rotation-settings" style="display: none;">
                        <div class="form-group">
                            <label>Messages per IP Address</label>
                            <input type="number" class="form-control" value="50" min="1" max="1000">
                        </div>
                    </div>
                    
                    <div id="time-rotation-settings" style="display: none;">
                        <div class="form-group">
                            <label>Rotation Interval</label>
                            <select class="form-control">
                                <option value="30">Every 30 minutes</option>
                                <option value="60">Every 1 hour</option>
                                <option value="120">Every 2 hours</option>
                                <option value="240">Every 4 hours</option>
                                <option value="480">Every 8 hours</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="checkbox-group">
                        <label class="checkbox-label">
                            <input type="checkbox" class="checkbox-input" id="random-timing" checked>
                            Add random timing variation (±10%)
                        </label>
                        
                        <label class="checkbox-label">
                            <input type="checkbox" class="checkbox-input" id="verify-ip-changed" checked>
                            Verify IP changed after rotation
                        </label>
                        
                        <label class="checkbox-label">
                            <input type="checkbox" class="checkbox-input" id="log-ip-changes" checked>
                            Log all IP changes
                        </label>
                    </div>
                    
                    <div style="margin-top: 20px; text-align: right;">
                        <button class="form-button" id="save-rotation-settings">Save Settings</button>
                    </div>
                </div>
            </div>
        </div>
        
        <style>
            .status-item {
                margin-bottom: 10px;
                font-size: 14px;
            }
            
            .status-label {
                color: #AAA;
                display: inline-block;
                width: 140px;
            }
            
            .status-value {
                font-weight: bold;
                color: #EEE;
            }
            
            /* Status colors */
            .status-connected {
                color: #4CAF50 !important;
            }
            
            .status-error {
                color: #F44336 !important;
            }
        </style>
        
        <script>
            // Function to show status messages
            function showStatusMessage(message, type) {
                // Check if the message container exists, if not create it
                let messageContainer = document.getElementById('status-message-container');
                if (!messageContainer) {
                    messageContainer = document.createElement('div');
                    messageContainer.id = 'status-message-container';
                    messageContainer.style.position = 'fixed';
                    messageContainer.style.top = '20px';
                    messageContainer.style.right = '20px';
                    messageContainer.style.zIndex = '9999';
                    document.body.appendChild(messageContainer);
                }
                
                // Create message element
                const messageElement = document.createElement('div');
                let statusClass = 'status-success';
                if (type === 'error') {
                    statusClass = 'status-error';
                } else if (type === 'info') {
                    statusClass = 'status-info';
                }
                messageElement.className = 'status-message ' + statusClass;
                messageElement.style.padding = '12px 20px';
                messageElement.style.marginBottom = '10px';
                messageElement.style.borderRadius = '4px';
                let bgColor = '#4CAF50'; // Success green
                if (type === 'error') {
                    bgColor = '#f44336'; // Error red
                } else if (type === 'info') {
                    bgColor = '#2196F3'; // Info blue
                }
                messageElement.style.backgroundColor = bgColor;
                messageElement.style.color = 'white';
                messageElement.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
                messageElement.style.transition = 'all 0.3s ease';
                messageElement.textContent = message;
                
                // Add the message to the container
                messageContainer.appendChild(messageElement);
                
                // Remove the message after 5 seconds
                setTimeout(() => {
                    messageElement.style.opacity = '0';
                    setTimeout(() => {
                        if (messageContainer.contains(messageElement)) {
                            messageContainer.removeChild(messageElement);
                        }
                    }, 300);
                }, 5000);
            }
            
            // Device status polling for the proxy tab
            let statusPollInterval;
            
            function startPollingDeviceStatus() {
                // Initial load
                loadDeviceStatus();
                
                // Set up interval for polling
                statusPollInterval = setInterval(loadDeviceStatus, 10000); // Poll every 10 seconds
            }
            
            function stopPollingDeviceStatus() {
                if (statusPollInterval) {
                    clearInterval(statusPollInterval);
                }
            }
            
            function loadDeviceStatus() {
                fetch('/api/device/status')
                    .then(response => response.json())
                    .then(data => {
                        console.log('Device status data:', data);
                        
                        if (data.success) {
                            // Update UI elements with device status
                            const statusIndicator = document.getElementById('device-status-indicator');
                            const ipDisplay = document.getElementById('current-ip-display');
                            const ipCarrier = document.getElementById('ip-carrier');
                            const ipUsage = document.getElementById('ip-usage');
                            
                            if (statusIndicator) {
                                statusIndicator.style.backgroundColor = data.connected ? '#4CAF50' : '#F44336';
                            }
                            
                            if (ipDisplay && data.network_info && data.network_info.current_ip) {
                                ipDisplay.textContent = data.network_info.current_ip;
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Error checking device status:', error);
                    });
            }
            
            // Initialize Force Rotate IP button
            document.addEventListener('DOMContentLoaded', function() {
                const rotateButton = document.getElementById('force-rotate-ip-btn');
                if (rotateButton) {
                    // Remove any existing event listeners to prevent duplicates
                    rotateButton.removeEventListener('click', rotateProxidizeIP);
                    // Add the event listener
                    rotateButton.addEventListener('click', rotateProxidizeIP);
                    console.log("Force Rotate IP button initialized");
                }
                
                // Start polling for device status when proxy tab is shown
                const proxyTab = document.getElementById('tab-proxy-link');
                if (proxyTab) {
                    proxyTab.addEventListener('click', function() {
                        startPollingDeviceStatus();
                    });
                }
                
                // Load device status immediately
                loadDeviceStatus();
            });
            
            function rotateProxidizeIP() {
                console.log('Force Rotate IP button clicked!');
                
                const button = document.getElementById('force-rotate-ip-btn');
                const ipDisplay = document.getElementById('current-ip-display');
                const ipCarrier = document.getElementById('ip-carrier');
                const ipUsage = document.getElementById('ip-usage');
                const statusIndicator = document.getElementById('device-status-indicator');
                const rotationProgress = document.getElementById('rotation-progress');
                const rotationProgressBar = document.getElementById('rotation-progress-bar');
                
                if (!button || !ipDisplay) {
                    console.error('Unable to find required elements for IP rotation');
                    return;
                }
                
                // Create tooltip message for user feedback
                showStatusMessage('Initiating IP rotation...', 'info');
                
                // Disable button and show rotating state
                button.disabled = true;
                button.innerText = 'Rotating...';
                
                // Show rotating state in the UI
                if (statusIndicator) statusIndicator.style.backgroundColor = '#FFA000'; // Amber color
                if (ipDisplay) ipDisplay.textContent = 'Rotating...';
                if (ipCarrier) ipCarrier.textContent = '';
                if (ipUsage) ipUsage.textContent = '';
                
                // Show progress bar
                if (rotationProgress) rotationProgress.style.display = 'block';
                
                // Animate progress bar
                let progress = 0;
                const progressInterval = setInterval(() => {
                    progress += 5;
                    if (rotationProgressBar) rotationProgressBar.style.width = Math.min(progress, 95) + '%';
                    if (progress >= 100) clearInterval(progressInterval);
                }, 150);
                
                // Call API to rotate IP
                fetch('/api/device/refresh-ip', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Rotation API response:', data);
                    
                    // Complete the progress bar animation
                    if (rotationProgressBar) rotationProgressBar.style.width = '100%';
                    
                    setTimeout(() => {
                        if (data.success) {
                            // Update the IP display with new IP
                            if (statusIndicator) statusIndicator.style.backgroundColor = '#4CAF50'; // Green color
                            if (ipDisplay) ipDisplay.textContent = data.new_ip || 'IP Updated';
                            if (ipCarrier) ipCarrier.textContent = '(T-Mobile)';
                            if (ipUsage) ipUsage.textContent = 'New connection';
                            
                            // Show success message in a non-blocking way
                            showStatusMessage('IP rotated successfully to: ' + data.new_ip, 'success');
                        } else {
                            // Show error state
                            if (statusIndicator) statusIndicator.style.backgroundColor = '#F44336'; // Red color
                            if (ipDisplay) ipDisplay.textContent = 'Error';
                            
                            // Show error message
                            showStatusMessage('Failed to rotate IP: ' + (data.error || 'Unknown error'), 'error');
                        }
                        
                        // Re-enable button
                        button.disabled = false;
                        button.innerText = 'Force Rotate IP';
                        
                        // Hide progress bar after a delay
                        setTimeout(() => {
                            if (rotationProgress) rotationProgress.style.display = 'none';
                            if (rotationProgressBar) rotationProgressBar.style.width = '0%';
                        }, 1000);
                        
                        // Refresh device status after rotation
                        setTimeout(loadDeviceStatus, 2000);
                    }, 500);
                })
                .catch(error => {
                    console.error('Error rotating IP:', error);
                    
                    // Show error state
                    if (statusIndicator) statusIndicator.style.backgroundColor = '#F44336'; // Red color
                    if (ipDisplay) ipDisplay.textContent = 'Error';
                    
                    // Show error message
                    showStatusMessage('Error rotating IP. Please try again.', 'error');
                    
                    // Re-enable button
                    button.disabled = false;
                    button.innerText = 'Force Rotate IP';
                    
                    // Hide progress bar
                    setTimeout(() => {
                        if (rotationProgress) rotationProgress.style.display = 'none';
                        if (rotationProgressBar) rotationProgressBar.style.width = '0%';
                    }, 500);
                    
                    // Clear the interval
                    clearInterval(progressInterval);
                });
            }
            
            document.addEventListener('DOMContentLoaded', function() {
                // Elements
                const connectionStatus = document.getElementById('proxy-connection-status');
                const currentIp = document.getElementById('proxy-current-ip');
                const lastRotation = document.getElementById('proxy-last-rotation');
                const proxyServer = document.getElementById('proxy-server');
                const rotationCount = document.getElementById('rotation-count');
                const checkConnectionBtn = document.getElementById('check-connection-btn');
                const rotateIpBtn = document.getElementById('rotate-ip-btn');
                const saveConfigBtn = document.getElementById('save-config-btn');
                const testConfigBtn = document.getElementById('test-config-btn');
                const rotationStrategy = document.getElementById('rotation-strategy');
                const messagesRotationSettings = document.getElementById('messages-rotation-settings');
                const timeRotationSettings = document.getElementById('time-rotation-settings');
                
                // Message Elements
                const sendMessageBtn = document.getElementById('send-message-btn');
                const accountSelector = document.getElementById('account-selector');
                const recipientNumber = document.getElementById('recipient-number');
                const messageContent = document.getElementById('message-content');
                const messageStatus = document.getElementById('message-status');
                
                // Load initial proxy status
                function loadProxyStatus() {
                    fetch('/api/device/status')
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                // Update status elements
                                if (data.connected) {
                                    connectionStatus.innerText = 'Connected';
                                    connectionStatus.className = 'status-value status-connected';
                                } else {
                                    connectionStatus.innerText = 'Disconnected';
                                    connectionStatus.className = 'status-value status-error';
                                }
                                
                                // Check if proxy_info exists (proxidize is active)
                                if (data.proxy_info) {
                                    proxyServer.innerText = data.proxy_info.server || 'Unknown';
                                    currentIp.innerText = data.network_info.current_ip || 'Unknown';
                                    lastRotation.innerText = data.network_info.last_rotation || 'Unknown';
                                    rotationCount.innerText = data.network_info.rotation_count || '0';
                                } else {
                                    // Fallback for device manager
                                    currentIp.innerText = data.network_info.current_ip || 'Unknown';
                                }
                            } else {
                                connectionStatus.innerText = 'Error: ' + (data.error || 'Unknown error');
                                connectionStatus.className = 'status-value status-error';
                            }
                        })
                        .catch(error => {
                            console.error('Error loading proxy status:', error);
                            connectionStatus.innerText = 'Connection Error';
                            connectionStatus.className = 'status-value status-error';
                        });
                }
                
                // Load proxy configuration
                function loadProxyConfig() {
                    fetch('/api/proxy/config')
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                // Update form fields
                                document.getElementById('http-proxy').value = data.http_proxy || '';
                                document.getElementById('socks-proxy').value = data.socks_proxy || '';
                                document.getElementById('proxy-username').value = data.username || '';
                                document.getElementById('rotation-url').value = data.rotation_url || '';
                            }
                        })
                        .catch(error => {
                            console.error('Error loading proxy configuration:', error);
                        });
                }
                
                // Save proxy configuration
                function saveProxyConfig() {
                    saveConfigBtn.disabled = true;
                    saveConfigBtn.innerText = 'Saving...';
                    
                    const config = {
                        http_proxy: document.getElementById('http-proxy').value,
                        socks_proxy: document.getElementById('socks-proxy').value,
                        username: document.getElementById('proxy-username').value,
                        password: document.getElementById('proxy-password').value,
                        rotation_url: document.getElementById('rotation-url').value
                    };
                    
                    fetch('/api/proxy/config', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(config)
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showStatusMessage('Proxy configuration saved successfully', 'success');
                        } else {
                            showStatusMessage('Error saving configuration: ' + data.error, 'error');
                        }
                        
                        saveConfigBtn.disabled = false;
                        saveConfigBtn.innerText = 'Save Configuration';
                    })
                    .catch(error => {
                        console.error('Error saving configuration:', error);
                        showStatusMessage('Error saving configuration', 'error');
                        
                        saveConfigBtn.disabled = false;
                        saveConfigBtn.innerText = 'Save Configuration';
                    });
                }
                
                // Test proxy connection
                function testProxyConnection() {
                    checkConnectionBtn.disabled = true;
                    checkConnectionBtn.innerText = 'Checking...';
                    
                    fetch('/api/proxy/check')
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                showStatusMessage('Proxy connection successful: ' + data.ip, 'success');
                                connectionStatus.innerText = 'Connected';
                                connectionStatus.className = 'status-value status-connected';
                                currentIp.innerText = data.ip || 'Unknown';
                            } else {
                                showStatusMessage('Proxy connection failed: ' + data.message, 'error');
                                connectionStatus.innerText = 'Disconnected';
                                connectionStatus.className = 'status-value status-error';
                            }
                            
                            checkConnectionBtn.disabled = false;
                            checkConnectionBtn.innerText = 'Check Connection';
                        })
                        .catch(error => {
                            console.error('Error testing connection:', error);
                            showStatusMessage('Error testing connection', 'error');
                            
                            checkConnectionBtn.disabled = false;
                            checkConnectionBtn.innerText = 'Check Connection';
                        });
                }
                
                // Rotate IP address with animation and improved feedback
                function rotateIpAddress() {
                    rotateIpBtn.disabled = true;
                    rotateIpBtn.innerText = 'Rotating...';
                    
                    // Show a rotating animation in the IP field
                    const originalIp = currentIp.innerText;
                    currentIp.innerHTML = '<span class="rotating-text">Rotating IP...</span>';
                    
                    // Create and add CSS for rotation animation if it doesn't exist
                    if (!document.getElementById('rotation-animation-style')) {
                        const style = document.createElement('style');
                        style.id = 'rotation-animation-style';
                        style.textContent = `
                            @keyframes rotatingAnimation {
                                0% { opacity: 1; }
                                50% { opacity: 0.5; }
                                100% { opacity: 1; }
                            }
                            .rotating-text {
                                animation: rotatingAnimation 1s infinite;
                                color: #ff6b00;
                                font-weight: bold;
                            }
                        `;
                        document.head.appendChild(style);
                    }
                    
                    // Show status as processing
                    showStatusMessage('Sending IP rotation command to Proxidize...', 'info');
                    
                    fetch('/api/device/refresh-ip', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showStatusMessage('IP rotation successful: ' + data.new_ip, 'success');
                            currentIp.innerText = data.new_ip || 'Unknown';
                            lastRotation.innerText = 'Just now';
                            
                            // Highlight the new IP with a brief flash animation
                            currentIp.style.transition = 'background-color 1s';
                            currentIp.style.backgroundColor = '#e6ffe6';
                            setTimeout(() => {
                                currentIp.style.backgroundColor = 'transparent';
                            }, 1500);
                            
                            // Update rotation count
                            const count = parseInt(rotationCount.innerText) || 0;
                            rotationCount.innerText = (count + 1).toString();
                        } else {
                            showStatusMessage('IP rotation failed: ' + data.error, 'error');
                            currentIp.innerText = originalIp; // Restore original IP
                        }
                        
                        rotateIpBtn.disabled = false;
                        rotateIpBtn.innerText = 'Rotate IP Address';
                    })
                    .catch(error => {
                        console.error('Error rotating IP:', error);
                        showStatusMessage('Error rotating IP: ' + error.message, 'error');
                        currentIp.innerText = originalIp; // Restore original IP
                        
                        rotateIpBtn.disabled = false;
                        rotateIpBtn.innerText = 'Rotate IP Address';
                    });
                }
                
                // Handle rotation strategy change
                rotationStrategy.addEventListener('change', function() {
                    const strategy = this.value;
                    
                    // Hide all settings
                    messagesRotationSettings.style.display = 'none';
                    timeRotationSettings.style.display = 'none';
                    
                    // Show selected strategy settings
                    if (strategy === 'messages') {
                        messagesRotationSettings.style.display = 'block';
                    } else if (strategy === 'time') {
                        timeRotationSettings.style.display = 'block';
                    }
                });
                
                // Message Sending Functionality
                function sendMessage() {
                    // Validate inputs
                    const account_id = accountSelector.value;
                    const recipient = recipientNumber.value.trim();
                    const content = messageContent.value.trim();
                    
                    if (!recipient) {
                        showMessageStatus('Please enter a recipient phone number', 'error');
                        return;
                    }
                    
                    if (!content) {
                        showMessageStatus('Please enter a message', 'error');
                        return;
                    }
                    
                    // Disable button during sending
                    sendMessageBtn.disabled = true;
                    sendMessageBtn.innerText = 'Sending...';
                    
                    // Clear previous status
                    messageStatus.style.display = 'none';
                    
                    // Send API request
                    fetch('/api/send-message', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            account_id: account_id,
                            recipient: recipient,
                            content: content
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showMessageStatus('Message sent successfully!', 'success');
                            // Clear form
                            messageContent.value = '';
                        } else {
                            showMessageStatus('Error sending message: ' + data.error, 'error');
                        }
                        
                        // Re-enable button
                        sendMessageBtn.disabled = false;
                        sendMessageBtn.innerText = 'Send Message';
                    })
                    .catch(error => {
                        console.error('Error sending message:', error);
                        showMessageStatus('Error sending message. Please try again.', 'error');
                        
                        // Re-enable button
                        sendMessageBtn.disabled = false;
                        sendMessageBtn.innerText = 'Send Message';
                    });
                }
                
                // Display message status
                function showMessageStatus(message, type) {
                    messageStatus.innerText = message;
                    messageStatus.style.display = 'block';
                    
                    if (type === 'success') {
                        messageStatus.style.backgroundColor = '#4CAF5033';
                        messageStatus.style.color = '#4CAF50';
                        messageStatus.style.border = '1px solid #4CAF50';
                    } else {
                        messageStatus.style.backgroundColor = '#F4433633';
                        messageStatus.style.color = '#F44336';
                        messageStatus.style.border = '1px solid #F44336';
                    }
                }
                
                // Attach event listeners
                if (checkConnectionBtn) checkConnectionBtn.addEventListener('click', testProxyConnection);
                if (rotateIpBtn) rotateIpBtn.addEventListener('click', rotateIpAddress);
                if (saveConfigBtn) saveConfigBtn.addEventListener('click', saveProxyConfig);
                if (testConfigBtn) testConfigBtn.addEventListener('click', testProxyConnection);
                if (sendMessageBtn) sendMessageBtn.addEventListener('click', sendMessage);
                
                // Save rotation settings
                const saveRotationSettingsBtn = document.getElementById('save-rotation-settings');
                if (saveRotationSettingsBtn) {
                    saveRotationSettingsBtn.addEventListener('click', function() {
                        showStatusMessage('Rotation settings saved successfully', 'success');
                    });
                }
                
                // Function to load proxy configuration
                function loadProxyConfig() {
                    fetch('/api/proxy/config', {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Populate form fields if they exist
                            const httpProxyInput = document.getElementById('http-proxy-input');
                            const socksProxyInput = document.getElementById('socks-proxy-input');
                            const usernameInput = document.getElementById('proxy-username-input');
                            const rotationUrlInput = document.getElementById('rotation-url-input');
                            
                            if (httpProxyInput) httpProxyInput.value = data.http_proxy || '';
                            if (socksProxyInput) socksProxyInput.value = data.socks_proxy || '';
                            if (usernameInput) usernameInput.value = data.username || '';
                            if (rotationUrlInput) rotationUrlInput.value = data.rotation_url || '';
                            
                            console.log('Proxy config loaded successfully');
                        } else {
                            console.error('Error loading proxy config:', data.error);
                        }
                    })
                    .catch(error => {
                        console.error('Error loading proxy config:', error);
                    });
                }
                
                // Initial load
                loadProxyStatus();
                loadProxyConfig();
                
                // Proxidize Config Management
                const loadProxyConfigBtn = document.getElementById('load-proxy-config');
                const saveProxyConfigBtn = document.getElementById('save-proxy-config');
                
                if (loadProxyConfigBtn) {
                    loadProxyConfigBtn.addEventListener('click', function() {
                        // Fetch the current configuration
                        fetch('/api/proxy/config', {
                            method: 'GET',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                // Populate form fields
                                document.getElementById('http-proxy-input').value = data.http_proxy || '';
                                document.getElementById('socks-proxy-input').value = data.socks_proxy || '';
                                document.getElementById('proxy-username-input').value = data.username || '';
                                document.getElementById('rotation-url-input').value = data.rotation_url || '';
                                
                                // Password is not returned for security reasons
                                document.getElementById('proxy-password-input').value = '';
                                
                                showStatusMessage('Configuration loaded successfully', 'success');
                            } else {
                                showStatusMessage('Error loading configuration: ' + data.error, 'error');
                            }
                        })
                        .catch(error => {
                            console.error('Error loading proxy config:', error);
                            showStatusMessage('Connection error while loading configuration', 'error');
                        });
                    });
                }
                
                if (saveProxyConfigBtn) {
                    saveProxyConfigBtn.addEventListener('click', function() {
                        // Gather form data
                        const configData = {
                            http_proxy: document.getElementById('http-proxy-input').value,
                            socks_proxy: document.getElementById('socks-proxy-input').value,
                            username: document.getElementById('proxy-username-input').value,
                            password: document.getElementById('proxy-password-input').value,
                            rotation_url: document.getElementById('rotation-url-input').value
                        };
                        
                        // Send to backend
                        fetch('/api/proxy/config', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(configData)
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                showStatusMessage('Configuration saved successfully', 'success');
                                
                                // Clear password for security
                                document.getElementById('proxy-password-input').value = '';
                            } else {
                                showStatusMessage('Error saving configuration: ' + data.error, 'error');
                            }
                        })
                        .catch(error => {
                            console.error('Error saving proxy config:', error);
                            showStatusMessage('Connection error while saving configuration', 'error');
                        });
                    });
                }
                
                // Load the configuration on page load
                fetch('/api/proxy/config', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Populate form fields
                        document.getElementById('http-proxy-input').value = data.http_proxy || '';
                        document.getElementById('socks-proxy-input').value = data.socks_proxy || '';
                        document.getElementById('proxy-username-input').value = data.username || '';
                        document.getElementById('rotation-url-input').value = data.rotation_url || '';
                    }
                })
                .catch(error => {
                    console.error('Error auto-loading proxy config:', error);
                });
                
                // Force Rotate IP button
                const forceRotateIpBtn = document.getElementById('force-rotate-ip-btn');
                if (forceRotateIpBtn) {
                    forceRotateIpBtn.addEventListener('click', function() {
                        // Show rotation in progress
                        this.disabled = true;
                        this.innerText = 'Rotating...';
                        
                        // Call the rotation API
                        fetch('/api/device/refresh-ip', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            }
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                // Update the display with new IP
                                document.getElementById('current-ip-display').textContent = data.new_ip || 'IP updated';
                                showStatusMessage('IP rotated successfully', 'success');
                            } else {
                                showStatusMessage('Failed to rotate IP: ' + (data.error || 'Unknown error'), 'error');
                            }
                            
                            // Re-enable the button
                            this.disabled = false;
                            this.innerText = 'Force Rotate IP';
                            
                            // Refresh status after rotation
                            setTimeout(() => {
                                loadProxyStatus();
                            }, 2000);
                        })
                        .catch(error => {
                            console.error('Error during IP rotation:', error);
                            showStatusMessage('Connection error during IP rotation', 'error');
                            
                            // Re-enable the button
                            this.disabled = false;
                            this.innerText = 'Force Rotate IP';
                        });
                    });
                }
                
                // Proxidize Direct API Test Button
                const testDirectProxidizeButton = document.getElementById('test-direct-proxidize');
                if (testDirectProxidizeButton) {
                    testDirectProxidizeButton.addEventListener('click', function() {
                        const resultElement = document.getElementById('proxidize-test-result');
                        resultElement.textContent = 'Testing...';
                        resultElement.style.backgroundColor = '#FFE0B2';
                        resultElement.style.color = '#E65100';
                        
                        // Make API call to backend to test direct Proxidize connection
                        fetch('/api/device/direct-rotation-test', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                        })
                        .then(response => response.json())
                        .then(data => {
                            console.log('Direct API test result:', data);
                            
                            if (data.success) {
                                resultElement.textContent = 'Success! Status: ' + data.status_code;
                                resultElement.style.backgroundColor = '#E8F5E9';
                                resultElement.style.color = '#2E7D32';
                                
                                // Create modal to show detailed results
                                const modal = document.createElement('div');
                                modal.style.position = 'fixed';
                                modal.style.top = '0';
                                modal.style.left = '0';
                                modal.style.width = '100%';
                                modal.style.height = '100%';
                                modal.style.backgroundColor = 'rgba(0,0,0,0.7)';
                                modal.style.zIndex = '1000';
                                modal.style.display = 'flex';
                                modal.style.justifyContent = 'center';
                                modal.style.alignItems = 'center';
                                
                                const modalContent = document.createElement('div');
                                modalContent.style.backgroundColor = 'white';
                                modalContent.style.padding = '20px';
                                modalContent.style.borderRadius = '5px';
                                modalContent.style.maxWidth = '800px';
                                modalContent.style.width = '80%';
                                modalContent.style.maxHeight = '80vh';
                                modalContent.style.overflowY = 'auto';
                                
                                const closeBtn = document.createElement('button');
                                closeBtn.innerText = 'Close';
                                closeBtn.className = 'form-button';
                                closeBtn.style.marginTop = '15px';
                                closeBtn.style.float = 'right';
                                
                                modalContent.innerHTML = `
                                    <h3 style="color: #FF6600; margin-top: 0;">Proxidize API Test Results</h3>
                                    <div style="margin-bottom: 15px;">
                                        <strong>Rotation URL:</strong> ${data.rotation_url}
                                    </div>
                                    <div style="margin-bottom: 15px;">
                                        <strong>Status Code:</strong> ${data.status_code}
                                    </div>
                                    <div>
                                        <strong>Response:</strong>
                                        <pre style="background-color: #F5F5F5; padding: 10px; overflow: auto; max-height: 300px; border-radius: 5px;">${data.response_body}</pre>
                                    </div>
                                `;
                                
                                modalContent.appendChild(closeBtn);
                                modal.appendChild(modalContent);
                                document.body.appendChild(modal);
                                
                                closeBtn.addEventListener('click', function() {
                                    document.body.removeChild(modal);
                                });
                                
                                modal.addEventListener('click', function(e) {
                                    if (e.target === modal) {
                                        document.body.removeChild(modal);
                                    }
                                });
                            } else {
                                resultElement.textContent = 'Error: ' + (data.error || 'Unknown error');
                                resultElement.style.backgroundColor = '#FFEBEE';
                                resultElement.style.color = '#C62828';
                                
                                // Show error details
                                const modal = document.createElement('div');
                                modal.style.position = 'fixed';
                                modal.style.top = '0';
                                modal.style.left = '0';
                                modal.style.width = '100%';
                                modal.style.height = '100%';
                                modal.style.backgroundColor = 'rgba(0,0,0,0.7)';
                                modal.style.zIndex = '1000';
                                modal.style.display = 'flex';
                                modal.style.justifyContent = 'center';
                                modal.style.alignItems = 'center';
                                
                                const modalContent = document.createElement('div');
                                modalContent.style.backgroundColor = 'white';
                                modalContent.style.padding = '20px';
                                modalContent.style.borderRadius = '5px';
                                modalContent.style.maxWidth = '800px';
                                modalContent.style.width = '80%';
                                
                                const closeBtn = document.createElement('button');
                                closeBtn.innerText = 'Close';
                                closeBtn.className = 'form-button';
                                closeBtn.style.marginTop = '15px';
                                closeBtn.style.float = 'right';
                                
                                modalContent.innerHTML = `
                                    <h3 style="color: #FF6600; margin-top: 0;">Proxidize API Test Error</h3>
                                    <div style="color: #C62828; margin-bottom: 15px;">
                                        <strong>Error:</strong> ${data.error || 'Unknown error occurred'}
                                    </div>
                                `;
                                
                                modalContent.appendChild(closeBtn);
                                modal.appendChild(modalContent);
                                document.body.appendChild(modal);
                                
                                closeBtn.addEventListener('click', function() {
                                    document.body.removeChild(modal);
                                });
                                
                                modal.addEventListener('click', function(e) {
                                    if (e.target === modal) {
                                        document.body.removeChild(modal);
                                    }
                                });
                            }
                        })
                        .catch(error => {
                            console.error('Error testing Proxidize API:', error);
                            resultElement.textContent = 'Connection error';
                            resultElement.style.backgroundColor = '#FFEBEE';
                            resultElement.style.color = '#C62828';
                        });
                    });
                }
            });
        </script>
        '''
    )

@app.route('/anti-detection')
def anti_detection_route():
    """The advanced anti-detection systems page"""
    process_assets()
    return render_template_string(
        BASE_HTML,
        title="Anti-Detection Systems",
        active_page="/anti-detection",
        content='''
        <div class="app-container">
            <div class="app-content">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <div style="font-size: 20px; font-weight: bold; color: #EEE;">Advanced Anti-Detection Systems</div>
                    <div>
                        <button class="form-button secondary-button">Reset to Default</button>
                        <button class="form-button">Save Settings</button>
                    </div>
                </div>
                
                <div style="display: flex; gap: 20px; height: calc(100% - 60px);">
                    <!-- Settings Categories -->
                    <div style="width: 250px;">
                        <div style="background-color: #252525; border-radius: 6px; padding: 0; overflow: hidden;">
                            <div class="tabs" style="flex-direction: column; background-color: transparent; border-bottom: none;">
                                <div class="tab active" data-tab="browser">Browser Fingerprinting</div>
                                <div class="tab" data-tab="device">Device Simulation</div>
                                <div class="tab" data-tab="proxy">Proxy Management</div>
                                <div class="tab" data-tab="captcha">Captcha Handling</div>
                                <div class="tab" data-tab="automation">Automation Resilience</div>
                                <div class="tab" data-tab="aging">Account Aging</div>
                                <div class="tab" data-tab="android">Android Emulation</div>
                                <div class="tab" data-tab="profiles">System Profiles</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Settings Panel -->
                    <div style="flex: 1;">
                        <div style="background-color: #252525; border-radius: 6px; padding: 20px; height: 100%; overflow: auto;">
                            <!-- Browser Fingerprinting Tab Content -->
                            <div id="tab-browser" class="tab-content" style="display: block;">
                            <h3 style="margin-top: 0; color: #FF6600; font-size: 18px;">Browser Fingerprint Randomization</h3>
                            
                            <div style="margin-bottom: 20px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <label class="form-label" style="margin: 0;">Enable Fingerprint Randomization</label>
                                    <label class="switch">
                                        <input type="checkbox" checked>
                                        <span class="slider round"></span>
                                    </label>
                                </div>
                                <div style="font-size: 13px; color: #AAA; margin-left: 0;">
                                    Creates unique, persistent fingerprints for each account to avoid detection
                                </div>
                            </div>
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                                <div>
                                    <label class="form-label">User-Agent Rotation</label>
                                    <select class="form-select">
                                        <option selected>Per Account (Consistent)</option>
                                        <option>Per Session</option>
                                        <option>Per Request</option>
                                        <option>Disabled</option>
                                    </select>
                                    <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                        Controls how user-agent strings are rotated
                                    </div>
                                </div>
                                
                                <div>
                                    <label class="form-label">Canvas Fingerprint Variation</label>
                                    <select class="form-select">
                                        <option selected>Subtle Noise</option>
                                        <option>Complete Randomization</option>
                                        <option>Consistent per Account</option>
                                        <option>Disabled</option>
                                    </select>
                                    <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                        Prevents canvas-based fingerprinting detection
                                    </div>
                                </div>
                                
                                <div>
                                    <label class="form-label">WebRTC Protection</label>
                                    <select class="form-select">
                                        <option selected>Enabled (Prevent IP Leaks)</option>
                                        <option>Disabled</option>
                                    </select>
                                    <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                        Prevents IP address leaks through WebRTC
                                    </div>
                                </div>
                                
                                <div>
                                    <label class="form-label">Font Fingerprinting Protection</label>
                                    <select class="form-select">
                                        <option selected>Enabled (Randomize Fonts)</option>
                                        <option>Consistent per Account</option>
                                        <option>Disabled</option>
                                    </select>
                                    <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                        Randomizes available fonts to prevent fingerprinting
                                    </div>
                                </div>
                                
                                <div>
                                    <label class="form-label">Timezone/Locale Consistency</label>
                                    <select class="form-select">
                                        <option>Auto (Based on IP)</option>
                                        <option selected>Fixed per Account</option>
                                        <option>Random per Session</option>
                                    </select>
                                    <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                        Maintains consistent timezone and locale settings
                                    </div>
                                </div>
                                
                                <div>
                                    <label class="form-label">Header Manipulation</label>
                                    <select class="form-select">
                                        <option selected>Smart (Anti-Detection)</option>
                                        <option>Minimal (Performance)</option>
                                        <option>Maximum (Security)</option>
                                        <option>Disabled</option>
                                    </select>
                                    <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                        Customizes HTTP headers to avoid detection
                                    </div>
                                </div>
                            </div>
                            
                            <h3 style="color: #FF6600; font-size: 18px;">Behavioral Patterns</h3>
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                                <div>
                                    <label class="form-label">Mouse Movement Simulation</label>
                                    <select class="form-select">
                                        <option selected>Realistic (Human-like)</option>
                                        <option>Optimized (Faster)</option>
                                        <option>Minimal (Performance)</option>
                                        <option>Disabled</option>
                                    </select>
                                    <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                        Generates human-like cursor movement patterns
                                    </div>
                                </div>
                                
                                <div>
                                    <label class="form-label">Keyboard Typing Patterns</label>
                                    <select class="form-select">
                                        <option selected>Natural (Human-like)</option>
                                        <option>Consistent Speed</option>
                                        <option>Disabled</option>
                                    </select>
                                    <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                        Simulates realistic human typing rhythms
                                    </div>
                                </div>
                                
                                <div>
                                    <label class="form-label">Page Scroll Behavior</label>
                                    <select class="form-select">
                                        <option selected>Natural Scrolling</option>
                                        <option>Optimized (Faster)</option>
                                        <option>Disabled</option>
                                    </select>
                                    <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                        Simulates human-like page scrolling patterns
                                    </div>
                                </div>
                                
                                <div>
                                    <label class="form-label">Navigation Timing</label>
                                    <select class="form-select">
                                        <option selected>Variable (Human-like)</option>
                                        <option>Optimized (Faster)</option>
                                        <option>Fixed Intervals</option>
                                    </select>
                                    <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                        Controls timing between navigation actions
                                    </div>
                                </div>
                            </div>
                            
                            <h3 style="color: #FF6600; font-size: 18px;">Advanced Settings</h3>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Fingerprint Persistence</label>
                                <select class="form-select">
                                    <option selected>Persistent per Account</option>
                                    <option>Session Only</option>
                                    <option>Rotating Schedule</option>
                                </select>
                                <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                    Controls how long the same fingerprint is used for an account
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Hardware Acceleration</label>
                                <select class="form-select">
                                    <option selected>Enabled (WebGL Fingerprinting Protected)</option>
                                    <option>Disabled</option>
                                </select>
                                <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                    Controls WebGL and hardware acceleration features
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label class="form-label">Audio Fingerprinting Protection</label>
                                <select class="form-select">
                                    <option selected>Enabled</option>
                                    <option>Disabled</option>
                                </select>
                                <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                    Prevents audio context-based browser fingerprinting
                                </div>
                            </div>
                            
                            <div style="text-align: right; margin-top: 30px;">
                                <button class="form-button secondary-button">Reset Tab</button>
                                <button class="form-button">Apply Changes</button>
                            </div>
                            </div>
                            
                            <!-- Proxy Management Tab Content -->
                            <div id="tab-proxy" class="tab-content" style="display: none;">
                                <h3 style="margin-top: 0; color: #FF6600; font-size: 18px;">Advanced Proxy Management</h3>
                                
                                <div style="margin-bottom: 20px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <label class="form-label" style="margin: 0;">Enable Mobile IP Rotation</label>
                                        <label class="switch">
                                            <input type="checkbox" checked>
                                            <span class="slider round"></span>
                                        </label>
                                    </div>
                                    <div style="font-size: 13px; color: #AAA; margin-left: 0;">
                                        Automatically rotate mobile IPs to avoid detection and blocks
                                    </div>
                                </div>

                                <div style="margin-bottom: 20px; border: 1px solid #FF6600; border-radius: 5px; padding: 15px; background-color: #FFF3E0;">
                                    <h4 style="margin-top: 0; color: #FF6600; font-size: 16px;">Proxidize API Configuration</h4>
                                    <div>
                                        <div style="margin-bottom: 15px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                            <div>
                                                <label class="form-label">HTTP Proxy Server</label>
                                                <input type="text" class="form-input" id="http-proxy-input" placeholder="host:port">
                                            </div>
                                            <div>
                                                <label class="form-label">SOCKS Proxy Server</label>
                                                <input type="text" class="form-input" id="socks-proxy-input" placeholder="host:port">
                                            </div>
                                        </div>
                                        <div style="margin-bottom: 15px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                            <div>
                                                <label class="form-label">Username</label>
                                                <input type="text" class="form-input" id="proxy-username-input">
                                            </div>
                                            <div>
                                                <label class="form-label">Password</label>
                                                <input type="password" class="form-input" id="proxy-password-input">
                                            </div>
                                        </div>
                                        <div style="margin-bottom: 15px;">
                                            <label class="form-label">Rotation URL</label>
                                            <input type="text" class="form-input" id="rotation-url-input" style="width: 100%;" placeholder="https://api.proxidize.com/...">
                                        </div>
                                        <div style="display: flex; justify-content: flex-end; gap: 10px;">
                                            <button id="load-proxy-config" class="form-button secondary-button">Load Current Config</button>
                                            <button id="save-proxy-config" class="form-button">Save Configuration</button>
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 20px; border: 1px solid #FF6600; border-radius: 5px; padding: 15px; background-color: #FFF3E0;">
                                    <h4 style="margin-top: 0; color: #FF6600; font-size: 16px;">Proxidize API Connection Test</h4>
                                    <p style="font-size: 13px; margin: 10px 0;">
                                        Test direct connection to Proxidize API to verify configuration
                                    </p>
                                    <div style="display: flex; gap: 10px;">
                                        <button id="test-direct-proxidize" class="form-button">Test Direct API Connection</button>
                                        <div id="proxidize-test-result" style="margin-left: 10px; padding: 5px 10px; border-radius: 3px;"></div>
                                    </div>
                                </div>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                                    <div>
                                        <label class="form-label">IP Rotation Method</label>
                                        <select class="form-select">
                                            <option selected>Airplane Mode Toggle (Android)</option>
                                            <option>APN Reset (Android)</option>
                                            <option>Mobile Data Restart</option>
                                            <option>Manual Proxy Configuration</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Method used to obtain new IPs
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Rotation Schedule</label>
                                        <select class="form-select">
                                            <option>Every 10 messages</option>
                                            <option selected>Every 25 messages</option>
                                            <option>Every 50 messages</option>
                                            <option>Every 2 hours</option>
                                            <option>Custom Schedule</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Controls when the system will rotate to a new IP
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Mobile Carrier Targeting</label>
                                        <select class="form-select">
                                            <option selected>Auto-Detect</option>
                                            <option>T-Mobile</option>
                                            <option>Verizon</option>
                                            <option>AT&T</option>
                                            <option>Sprint</option>
                                            <option>Other (Specify)</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Detects and categorizes mobile carriers
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">IP Reputation Monitoring</label>
                                        <select class="form-select">
                                            <option selected>Enabled (Auto-Blacklist Flagged IPs)</option>
                                            <option>Monitoring Only</option>
                                            <option>Disabled</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Tracks which IPs get flagged and auto-blacklists them
                                        </div>
                                    </div>
                                </div>
                                
                                <h3 style="color: #FF6600; font-size: 18px;">Mobile Device Settings</h3>
                                
                                <div style="margin-bottom: 15px;">
                                    <label class="form-label">Connected Android Device</label>
                                    <select class="form-select">
                                        <option selected>BLU G44 (Auto-Detected)</option>
                                        <option>Samsung Galaxy A12</option>
                                        <option>Motorola Moto G7</option>
                                        <option>Other (Custom Configuration)</option>
                                    </select>
                                    <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                        The Android device used for IP rotation
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <label class="form-label">ADB Connection Mode</label>
                                    <select class="form-select">
                                        <option selected>USB (Physical Connection)</option>
                                        <option>Wireless (ADB over Wi-Fi)</option>
                                        <option>Scrcpy Integration</option>
                                    </select>
                                </div>
                                
                                <div style="margin-bottom: 20px;">
                                    <label class="form-label">IP Change Verification</label>
                                    <select class="form-select">
                                        <option selected>Verify IP Change (Recommended)</option>
                                        <option>Assume Success</option>
                                    </select>
                                    <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                        Verifies that the IP actually changed after rotation
                                    </div>
                                </div>
                                
                                <div style="display: flex; align-items: center; background-color: #2A2A2A; padding: 15px; border-radius: 6px; margin-bottom: 25px;">
                                    <div id="device-status-indicator" style="border-radius: 50%; width: 12px; height: 12px; background-color: #00C853; margin-right: 10px;"></div>
                                    <div>
                                        <div style="font-weight: bold; color: #EEE;">BLU G44 Device Connected</div>
                                        <div style="font-size: 13px; color: #AAA;">
                                            Current IP: <span id="current-ip-display">174.220.10.112</span> 
                                            <span id="ip-carrier">(T-Mobile)</span> - 
                                            <span id="ip-usage">Used for 17 messages</span>
                                            <div id="rotation-progress" style="display: none; margin-top: 5px;">
                                                <div style="width: 100%; background-color: #444; height: 4px; border-radius: 2px;">
                                                    <div id="rotation-progress-bar" style="width: 0%; background-color: #FF6600; height: 4px; border-radius: 2px; transition: width 0.3s;"></div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <button id="force-rotate-ip-btn" class="form-button secondary-button" style="margin-left: auto;" onclick="rotateProxidizeIP(); return false;">Force Rotate IP</button>
                                </div>
                                
                                <h3 style="color: #FF6600; font-size: 18px;">IP Analysis & Blacklisting</h3>
                                
                                <div style="margin-bottom: 20px;">
                                    <label class="form-label">IP Blacklist Source</label>
                                    <select class="form-select">
                                        <option selected>Local + External Blacklists</option>
                                        <option>Local Blacklist Only</option>
                                        <option>Disabled</option>
                                    </select>
                                    <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                        Source of IP blacklist data for checking
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <label class="form-label">Geographic Distribution</label>
                                    <select class="form-select">
                                        <option selected>United States (Florida Focus)</option>
                                        <option>United States (All Regions)</option>
                                        <option>North America</option>
                                        <option>Custom Region Set</option>
                                    </select>
                                </div>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                                    <div>
                                        <label class="form-label">Connection Testing</label>
                                        <select class="form-select">
                                            <option selected>Full Test Before Use</option>
                                            <option>Basic Connectivity Only</option>
                                            <option>Disabled (Not Recommended)</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Tests IP connections before using them
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Latency Optimization</label>
                                        <select class="form-select">
                                            <option selected>Auto-Select Fastest Connection</option>
                                            <option>Prioritize IP Freshness</option>
                                            <option>Balance Speed & Freshness</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Optimizes for fastest network connections
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="text-align: right; margin-top: 30px;">
                                    <button class="form-button secondary-button">Reset Tab</button>
                                    <button class="form-button">Apply Changes</button>
                                </div>
                            </div>
                            
                            <!-- Captcha Handling Tab Content -->
                            <div id="tab-captcha" class="tab-content" style="display: none;">
                                <h3 style="margin-top: 0; color: #FF6600; font-size: 18px;">Captcha & Challenge Handling</h3>
                                
                                <div style="margin-bottom: 20px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <label class="form-label" style="margin: 0;">Enable Automated Captcha Solving</label>
                                        <label class="switch">
                                            <input type="checkbox" checked>
                                            <span class="slider round"></span>
                                        </label>
                                    </div>
                                    <div style="font-size: 13px; color: #AAA; margin-left: 0;">
                                        When enabled, the system will attempt to automatically solve captchas using selected services
                                    </div>
                                </div>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                                    <div>
                                        <label class="form-label">Primary Solving Service</label>
                                        <select class="form-select">
                                            <option selected>2Captcha</option>
                                            <option>Anti-Captcha</option>
                                            <option>CapMonster</option>
                                            <option>DeathByCaptcha</option>
                                            <option>Custom API Integration</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Primary service used for solving captchas
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">API Key</label>
                                        <div style="display: flex; gap: 5px;">
                                            <input type="password" class="form-input" value="••••••••••••••••" style="flex: 1;">
                                            <button class="form-button secondary-button" style="white-space: nowrap;">Test API</button>
                                        </div>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            API key for the selected captcha solving service
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Backup Solving Service</label>
                                        <select class="form-select">
                                            <option>None</option>
                                            <option selected>Anti-Captcha</option>
                                            <option>2Captcha</option>
                                            <option>CapMonster</option>
                                            <option>DeathByCaptcha</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Used if primary service fails or times out
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Backup API Key</label>
                                        <div style="display: flex; gap: 5px;">
                                            <input type="password" class="form-input" value="••••••••••••••••" style="flex: 1;">
                                            <button class="form-button secondary-button" style="white-space: nowrap;">Test API</button>
                                        </div>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            API key for the backup captcha solving service
                                        </div>
                                    </div>
                                </div>
                                
                                <h3 style="color: #FF6600; font-size: 18px;">Challenge Detection & Handling</h3>
                                
                                <div style="margin-bottom: 20px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <label class="form-label" style="margin: 0;">Enable Challenge Detection</label>
                                        <label class="switch">
                                            <input type="checkbox" checked>
                                            <span class="slider round"></span>
                                        </label>
                                    </div>
                                    <div style="font-size: 13px; color: #AAA; margin-left: 0;">
                                        Automatically detects when TextNow is presenting unusual verification requests
                                    </div>
                                </div>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                                    <div>
                                        <label class="form-label">Challenge Response</label>
                                        <select class="form-select">
                                            <option selected>Smart Adaptation</option>
                                            <option>Pause & Notify</option>
                                            <option>Try Manual Solving</option>
                                            <option>Skip Account</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Action to take when a challenge is detected
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Session Adaptation</label>
                                        <select class="form-select">
                                            <option selected>Modify Behavior (Recommended)</option>
                                            <option>Use Clean Session</option>
                                            <option>Rotate IP & Retry</option>
                                            <option>No Adaptation</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            How sessions adapt when challenges are detected
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Pattern Recognition</label>
                                        <select class="form-select">
                                            <option selected>Enabled (Learn Triggers)</option>
                                            <option>Monitoring Only</option>
                                            <option>Disabled</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Learn which actions trigger challenges
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Avoidance Learning</label>
                                        <select class="form-select">
                                            <option selected>Enabled (Auto-Adapt)</option>
                                            <option>Manual Review</option>
                                            <option>Disabled</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Automatically adjust behavior to prevent captchas
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; border-radius: 6px; padding: 20px; margin-bottom: 25px;">
                                    <h4 style="margin-top: 0; color: #FF6600; font-size: 16px;">Manual Captcha Solving Interface</h4>
                                    <div style="font-size: 13px; color: #CCC; margin-bottom: 15px;">
                                        When automatic solving fails, captchas will be displayed here for manual resolution
                                    </div>
                                    
                                    <div style="display: flex; gap: 20px; align-items: flex-start;">
                                        <div style="flex: 1;">
                                            <div style="background-color: #333; border-radius: 4px; padding: 10px; margin-bottom: 10px; font-size: 14px; color: #CCC;">
                                                No active captchas needing manual resolution at this time.
                                            </div>
                                            
                                            <div style="display: flex; justify-content: space-between; margin-top: 15px;">
                                                <div style="color: #CCC; font-size: 13px;">
                                                    Manual solving is used when automatic services fail
                                                </div>
                                                <button class="form-button secondary-button">Test Manual Interface</button>
                                            </div>
                                        </div>
                                        
                                        <div style="border-left: 1px solid #444; height: 100px;"></div>
                                        
                                        <div style="width: 300px;">
                                            <div style="background-color: #333; border-radius: 4px; padding: 10px; font-size: 14px; color: #CCC;">
                                                <div style="font-weight: bold; margin-bottom: 5px;">Notification Settings</div>
                                                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                                                    <input type="checkbox" checked style="margin-right: 8px;">
                                                    <span>Send browser notification</span>
                                                </div>
                                                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                                                    <input type="checkbox" checked style="margin-right: 8px;">
                                                    <span>Play sound alert</span>
                                                </div>
                                                <div style="display: flex; align-items: center;">
                                                    <input type="checkbox" style="margin-right: 8px;">
                                                    <span>Send email alert</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <h3 style="color: #FF6600; font-size: 18px;">Performance & Analytics</h3>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                                    <div>
                                        <label class="form-label">Success Rate Tracking</label>
                                        <select class="form-select">
                                            <option selected>Enabled (Track All Metrics)</option>
                                            <option>Basic Tracking Only</option>
                                            <option>Disabled</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Monitor solution effectiveness over time
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Cost Optimization</label>
                                        <select class="form-select">
                                            <option selected>Balance Cost & Speed</option>
                                            <option>Prioritize Speed</option>
                                            <option>Prioritize Cost</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Optimize captcha solving for cost or speed
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="display: flex; background-color: #2A2A2A; border-radius: 6px; padding: 15px; margin-bottom: 20px;">
                                    <div style="flex: 1; border-right: 1px solid #444; padding-right: 15px;">
                                        <div style="font-size: 14px; font-weight: bold; color: #CCC; margin-bottom: 10px;">Solving Success Rate</div>
                                        <div style="font-size: 24px; font-weight: bold; color: #00C853;">94.7%</div>
                                        <div style="font-size: 12px; color: #AAA;">Last 7 days (382 captchas)</div>
                                    </div>
                                    
                                    <div style="flex: 1; padding: 0 15px; border-right: 1px solid #444;">
                                        <div style="font-size: 14px; font-weight: bold; color: #CCC; margin-bottom: 10px;">Average Solve Time</div>
                                        <div style="font-size: 24px; font-weight: bold; color: #EEE;">8.2s</div>
                                        <div style="font-size: 12px; color: #AAA;">Primary service: 2Captcha</div>
                                    </div>
                                    
                                    <div style="flex: 1; padding-left: 15px;">
                                        <div style="font-size: 14px; font-weight: bold; color: #CCC; margin-bottom: 10px;">Monthly Cost</div>
                                        <div style="font-size: 24px; font-weight: bold; color: #EEE;">$14.25</div>
                                        <div style="font-size: 12px; color: #AAA;">Estimated (based on current usage)</div>
                                    </div>
                                </div>
                                
                                <div style="text-align: right; margin-top: 30px;">
                                    <button class="form-button secondary-button">Reset Tab</button>
                                    <button class="form-button">Apply Changes</button>
                                </div>
                            </div>
                            
                            <!-- Android Emulation Tab Content -->
                            <div id="tab-android" class="tab-content" style="display: none;">
                                <h3 style="margin-top: 0; color: #FF6600; font-size: 18px;">Android Emulation System</h3>
                                
                                <div style="margin-bottom: 20px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <label class="form-label" style="margin: 0;">Enable Android Emulation</label>
                                        <label class="switch">
                                            <input type="checkbox" checked>
                                            <span class="slider round"></span>
                                        </label>
                                    </div>
                                    <div style="font-size: 13px; color: #AAA; margin-left: 0;">
                                        Uses lightweight Android emulation optimized for TextNow operations
                                    </div>
                                </div>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                                    <div>
                                        <label class="form-label">Emulation Mode</label>
                                        <select class="form-select">
                                            <option>Full Emulation</option>
                                            <option selected>Hybrid (Phone + Emulation)</option>
                                            <option>Physical Device Only</option>
                                            <option>Demo Mode (No Emulation)</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Type of Android emulation to use
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Device Profile</label>
                                        <select class="form-select">
                                            <option selected>BLU G44 (Perfect Match)</option>
                                            <option>Samsung Galaxy A12</option>
                                            <option>Motorola Moto G7</option>
                                            <option>Custom Profile</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Android device to simulate
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Multi-Instance Support</label>
                                        <select class="form-select">
                                            <option>Single Instance</option>
                                            <option selected>Up to 5 Instances</option>
                                            <option>Up to 10 Instances</option>
                                            <option>Custom (Set Maximum)</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Number of simultaneous emulator instances
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Resource Allocation</label>
                                        <select class="form-select">
                                            <option>Minimal (1GB RAM)</option>
                                            <option selected>Standard (2GB RAM)</option>
                                            <option>Enhanced (4GB RAM)</option>
                                            <option>Custom Allocation</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            System resources allocated to each instance
                                        </div>
                                    </div>
                                </div>
                                
                                <h3 style="color: #FF6600; font-size: 18px;">Device Simulation Settings</h3>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px;">
                                    <div>
                                        <label class="form-label">Hardware Fingerprinting</label>
                                        <select class="form-select">
                                            <option selected>Exact Device Match</option>
                                            <option>Randomized (Same Model)</option>
                                            <option>Basic Fingerprinting Only</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Match real device hardware identifiers
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Sensor Simulation</label>
                                        <select class="form-select">
                                            <option selected>Full Sensor Suite</option>
                                            <option>Essential Sensors Only</option>
                                            <option>Disabled</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Simulate GPS, accelerometer, and other sensors
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">IMEI/Serial Generation</label>
                                        <select class="form-select">
                                            <option selected>Realistic Unique IDs</option>
                                            <option>Copy Physical Device</option>
                                            <option>Basic Generation</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Generate realistic device identifiers
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Screen Parameters</label>
                                        <select class="form-select">
                                            <option selected>Exact Match (BLU G44)</option>
                                            <option>Standard HD (720p)</option>
                                            <option>Full HD (1080p)</option>
                                            <option>Custom Resolution</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Match screen metrics of target device
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; border-radius: 6px; padding: 20px; margin-bottom: 25px;">
                                    <h4 style="margin-top: 0; color: #FF6600; font-size: 16px;">Mobile Network Integration</h4>
                                    
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                                        <div>
                                            <label class="form-label">Hybrid Operation Mode</label>
                                            <select class="form-select">
                                                <option selected>Phone IP + Emulator Actions</option>
                                                <option>Emulator Only</option>
                                                <option>Phone Only</option>
                                            </select>
                                            <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                                Use phone for IP but emulator for actions
                                            </div>
                                        </div>
                                        
                                        <div>
                                            <label class="form-label">Connection Type</label>
                                            <select class="form-select">
                                                <option selected>USB Tethering</option>
                                                <option>ADB Connection</option>
                                                <option>Wireless Connection</option>
                                            </select>
                                            <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                                How emulator connects to mobile device
                                            </div>
                                        </div>
                                        
                                        <div>
                                            <label class="form-label">Carrier Profile</label>
                                            <select class="form-select">
                                                <option selected>Auto-Detect (Current Device)</option>
                                                <option>T-Mobile</option>
                                                <option>Verizon</option>
                                                <option>AT&T</option>
                                                <option>Sprint</option>
                                            </select>
                                            <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                                Carrier network settings to simulate
                                            </div>
                                        </div>
                                        
                                        <div>
                                            <label class="form-label">Connection Management</label>
                                            <select class="form-select">
                                                <option selected>Auto Recovery</option>
                                                <option>Manual Reconnection</option>
                                                <option>Minimal Management</option>
                                            </select>
                                            <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                                How to handle device disconnections
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div style="display: flex; align-items: center; background-color: #333; padding: 12px; border-radius: 4px;">
                                        <div style="border-radius: 50%; width: 12px; height: 12px; background-color: #00C853; margin-right: 10px;"></div>
                                        <div>
                                            <div style="font-weight: bold; color: #EEE;">BLU G44 Device Connected and Bridged</div>
                                            <div style="font-size: 13px; color: #AAA;">Serial: BLU445789XCV • Uptime: 3h 24m • Signal: Excellent (T-Mobile)</div>
                                        </div>
                                        <button class="form-button secondary-button" style="margin-left: auto;">Test Connection</button>
                                    </div>
                                </div>
                                
                                <h3 style="color: #FF6600; font-size: 18px;">App Automation & Security</h3>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px;">
                                    <div>
                                        <label class="form-label">TextNow App Integration</label>
                                        <select class="form-select">
                                            <option selected>Direct Control</option>
                                            <option>API Integration</option>
                                            <option>Basic Interaction</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Method of controlling TextNow app
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Anti-Detection Measures</label>
                                        <select class="form-select">
                                            <option selected>Maximum (All Protections)</option>
                                            <option>Standard Protections</option>
                                            <option>Basic Only</option>
                                            <option>Disabled</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Prevent emulator detection by apps
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">SafetyNet Bypass</label>
                                        <select class="form-select">
                                            <option selected>Enabled (Recommended)</option>
                                            <option>Basic Bypass</option>
                                            <option>Disabled</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Pass Google SafetyNet integrity checks
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">App Environment Isolation</label>
                                        <select class="form-select">
                                            <option selected>Complete Isolation</option>
                                            <option>Standard Isolation</option>
                                            <option>Minimal Isolation</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Prevent cross-app detection
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="text-align: right; margin-top: 30px;">
                                    <button class="form-button secondary-button">Reset Tab</button>
                                    <button class="form-button">Apply Changes</button>
                                </div>
                            </div>
                            
                            <!-- Proxidize Configuration Tab Content -->
                            <div id="tab-device" class="tab-content" style="display: none;">
                                <h3 style="margin-top: 0; color: #FF6600; font-size: 18px;">Proxidize Device Configuration</h3>
                                
                                <div style="margin-bottom: 20px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <label class="form-label" style="margin: 0;">Enable Advanced Proxidize Features</label>
                                        <label class="switch">
                                            <input type="checkbox" checked>
                                            <span class="slider round"></span>
                                        </label>
                                    </div>
                                    <div style="font-size: 13px; color: #AAA; margin-left: 0;">
                                        Enables comprehensive device simulation through Proxidize network
                                    </div>
                                </div>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                                    <div>
                                        <label class="form-label">Proxy Connection Type</label>
                                        <select class="form-select">
                                            <option selected>HTTP</option>
                                            <option>SOCKS5</option>
                                            <option>HTTPS</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            The connection protocol for Proxidize
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Simulation Fidelity</label>
                                        <select class="form-select">
                                            <option selected>Maximum (Undetectable)</option>
                                            <option>High (Balanced)</option>
                                            <option>Standard</option>
                                            <option>Basic (Performance)</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            How accurately to simulate the device
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Device Rotation</label>
                                        <select class="form-select">
                                            <option>Single Device Profile</option>
                                            <option selected>Per Account (Fixed)</option>
                                            <option>Random Rotation</option>
                                            <option>Scheduled Rotation</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            How to handle multiple device profiles
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Profile Library</label>
                                        <select class="form-select">
                                            <option selected>Standard Library (20 Profiles)</option>
                                            <option>Extended Library (50+ Profiles)</option>
                                            <option>Custom Profile Set</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Device profile library to use
                                        </div>
                                    </div>
                                </div>
                                
                                <h3 style="color: #FF6600; font-size: 18px;">Proxidize Connection Parameters</h3>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px;">
                                    <div>
                                        <label class="form-label">User Agent Handling</label>
                                        <select class="form-select">
                                            <option selected>Complete Device Match</option>
                                            <option>Generic Android</option>
                                            <option>Custom User Agent</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            How to manage User-Agent headers with Proxidize
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Connection Timeout</label>
                                        <select class="form-select">
                                            <option>10 seconds</option>
                                            <option selected>30 seconds</option>
                                            <option>60 seconds</option>
                                            <option>120 seconds</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Maximum wait time for Proxidize connections
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">IP Rotation Interval</label>
                                        <select class="form-select">
                                            <option>Every 15 minutes</option>
                                            <option selected>Every 30 minutes</option>
                                            <option>Every hour</option>
                                            <option>Manual only</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            How often to automatically rotate Proxidize IPs
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Connection Mode</label>
                                        <select class="form-select">
                                            <option selected>Direct Modem Connection</option>
                                            <option>API-based Management</option>
                                            <option>Custom Configuration</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            How to establish connection with Proxidize
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; border-radius: 6px; padding: 20px; margin-bottom: 25px;">
                                    <h4 style="margin-top: 0; color: #FF6600; font-size: 16px;">Proxidize Configuration Status</h4>
                                    
                                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 15px; font-size: 13px;">
                                        <div>
                                            <div style="color: #CCC; font-weight: bold;">Proxy Server</div>
                                            <div style="color: #EEE;">nae2.proxi.es:2148</div>
                                        </div>
                                        <div>
                                            <div style="color: #CCC; font-weight: bold;">Connection Type</div>
                                            <div style="color: #EEE;">HTTP</div>
                                        </div>
                                        <div>
                                            <div style="color: #CCC; font-weight: bold;">Auth Method</div>
                                            <div style="color: #EEE;">Username/Password</div>
                                        </div>
                                        <div>
                                            <div style="color: #CCC; font-weight: bold;">Current IP</div>
                                            <div style="color: #EEE;">174.225.114.230</div>
                                        </div>
                                        <div>
                                            <div style="color: #CCC; font-weight: bold;">Rotation API</div>
                                            <div style="color: #EEE;">Enabled (Proxidize API)</div>
                                        </div>
                                        <div>
                                            <div style="color: #CCC; font-weight: bold;">Rotation Interval</div>
                                            <div style="color: #EEE;">30 minutes</div>
                                        </div>
                                        <div>
                                            <div style="color: #CCC; font-weight: bold;">Connection Status</div>
                                            <div style="color: #00C853;">Connected</div>
                                        </div>
                                        <div>
                                            <div style="color: #CCC; font-weight: bold;">Last Rotation</div>
                                            <div style="color: #EEE;">3 minutes ago</div>
                                        </div>
                                        <div>
                                            <div style="color: #CCC; font-weight: bold;">Token Status</div>
                                            <div style="color: #00C853;">Valid Token</div>
                                        </div>
                                    </div>
                                    
                                    <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 10px;">
                                        <button class="form-button secondary-button">Test Connection</button>
                                        <button class="form-button secondary-button">View Logs</button>
                                    </div>
                                </div>
                                
                                <h3 style="color: #FF6600; font-size: 18px;">Advanced Simulation Features</h3>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                                    <div>
                                        <label class="form-label">Location Spoofing</label>
                                        <select class="form-select">
                                            <option selected>Florida Locations</option>
                                            <option>Random US Locations</option>
                                            <option>Fixed Location</option>
                                            <option>Disabled</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Set precise GPS coordinates
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Camera Simulation</label>
                                        <select class="form-select">
                                            <option selected>Virtual Camera (BLU G44 Specs)</option>
                                            <option>Generic Camera</option>
                                            <option>Disabled</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Virtual camera input simulation
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Biometric Simulation</label>
                                        <select class="form-select">
                                            <option selected>Fingerprint Authentication</option>
                                            <option>Basic Authentication</option>
                                            <option>Disabled</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Simulate biometric authentication
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Battery Behavior</label>
                                        <select class="form-select">
                                            <option selected>Realistic Patterns</option>
                                            <option>Always Full</option>
                                            <option>Random Levels</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Simulate realistic battery behavior
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="text-align: right; margin-top: 30px;">
                                    <button class="form-button secondary-button">Reset Tab</button>
                                    <button class="form-button">Apply Changes</button>
                                </div>
                            </div>
                            
                            <div id="tab-automation" class="tab-content" style="display: none;">
                                <h3 style="margin-top: 0; color: #FF6600; font-size: 18px;">Automation Resilience</h3>
                                
                                <div style="margin-bottom: 20px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <label class="form-label" style="margin: 0;">Enable Advanced Resilience System</label>
                                        <label class="switch">
                                            <input type="checkbox" checked>
                                            <span class="slider round"></span>
                                        </label>
                                    </div>
                                    <div style="font-size: 13px; color: #AAA; margin-left: 0;">
                                        Enables sophisticated error recovery and self-healing capabilities
                                    </div>
                                </div>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                                    <div>
                                        <label class="form-label">Resilience Level</label>
                                        <select class="form-select">
                                            <option selected>Maximum (Aggressive Recovery)</option>
                                            <option>Standard (Balanced)</option>
                                            <option>Basic (Minimal Intervention)</option>
                                            <option>Custom Configuration</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            How aggressively to recover from failures
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Error Recognition</label>
                                        <select class="form-select">
                                            <option selected>AI-Powered (Dynamic)</option>
                                            <option>Pattern-Based</option>
                                            <option>Basic Recognition</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Method used to identify automation errors
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Self-Healing Mode</label>
                                        <select class="form-select">
                                            <option selected>Comprehensive (All Systems)</option>
                                            <option>Targeted (Critical Systems Only)</option>
                                            <option>Manual Approval Required</option>
                                            <option>Disabled</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Auto-recovery capabilities for automation
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Learning Algorithm</label>
                                        <select class="form-select">
                                            <option selected>Continuous Improvement</option>
                                            <option>Scheduled Learning</option>
                                            <option>No Learning</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            How the system learns from past failures
                                        </div>
                                    </div>
                                </div>
                                
                                <h3 style="color: #FF6600; font-size: 18px;">TextNow Change Adaptation</h3>
                                
                                <div style="margin-bottom: 20px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <label class="form-label" style="margin: 0;">Enable UI Change Detection</label>
                                        <label class="switch">
                                            <input type="checkbox" checked>
                                            <span class="slider round"></span>
                                        </label>
                                    </div>
                                    <div style="font-size: 13px; color: #AAA; margin-left: 0;">
                                        Automatically detects changes to TextNow's interface and adapts automatically
                                    </div>
                                </div>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px;">
                                    <div>
                                        <label class="form-label">Detection Method</label>
                                        <select class="form-select">
                                            <option selected>Visual Pattern Recognition</option>
                                            <option>DOM Structure Analysis</option>
                                            <option>Hybrid Approach</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Method to detect UI changes
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Adaptation Response</label>
                                        <select class="form-select">
                                            <option selected>Auto-Update (Immediate)</option>
                                            <option>Hybrid (Auto + Manual)</option>
                                            <option>Manual Verification</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            How to respond when UI changes are detected
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Flow Recovery</label>
                                        <select class="form-select">
                                            <option selected>Smart Navigation</option>
                                            <option>Retry With Variations</option>
                                            <option>Fallback to Basic</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            How to recover navigation flows after changes
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Update Frequency</label>
                                        <select class="form-select">
                                            <option selected>Real-Time Monitoring</option>
                                            <option>Daily Check</option>
                                            <option>Weekly Check</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            How often to check for TextNow changes
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; border-radius: 6px; padding: 20px; margin-bottom: 25px;">
                                    <h4 style="margin-top: 0; color: #FF6600; font-size: 16px;">Recovery Action Templates</h4>
                                    
                                    <div style="margin-bottom: 15px; font-size: 13px; color: #CCC;">
                                        Pre-configured response strategies for common failure scenarios:
                                    </div>
                                    
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                                        <div style="background-color: #333; border-radius: 4px; padding: 12px;">
                                            <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Login Failure Recovery</div>
                                            <div style="font-size: 12px; color: #AAA;">
                                                Multi-stage process to recover from authentication failures, including session clearing, credential verification, and CAPTCHA handling.
                                            </div>
                                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                                                <div style="font-size: 11px; color: #008800;">Status: Active</div>
                                                <button class="form-button secondary-button" style="font-size: 12px; padding: 3px 8px;">Edit</button>
                                            </div>
                                        </div>
                                        
                                        <div style="background-color: #333; border-radius: 4px; padding: 12px;">
                                            <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Number Verification Bypass</div>
                                            <div style="font-size: 12px; color: #AAA;">
                                                Advanced techniques to handle unexpected verification requests from TextNow, including timing adjustments and session management.
                                            </div>
                                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                                                <div style="font-size: 11px; color: #008800;">Status: Active</div>
                                                <button class="form-button secondary-button" style="font-size: 12px; padding: 3px 8px;">Edit</button>
                                            </div>
                                        </div>
                                        
                                        <div style="background-color: #333; border-radius: 4px; padding: 12px;">
                                            <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Rate Limit Recovery</div>
                                            <div style="font-size: 12px; color: #AAA;">
                                                Intelligent rate-limiting detection and adaptive pausing to prevent account flagging while maximizing throughput.
                                            </div>
                                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                                                <div style="font-size: 11px; color: #008800;">Status: Active</div>
                                                <button class="form-button secondary-button" style="font-size: 12px; padding: 3px 8px;">Edit</button>
                                            </div>
                                        </div>
                                        
                                        <div style="background-color: #333; border-radius: 4px; padding: 12px;">
                                            <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">JS Error Resilience</div>
                                            <div style="font-size: 12px; color: #AAA;">
                                                Handles JavaScript execution errors and DOM manipulation failures with advanced retry strategies.
                                            </div>
                                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                                                <div style="font-size: 11px; color: #008800;">Status: Active</div>
                                                <button class="form-button secondary-button" style="font-size: 12px; padding: 3px 8px;">Edit</button>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div style="text-align: right;">
                                        <button class="form-button secondary-button">Add New Template</button>
                                    </div>
                                </div>
                                
                                <h3 style="color: #FF6600; font-size: 18px;">Reliability Analytics</h3>
                                
                                <div style="display: flex; margin-bottom: 25px; background-color: #2A2A2A; border-radius: 6px; padding: 15px;">
                                    <div style="flex: 1; text-align: center; border-right: 1px solid #444; padding: 0 15px;">
                                        <div style="font-size: 14px; color: #CCC; margin-bottom: 5px;">Automation Success Rate</div>
                                        <div style="font-size: 24px; font-weight: bold; color: #00C853;">98.7%</div>
                                        <div style="font-size: 12px; color: #AAA;">Last 7 days</div>
                                    </div>
                                    
                                    <div style="flex: 1; text-align: center; border-right: 1px solid #444; padding: 0 15px;">
                                        <div style="font-size: 14px; color: #CCC; margin-bottom: 5px;">Auto-Recovered Errors</div>
                                        <div style="font-size: 24px; font-weight: bold; color: #EEE;">143</div>
                                        <div style="font-size: 12px; color: #AAA;">Last 7 days</div>
                                    </div>
                                    
                                    <div style="flex: 1; text-align: center; padding: 0 15px;">
                                        <div style="font-size: 14px; color: #CCC; margin-bottom: 5px;">Avg. Recovery Time</div>
                                        <div style="font-size: 24px; font-weight: bold; color: #EEE;">3.2s</div>
                                        <div style="font-size: 12px; color: #AAA;">Per incident</div>
                                    </div>
                                </div>
                                
                                <div style="text-align: right; margin-top: 30px;">
                                    <button class="form-button secondary-button">Reset Tab</button>
                                    <button class="form-button">Apply Changes</button>
                                </div>
                            </div>
                            
                            <div id="tab-aging" class="tab-content" style="display: none;">
                                <h3 style="margin-top: 0; color: #FF6600; font-size: 18px;">Account Aging & Nurturing</h3>
                                
                                <div style="margin-bottom: 20px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <label class="form-label" style="margin: 0;">Enable Account Aging System</label>
                                        <label class="switch">
                                            <input type="checkbox" checked>
                                            <span class="slider round"></span>
                                        </label>
                                    </div>
                                    <div style="font-size: 13px; color: #AAA; margin-left: 0;">
                                        Automatically nurtures new accounts to improve trust scores and long-term viability
                                    </div>
                                </div>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                                    <div>
                                        <label class="form-label">Aging Profile</label>
                                        <select class="form-select">
                                            <option selected>Aggressive (Expedited)</option>
                                            <option>Balanced (Standard)</option>
                                            <option>Conservative (Slow)</option>
                                            <option>Custom Profile</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Determines how quickly accounts mature
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Activity Patterns</label>
                                        <select class="form-select">
                                            <option selected>Human-Like (Randomized)</option>
                                            <option>Regular Schedule</option>
                                            <option>Minimal Activity</option>
                                            <option>Custom Pattern</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Activity patterns used during aging
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Aging Priorities</label>
                                        <select class="form-select">
                                            <option selected>Auto-Balance Resources</option>
                                            <option>Prioritize Newest Accounts</option>
                                            <option>Prioritize Campaign-Ready</option>
                                            <option>Custom Priority Rules</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            How to allocate resources for aging accounts
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Maturity Targeting</label>
                                        <select class="form-select">
                                            <option selected>Multi-Stage (Full Spectrum)</option>
                                            <option>Quick Ready State</option>
                                            <option>Long-Term Nurturing</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Targeted account maturity levels
                                        </div>
                                    </div>
                                </div>
                                
                                <h3 style="color: #FF6600; font-size: 18px;">Activity Simulation</h3>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px;">
                                    <div>
                                        <label class="form-label">Message Type Mix</label>
                                        <select class="form-select">
                                            <option selected>Balanced Mix (Recommended)</option>
                                            <option>Text-Heavy</option>
                                            <option>Media-Heavy</option>
                                            <option>Custom Mix</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Mix of message types during aging
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Conversation Partners</label>
                                        <select class="form-select">
                                            <option selected>Internal Network (Own Accounts)</option>
                                            <option>Verified Partners Only</option>
                                            <option>Mixed Sources</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Who accounts interact with during aging
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Activity Timing</label>
                                        <select class="form-select">
                                            <option selected>Natural Patterns (Randomized)</option>
                                            <option>Business Hours</option>
                                            <option>24/7 Activity</option>
                                            <option>Custom Schedule</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            When account activity occurs
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Feature Utilization</label>
                                        <select class="form-select">
                                            <option selected>Complete (All Features)</option>
                                            <option>Essential Features Only</option>
                                            <option>Minimal Utilization</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Which TextNow features accounts use
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; border-radius: 6px; padding: 20px; margin-bottom: 25px;">
                                    <h4 style="margin-top: 0; color: #FF6600; font-size: 16px;">Aging Stages & Activities</h4>
                                    
                                    <div style="display: grid; grid-template-columns: auto 1fr; gap: 15px; margin-bottom: 20px; font-size: 13px;">
                                        <div style="display: contents;">
                                            <div style="font-weight: bold; color: #EEE; padding: 8px 0; border-bottom: 1px solid #444;">Stage</div>
                                            <div style="font-weight: bold; color: #EEE; padding: 8px 0; border-bottom: 1px solid #444;">Activities</div>
                                        </div>
                                        
                                        <div style="display: contents;">
                                            <div style="color: #CCC; padding: 8px 0; border-bottom: 1px solid #3A3A3A;">Initial (Days 1-3)</div>
                                            <div style="color: #AAA; padding: 8px 0; border-bottom: 1px solid #3A3A3A;">Profile setup, voicemail recording, basic app exploration, 5-10 test messages to internal network, contact adding</div>
                                        </div>
                                        
                                        <div style="display: contents;">
                                            <div style="color: #CCC; padding: 8px 0; border-bottom: 1px solid #3A3A3A;">Early (Days 4-7)</div>
                                            <div style="color: #AAA; padding: 8px 0; border-bottom: 1px solid #3A3A3A;">Increased messaging frequency, varied message types, profile photo updates, device switching, expanded contact list</div>
                                        </div>
                                        
                                        <div style="display: contents;">
                                            <div style="color: #CCC; padding: 8px 0; border-bottom: 1px solid #3A3A3A;">Development (Days 8-14)</div>
                                            <div style="color: #AAA; padding: 8px 0; border-bottom: 1px solid #3A3A3A;">Group messages, media sharing, calling features, setting changes, increased message length variability</div>
                                        </div>
                                        
                                        <div style="display: contents;">
                                            <div style="color: #CCC; padding: 8px 0;">Mature (Day 15+)</div>
                                            <div style="color: #AAA; padding: 8px 0;">Natural usage patterns, consistent activity levels, all features utilized, ready for campaign integration</div>
                                        </div>
                                    </div>
                                    
                                    <div style="display: flex; justify-content: flex-end; margin-top: 10px;">
                                        <button class="form-button secondary-button">Customize Stages</button>
                                    </div>
                                </div>
                                
                                <h3 style="color: #FF6600; font-size: 18px;">Account Health Management</h3>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                                    <div>
                                        <label class="form-label">Automated Health Checks</label>
                                        <select class="form-select">
                                            <option selected>Comprehensive (All Metrics)</option>
                                            <option>Basic Checks Only</option>
                                            <option>Manual Health Checks</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Account health monitoring during aging
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Remediation Actions</label>
                                        <select class="form-select">
                                            <option selected>Auto-Fix Issues</option>
                                            <option>Flag for Review</option>
                                            <option>Basic Auto-Fixes Only</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            How to handle account health issues
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Risk Balancing</label>
                                        <select class="form-select">
                                            <option selected>Adaptive Risk Assessment</option>
                                            <option>Conservative (Low Risk)</option>
                                            <option>Aggressive (High Output)</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Balance between safety and productivity
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Account Retirement</label>
                                        <select class="form-select">
                                            <option selected>Health-Based Retirement</option>
                                            <option>Age-Based Retirement</option>
                                            <option>Manual Retirement Only</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            When to retire accounts from active use
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="display: flex; background-color: #2A2A2A; border-radius: 6px; padding: 15px; margin-bottom: 25px;">
                                    <div style="flex: 1; text-align: center; border-right: 1px solid #444; padding: 0 15px;">
                                        <div style="font-size: 14px; color: #CCC; margin-bottom: 5px;">Active Aging Accounts</div>
                                        <div style="font-size: 24px; font-weight: bold; color: #EEE;">1,247</div>
                                        <div style="font-size: 12px; color: #AAA;">Currently in process</div>
                                    </div>
                                    
                                    <div style="flex: 1; text-align: center; border-right: 1px solid #444; padding: 0 15px;">
                                        <div style="font-size: 14px; color: #CCC; margin-bottom: 5px;">Accounts Matured</div>
                                        <div style="font-size: 24px; font-weight: bold; color: #00C853;">5,721</div>
                                        <div style="font-size: 12px; color: #AAA;">Ready for campaigns</div>
                                    </div>
                                    
                                    <div style="flex: 1; text-align: center; padding: 0 15px;">
                                        <div style="font-size: 14px; color: #CCC; margin-bottom: 5px;">Health Score Avg.</div>
                                        <div style="font-size: 24px; font-weight: bold; color: #00C853;">92.4%</div>
                                        <div style="font-size: 12px; color: #AAA;">All aged accounts</div>
                                    </div>
                                </div>
                                
                                <div style="text-align: right; margin-top: 30px;">
                                    <button class="form-button secondary-button">Reset Tab</button>
                                    <button class="form-button">Apply Changes</button>
                                </div>
                            </div>
                            
                            <div id="tab-profiles" class="tab-content" style="display: none;">
                                <h3 style="margin-top: 0; color: #FF6600; font-size: 18px;">System Profiles</h3>
                                
                                <div style="margin-bottom: 20px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <label class="form-label" style="margin: 0;">Enable Profile System</label>
                                        <label class="switch">
                                            <input type="checkbox" checked>
                                            <span class="slider round"></span>
                                        </label>
                                    </div>
                                    <div style="font-size: 13px; color: #AAA; margin-left: 0;">
                                        Saves, manages, and switches between different configuration profiles
                                    </div>
                                </div>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                                    <div>
                                        <label class="form-label">Active Profile</label>
                                        <select class="form-select">
                                            <option selected>Maximum Performance (Default)</option>
                                            <option>Florida Campaign Optimized</option>
                                            <option>High Security</option>
                                            <option>Balanced Profile</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            The currently active system profile
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Profile Switching</label>
                                        <select class="form-select">
                                            <option selected>Manual Only</option>
                                            <option>Schedule-Based</option>
                                            <option>Campaign-Based</option>
                                            <option>Adaptive Switching</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            How and when profiles are switched
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Configuration Scope</label>
                                        <select class="form-select">
                                            <option selected>Complete System Configuration</option>
                                            <option>Only Anti-Detection Settings</option>
                                            <option>Only Campaign Settings</option>
                                            <option>Custom Scope</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Which settings are included in profiles
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Backup & Export</label>
                                        <select class="form-select">
                                            <option selected>Auto + Manual Backups</option>
                                            <option>Manual Backups Only</option>
                                            <option>No Backup</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Backup and portability options for profiles
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #2A2A2A; border-radius: 6px; padding: 20px; margin-bottom: 25px;">
                                    <h4 style="margin-top: 0; color: #FF6600; font-size: 16px; margin-bottom: 15px;">Available System Profiles</h4>
                                    
                                    <div style="display: grid; gap: 15px;">
                                        <div style="background-color: #333; border-radius: 4px; padding: 15px; position: relative;">
                                            <div style="position: absolute; top: 10px; right: 10px; background-color: #00C853; color: white; font-size: 11px; padding: 2px 8px; border-radius: 10px;">Active</div>
                                            
                                            <div style="font-weight: bold; color: #EEE; margin-bottom: 8px; font-size: 16px;">Maximum Performance (Default)</div>
                                            <div style="color: #AAA; font-size: 13px; margin-bottom: 12px;">
                                                Optimized for highest throughput and performance with balanced security measures.
                                            </div>
                                            
                                            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px;">
                                                <div style="background-color: #2A2A2A; border-radius: 10px; font-size: 11px; padding: 3px 8px; color: #CCC;">Anti-Detection: High</div>
                                                <div style="background-color: #2A2A2A; border-radius: 10px; font-size: 11px; padding: 3px 8px; color: #CCC;">IP Rotation: 25 msgs</div>
                                                <div style="background-color: #2A2A2A; border-radius: 10px; font-size: 11px; padding: 3px 8px; color: #CCC;">Browser Fingerprint: Maximum</div>
                                                <div style="background-color: #2A2A2A; border-radius: 10px; font-size: 11px; padding: 3px 8px; color: #CCC;">Activity Pattern: Human-Like</div>
                                            </div>
                                            
                                            <div style="display: flex; justify-content: flex-end; gap: 10px;">
                                                <button class="form-button secondary-button">Edit</button>
                                                <button class="form-button secondary-button">Clone</button>
                                                <button class="form-button secondary-button" disabled>Activate</button>
                                            </div>
                                        </div>
                                        
                                        <div style="background-color: #333; border-radius: 4px; padding: 15px;">
                                            <div style="font-weight: bold; color: #EEE; margin-bottom: 8px; font-size: 16px;">Florida Campaign Optimized</div>
                                            <div style="color: #AAA; font-size: 13px; margin-bottom: 12px;">
                                                Specifically tuned for Florida area codes with optimized geographic targeting and messaging patterns.
                                            </div>
                                            
                                            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px;">
                                                <div style="background-color: #2A2A2A; border-radius: 10px; font-size: 11px; padding: 3px 8px; color: #CCC;">Anti-Detection: Very High</div>
                                                <div style="background-color: #2A2A2A; border-radius: 10px; font-size: 11px; padding: 3px 8px; color: #CCC;">Location: Florida</div>
                                                <div style="background-color: #2A2A2A; border-radius: 10px; font-size: 11px; padding: 3px 8px; color: #CCC;">IP Rotation: 15 msgs</div>
                                                <div style="background-color: #2A2A2A; border-radius: 10px; font-size: 11px; padding: 3px 8px; color: #CCC;">Area Codes: FL Set</div>
                                            </div>
                                            
                                            <div style="display: flex; justify-content: flex-end; gap: 10px;">
                                                <button class="form-button secondary-button">Edit</button>
                                                <button class="form-button secondary-button">Clone</button>
                                                <button class="form-button">Activate</button>
                                            </div>
                                        </div>
                                        
                                        <div style="background-color: #333; border-radius: 4px; padding: 15px;">
                                            <div style="font-weight: bold; color: #EEE; margin-bottom: 8px; font-size: 16px;">High Security</div>
                                            <div style="color: #AAA; font-size: 13px; margin-bottom: 12px;">
                                                Maximum security and anti-detection measures, with conservative messaging patterns and enhanced resilience.
                                            </div>
                                            
                                            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px;">
                                                <div style="background-color: #2A2A2A; border-radius: 10px; font-size: 11px; padding: 3px 8px; color: #CCC;">Anti-Detection: Maximum</div>
                                                <div style="background-color: #2A2A2A; border-radius: 10px; font-size: 11px; padding: 3px 8px; color: #CCC;">IP Rotation: 10 msgs</div>
                                                <div style="background-color: #2A2A2A; border-radius: 10px; font-size: 11px; padding: 3px 8px; color: #CCC;">Browser Fingerprint: Ultra</div>
                                                <div style="background-color: #2A2A2A; border-radius: 10px; font-size: 11px; padding: 3px 8px; color: #CCC;">Speed: Conservative</div>
                                            </div>
                                            
                                            <div style="display: flex; justify-content: flex-end; gap: 10px;">
                                                <button class="form-button secondary-button">Edit</button>
                                                <button class="form-button secondary-button">Clone</button>
                                                <button class="form-button">Activate</button>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div style="display: flex; justify-content: space-between; margin-top: 15px;">
                                        <button class="form-button secondary-button">Import Profile</button>
                                        <button class="form-button">Create New Profile</button>
                                    </div>
                                </div>
                                
                                <h3 style="color: #FF6600; font-size: 18px;">Profile Management</h3>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                                    <div>
                                        <label class="form-label">Profile Storage</label>
                                        <select class="form-select">
                                            <option selected>Local + Cloud Backup</option>
                                            <option>Local Storage Only</option>
                                            <option>Cloud Priority</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Where system profiles are stored
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Encryption Level</label>
                                        <select class="form-select">
                                            <option selected>AES-256 (Maximum)</option>
                                            <option>Standard Encryption</option>
                                            <option>None</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Encryption for stored profile data
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Profile Templates</label>
                                        <select class="form-select">
                                            <option selected>Use Templates for New Profiles</option>
                                            <option>Start from Current Settings</option>
                                            <option>Start Blank</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            How new profiles are created
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="form-label">Platform Compatibility</label>
                                        <select class="form-select">
                                            <option selected>Cross-Platform Compatibility</option>
                                            <option>Windows Only</option>
                                            <option>Current Platform Only</option>
                                        </select>
                                        <div style="font-size: 12px; color: #AAA; margin-top: 5px;">
                                            Profile compatibility across systems
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="display: flex; justify-content: space-between; align-items: center; background-color: #2A2A2A; border-radius: 6px; padding: 15px; margin-bottom: 15px;">
                                    <div>
                                        <div style="font-weight: bold; color: #EEE; margin-bottom: 5px;">Last Profile Backup:</div>
                                        <div style="color: #AAA; font-size: 13px;">April 25, 2025 at 9:42 AM (42 minutes ago)</div>
                                    </div>
                                    
                                    <div>
                                        <button class="form-button secondary-button">Backup Now</button>
                                    </div>
                                </div>
                                
                                <div style="text-align: right; margin-top: 30px;">
                                    <button class="form-button secondary-button">Reset Tab</button>
                                    <button class="form-button">Apply Changes</button>
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
    
    # Import the enhanced campaign scheduling interface
    from campaign_schedule_enhanced import generate_campaign_schedule_html
    
    return render_template_string(
        BASE_HTML,
        title="Campaign Schedule",
        active_page="/campaign-schedule",
        content=generate_campaign_schedule_html()
    )

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Process assets before starting the server
    process_assets()
    
    print("\n" + "="*60)
    print("TEXTNOW MAX - ACCOUNT CREATOR & CAMPAIGN MANAGER")
    print("="*60)
    print("\nAccess the application in your web browser at: http://localhost:5000")
    print("\nAdvanced automation platform for TextNow messaging with account creation")
    print("and campaign management for 100,000+ messages in 8am-8pm window.")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)