"""
Voicemail Manager Page for ProgressGhostCreator

This module provides a Flask route to display the voicemail management interface
"""

import os
from flask import render_template_string, request, jsonify
import logging

from voicemail_setup import get_voicemail_manager

def voicemail_manager_page():
    """Return the voicemail manager HTML"""
    logo_exists = os.path.exists("static/progress_logo.png")
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ProgressGhostCreator - Voicemail Manager</title>
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
                flex: 1;
                display: flex;
                overflow: hidden;
            }
            
            .left-panel {
                width: 250px;
                background-color: #252525;
                border-right: 1px solid #444;
                display: flex;
                flex-direction: column;
            }
            
            .right-panel {
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .panel-header {
                padding: 15px;
                background-color: #333;
                border-bottom: 1px solid #444;
                font-weight: bold;
                font-size: 16px;
            }
            
            .panel-content {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
            }
            
            .action-button {
                background-color: #FF6600;
                color: white;
                border: none;
                padding: 10px 15px;
                margin-top: 10px;
                cursor: pointer;
                border-radius: 3px;
                font-weight: bold;
                display: inline-block;
            }
            
            .action-button:hover {
                background-color: #FF7722;
            }
            
            .secondary-button {
                background-color: #444;
                color: white;
                border: none;
                padding: 10px 15px;
                margin-top: 10px;
                cursor: pointer;
                border-radius: 3px;
                font-weight: bold;
                display: inline-block;
            }
            
            .secondary-button:hover {
                background-color: #555;
            }
            
            .file-list {
                margin-top: 15px;
                border: 1px solid #444;
                border-radius: 5px;
                background-color: #1E1E1E;
                max-height: 200px;
                overflow-y: auto;
            }
            
            .file-item {
                padding: 10px;
                border-bottom: 1px solid #333;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .file-item:last-child {
                border-bottom: none;
            }
            
            .file-item:hover {
                background-color: #2A2A2A;
            }
            
            .file-name {
                flex: 1;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .file-actions {
                display: flex;
            }
            
            .file-play {
                background-color: #007BFF;
                color: white;
                border: none;
                padding: 3px 8px;
                margin-right: 5px;
                cursor: pointer;
                border-radius: 3px;
                font-size: 12px;
            }
            
            .file-play:hover {
                background-color: #0069D9;
            }
            
            .stats-container {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin-top: 20px;
            }
            
            .stat-box {
                background-color: #333;
                border-radius: 5px;
                padding: 15px;
                text-align: center;
            }
            
            .stat-title {
                font-size: 14px;
                color: #CCC;
                margin-bottom: 5px;
            }
            
            .stat-value {
                font-size: 24px;
                font-weight: bold;
                color: #FF6600;
            }
            
            .setup-controls {
                margin-top: 20px;
                padding: 15px;
                background-color: #333;
                border-radius: 5px;
            }
            
            .progress-container {
                margin-top: 15px;
                background-color: #222;
                border-radius: 5px;
                padding: 20px;
            }
            
            .progress-bar-container {
                width: 100%;
                background-color: #444;
                height: 20px;
                border-radius: 10px;
                overflow: hidden;
                margin-top: 10px;
            }
            
            .progress-bar {
                height: 100%;
                background-color: #FF6600;
                width: 0%;
                transition: width 0.3s ease;
            }
            
            .progress-info {
                display: flex;
                justify-content: space-between;
                margin-top: 10px;
                font-size: 14px;
                color: #CCC;
            }
            
            .footer {
                padding: 10px;
                background-color: #222;
                border-top: 1px solid #444;
                text-align: center;
                font-size: 12px;
                color: #AAA;
            }
            
            .drag-drop-area {
                margin-top: 20px;
                padding: 30px;
                border: 2px dashed #444;
                border-radius: 5px;
                text-align: center;
                cursor: pointer;
            }
            
            .drag-drop-area:hover {
                border-color: #FF6600;
                background-color: rgba(255, 102, 0, 0.05);
            }
            
            .upload-icon {
                font-size: 32px;
                margin-bottom: 10px;
                color: #555;
            }
            
            .setup-status {
                margin-top: 15px;
                padding: 15px;
                background-color: #333;
                border-radius: 5px;
            }
            
            .setup-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }
            
            .setup-table th, .setup-table td {
                text-align: left;
                padding: 10px;
                border-bottom: 1px solid #444;
            }
            
            .setup-table th {
                background-color: #222;
                color: #CCC;
            }
            
            .status-label {
                display: inline-block;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            
            .status-pending {
                background-color: #FFC107;
                color: #333;
            }
            
            .status-in-progress {
                background-color: #007BFF;
                color: white;
            }
            
            .status-completed {
                background-color: #28A745;
                color: white;
            }
            
            .status-failed {
                background-color: #DC3545;
                color: white;
            }
            
            .filter-controls {
                display: flex;
                margin-bottom: 15px;
                align-items: center;
            }
            
            .filter-controls label {
                margin-right: 10px;
                font-size: 14px;
                color: #CCC;
            }
            
            .filter-controls select {
                padding: 5px 10px;
                background-color: #333;
                color: white;
                border: 1px solid #444;
                border-radius: 3px;
            }
        </style>
    </head>
    <body>
        <div class="app-container">
            <div class="app-header">
                {% if logo_exists %}
                <img src="/static/progress_logo.png" alt="Progress Bets Logo" class="logo">
                {% else %}
                <div class="logo-placeholder">ProgressBets</div>
                {% endif %}
                <div class="nav-menu">
                    <a href="/" class="nav-button">Home</a>
                    <a href="/creator" class="nav-button">Creator</a>
                    <a href="/dashboard" class="nav-button">Dashboard</a>
                    <a href="/campaigns" class="nav-button">Campaigns</a>
                    <a href="/voicemail-manager" class="nav-button active">Voicemails</a>
                </div>
            </div>
            
            <div class="app-content">
                <div class="left-panel">
                    <div class="panel-header">Voicemail Libraries</div>
                    <div class="panel-content">
                        <div>
                            <button id="import-vms" class="action-button">Import Voicemails</button>
                            <input type="file" id="folder-picker" style="display: none;" webkitdirectory directory multiple>
                        </div>
                        
                        <div class="stats-container">
                            <div class="stat-box">
                                <div class="stat-title">Total Voicemails</div>
                                <div class="stat-value">247</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-title">Used</div>
                                <div class="stat-value">128</div>
                            </div>
                        </div>
                        
                        <div style="margin-top: 20px;">
                            <h3 style="margin-bottom: 10px; color: #DDD; font-size: 16px;">Recent Voicemails</h3>
                            <div class="file-list">
                                <div class="file-item">
                                    <div class="file-name">greeting_001.mp3</div>
                                    <div class="file-actions">
                                        <button class="file-play">▶</button>
                                    </div>
                                </div>
                                <div class="file-item">
                                    <div class="file-name">casual_greeting_002.mp3</div>
                                    <div class="file-actions">
                                        <button class="file-play">▶</button>
                                    </div>
                                </div>
                                <div class="file-item">
                                    <div class="file-name">professional_001.mp3</div>
                                    <div class="file-actions">
                                        <button class="file-play">▶</button>
                                    </div>
                                </div>
                                <div class="file-item">
                                    <div class="file-name">formal_greeting_005.mp3</div>
                                    <div class="file-actions">
                                        <button class="file-play">▶</button>
                                    </div>
                                </div>
                                <div class="file-item">
                                    <div class="file-name">casual_female_003.mp3</div>
                                    <div class="file-actions">
                                        <button class="file-play">▶</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="drag-drop-area" id="drag-drop-zone">
                            <div class="upload-icon">⬆️</div>
                            <div>Drag & drop voicemail files here</div>
                            <div style="font-size: 12px; color: #AAA; margin-top: 5px;">MP3 or WAV format</div>
                        </div>
                    </div>
                </div>
                
                <div class="right-panel">
                    <div class="panel-header">
                        <div class="tab-container" style="display: flex;">
                            <div class="tab active" data-tab="setup" style="padding: 10px 20px; cursor: pointer; border-bottom: 2px solid #FF6600;">Batch Setup</div>
                            <div class="tab" data-tab="accounts" style="padding: 10px 20px; cursor: pointer; border-bottom: 2px solid transparent;">Account Management</div>
                            <div class="tab" data-tab="operations" style="padding: 10px 20px; cursor: pointer; border-bottom: 2px solid transparent;">Operations</div>
                        </div>
                    </div>
                    
                    <div class="panel-content">
                        <!-- Batch Setup Tab -->
                        <div class="tab-content" id="setup-tab">
                            <div>
                                <h2 style="margin-top: 0; color: #FFF;">Batch Voicemail Setup</h2>
                                <p style="color: #CCC;">Automatically set up voicemail greetings for your TextNow accounts using the Android emulator.</p>
                            </div>
                        
                        <div class="setup-controls">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <button id="start-setup" class="action-button">Start Setup</button>
                                    <button id="stop-setup" class="secondary-button" disabled>Stop</button>
                                </div>
                                <div>
                                    <label style="margin-right: 10px; color: #CCC;">Max Accounts:</label>
                                    <select id="max-accounts">
                                        <option value="10">10</option>
                                        <option value="25">25</option>
                                        <option value="50">50</option>
                                        <option value="100" selected>100</option>
                                        <option value="250">250</option>
                                        <option value="500">500</option>
                                        <option value="all">All</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="progress-container">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div style="font-weight: bold; color: #DDD;">Progress</div>
                                    <div style="color: #CCC;">32 of 100 Accounts</div>
                                </div>
                                <div class="progress-bar-container">
                                    <div class="progress-bar" style="width: 32%;"></div>
                                </div>
                                <div class="progress-info">
                                    <div>32% Complete</div>
                                    <div>Estimated time remaining: 34 minutes</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="setup-status">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h3 style="margin: 0; color: #DDD; font-size: 16px;">Setup Status</h3>
                                <div class="filter-controls">
                                    <label>Filter:</label>
                                    <select id="status-filter">
                                        <option value="all">All</option>
                                        <option value="pending">Pending</option>
                                        <option value="in-progress">In Progress</option>
                                        <option value="completed">Completed</option>
                                        <option value="failed">Failed</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div style="max-height: 300px; overflow-y: auto; margin-top: 10px;">
                                <table class="setup-table">
                                    <thead>
                                        <tr>
                                            <th>Phone Number</th>
                                            <th>Username</th>
                                            <th>Status</th>
                                            <th>Voicemail</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>+1 (954) 555-1234</td>
                                            <td>user123</td>
                                            <td><span class="status-label status-completed">Completed</span></td>
                                            <td>greeting_001.mp3</td>
                                        </tr>
                                        <tr>
                                            <td>+1 (754) 555-2345</td>
                                            <td>textnow456</td>
                                            <td><span class="status-label status-completed">Completed</span></td>
                                            <td>casual_greeting_002.mp3</td>
                                        </tr>
                                        <tr>
                                            <td>+1 (305) 555-3456</td>
                                            <td>miami789</td>
                                            <td><span class="status-label status-in-progress">In Progress</span></td>
                                            <td>professional_001.mp3</td>
                                        </tr>
                                        <tr>
                                            <td>+1 (786) 555-4567</td>
                                            <td>florida234</td>
                                            <td><span class="status-label status-pending">Pending</span></td>
                                            <td>-</td>
                                        </tr>
                                        <tr>
                                            <td>+1 (561) 555-5678</td>
                                            <td>palm567</td>
                                            <td><span class="status-label status-pending">Pending</span></td>
                                            <td>-</td>
                                        </tr>
                                        <tr>
                                            <td>+1 (954) 555-6789</td>
                                            <td>broward890</td>
                                            <td><span class="status-label status-failed">Failed</span></td>
                                            <td>formal_greeting_005.mp3</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        
                        <!-- Account Management Tab -->
                        <div class="tab-content" id="accounts-tab" style="display: none;">
                            <div>
                                <h2 style="margin-top: 0; color: #FFF;">Account Management</h2>
                                <p style="color: #CCC;">Select accounts to update their voicemail greetings individually.</p>
                            </div>
                            
                            <div class="filter-controls">
                                <div style="display: flex; margin-bottom: 15px; gap: 15px; flex-wrap: wrap;">
                                    <div>
                                        <label style="display: block; margin-bottom: 5px; color: #CCC;">Phone Number</label>
                                        <input type="text" placeholder="Enter phone number" style="padding: 8px; background-color: #333; color: white; border: 1px solid #444; border-radius: 3px; width: 180px;">
                                    </div>
                                    <div>
                                        <label style="display: block; margin-bottom: 5px; color: #CCC;">Username</label>
                                        <input type="text" placeholder="Enter username" style="padding: 8px; background-color: #333; color: white; border: 1px solid #444; border-radius: 3px; width: 180px;">
                                    </div>
                                    <div>
                                        <label style="display: block; margin-bottom: 5px; color: #CCC;">Area Code</label>
                                        <select style="padding: 8px; background-color: #333; color: white; border: 1px solid #444; border-radius: 3px; width: 180px;">
                                            <option value="">All Area Codes</option>
                                            <option value="954">954 (Fort Lauderdale)</option>
                                            <option value="754">754 (Fort Lauderdale)</option>
                                            <option value="305">305 (Miami)</option>
                                            <option value="786">786 (Miami)</option>
                                            <option value="561">561 (West Palm Beach)</option>
                                        </select>
                                    </div>
                                </div>
                                <button class="action-button">Search</button>
                            </div>
                            
                            <div style="margin-top: 20px;">
                                <table class="setup-table">
                                    <thead>
                                        <tr>
                                            <th style="width: 40px;"><input type="checkbox" id="select-all"></th>
                                            <th>Phone Number</th>
                                            <th>Username</th>
                                            <th>Current Voicemail</th>
                                            <th>Last Changed</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td><input type="checkbox" class="account-select"></td>
                                            <td>+1 (954) 555-1234</td>
                                            <td>user123</td>
                                            <td>greeting_001.mp3</td>
                                            <td>2 days ago</td>
                                            <td><button class="action-button" style="padding: 5px 10px; font-size: 12px;">Change</button></td>
                                        </tr>
                                        <tr>
                                            <td><input type="checkbox" class="account-select"></td>
                                            <td>+1 (754) 555-2345</td>
                                            <td>textnow456</td>
                                            <td>casual_greeting_002.mp3</td>
                                            <td>1 week ago</td>
                                            <td><button class="action-button" style="padding: 5px 10px; font-size: 12px;">Change</button></td>
                                        </tr>
                                        <tr>
                                            <td><input type="checkbox" class="account-select"></td>
                                            <td>+1 (305) 555-3456</td>
                                            <td>miami789</td>
                                            <td>professional_001.mp3</td>
                                            <td>3 days ago</td>
                                            <td><button class="action-button" style="padding: 5px 10px; font-size: 12px;">Change</button></td>
                                        </tr>
                                        <tr>
                                            <td><input type="checkbox" class="account-select"></td>
                                            <td>+1 (786) 555-4567</td>
                                            <td>florida234</td>
                                            <td>formal_greeting_005.mp3</td>
                                            <td>5 days ago</td>
                                            <td><button class="action-button" style="padding: 5px 10px; font-size: 12px;">Change</button></td>
                                        </tr>
                                        <tr>
                                            <td><input type="checkbox" class="account-select"></td>
                                            <td>+1 (561) 555-5678</td>
                                            <td>palm567</td>
                                            <td>casual_female_003.mp3</td>
                                            <td>2 weeks ago</td>
                                            <td><button class="action-button" style="padding: 5px 10px; font-size: 12px;">Change</button></td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            
                            <div style="margin-top: 20px; text-align: right;">
                                <button id="change-selected" class="action-button">Change Selected Accounts</button>
                            </div>
                        </div>
                        
                        <!-- Operations Tab -->
                        <div class="tab-content" id="operations-tab" style="display: none;">
                            <div>
                                <h2 style="margin-top: 0; color: #FFF;">Voicemail Operations</h2>
                                <p style="color: #CCC;">Track current and scheduled voicemail operations.</p>
                            </div>
                            
                            <div class="setup-status">
                                <h3 style="margin-top: 0; color: #DDD; font-size: 16px;">Current Operations</h3>
                                <table class="setup-table">
                                    <thead>
                                        <tr>
                                            <th>Operation</th>
                                            <th>Account</th>
                                            <th>Status</th>
                                            <th>Progress</th>
                                            <th>Started</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>Change Voicemail</td>
                                            <td>+1 (305) 555-3456</td>
                                            <td><span class="status-label status-in-progress">In Progress</span></td>
                                            <td>
                                                <div class="progress-bar-container" style="width: 100px; height: 10px;">
                                                    <div class="progress-bar" style="width: 65%;"></div>
                                                </div>
                                            </td>
                                            <td>Just now</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            
                            <div class="setup-status" style="margin-top: 20px;">
                                <h3 style="margin-top: 0; color: #DDD; font-size: 16px;">Operation History</h3>
                                <table class="setup-table">
                                    <thead>
                                        <tr>
                                            <th>Operation</th>
                                            <th>Account</th>
                                            <th>Status</th>
                                            <th>Voicemail</th>
                                            <th>Completed</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>Change Voicemail</td>
                                            <td>+1 (954) 555-1234</td>
                                            <td><span class="status-label status-completed">Completed</span></td>
                                            <td>greeting_001.mp3</td>
                                            <td>2 days ago</td>
                                        </tr>
                                        <tr>
                                            <td>Change Voicemail</td>
                                            <td>+1 (754) 555-2345</td>
                                            <td><span class="status-label status-completed">Completed</span></td>
                                            <td>casual_greeting_002.mp3</td>
                                            <td>1 week ago</td>
                                        </tr>
                                        <tr>
                                            <td>Change Voicemail</td>
                                            <td>+1 (561) 555-5678</td>
                                            <td><span class="status-label status-failed">Failed</span></td>
                                            <td>casual_female_003.mp3</td>
                                            <td>2 weeks ago</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                © ProgressBets™ | TextNow v1.0.0 | 5 Accounts Active
            </div>
        </div>
        
        <script>
            // Tab switching
            document.querySelectorAll('.tab').forEach(tab => {
                tab.addEventListener('click', function() {
                    // Update tab styling
                    document.querySelectorAll('.tab').forEach(t => {
                        t.classList.remove('active');
                        t.style.borderBottom = '2px solid transparent';
                    });
                    this.classList.add('active');
                    this.style.borderBottom = '2px solid #FF6600';
                    
                    // Hide all tab content
                    document.querySelectorAll('.tab-content').forEach(content => {
                        content.style.display = 'none';
                    });
                    
                    // Show selected tab content
                    const tabId = this.getAttribute('data-tab');
                    document.getElementById(tabId + '-tab').style.display = 'block';
                });
            });
            
            // Select all checkbox
            document.getElementById('select-all').addEventListener('change', function() {
                document.querySelectorAll('.account-select').forEach(checkbox => {
                    checkbox.checked = this.checked;
                });
            });
            
            // Change selected accounts button
            document.getElementById('change-selected').addEventListener('click', function() {
                const selectedCount = document.querySelectorAll('.account-select:checked').length;
                if (selectedCount > 0) {
                    const voicemailModal = `
                        <div id="voicemail-modal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.7); display: flex; justify-content: center; align-items: center; z-index: 1000;">
                            <div style="background-color: #333; border-radius: 5px; padding: 20px; width: 400px;">
                                <h3 style="margin-top: 0; color: #FFF;">Change Voicemail</h3>
                                <p>Select a voicemail for ${selectedCount} account(s):</p>
                                
                                <div style="display: flex; margin-bottom: 15px;">
                                    <input type="radio" id="random-vm" name="vm-selection" checked style="margin-right: 10px;">
                                    <label for="random-vm">Assign Random Voicemail</label>
                                </div>
                                
                                <div style="display: flex; margin-bottom: 15px;">
                                    <input type="radio" id="specific-vm" name="vm-selection" style="margin-right: 10px;">
                                    <label for="specific-vm">Choose Specific Voicemail</label>
                                </div>
                                
                                <select id="vm-select" style="width: 100%; padding: 8px; background-color: #222; color: white; border: 1px solid #444; border-radius: 3px; margin-bottom: 20px;" disabled>
                                    <option value="">Select a voicemail file...</option>
                                    <option value="greeting_001.mp3">greeting_001.mp3</option>
                                    <option value="casual_greeting_002.mp3">casual_greeting_002.mp3</option>
                                    <option value="professional_001.mp3">professional_001.mp3</option>
                                    <option value="formal_greeting_005.mp3">formal_greeting_005.mp3</option>
                                    <option value="casual_female_003.mp3">casual_female_003.mp3</option>
                                </select>
                                
                                <div style="text-align: right;">
                                    <button id="cancel-vm-change" class="secondary-button" style="margin-right: 10px;">Cancel</button>
                                    <button id="confirm-vm-change" class="action-button">Apply Change</button>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    document.body.insertAdjacentHTML('beforeend', voicemailModal);
                    
                    // Radio button toggle for select
                    document.getElementById('specific-vm').addEventListener('change', function() {
                        document.getElementById('vm-select').disabled = !this.checked;
                    });
                    
                    document.getElementById('random-vm').addEventListener('change', function() {
                        document.getElementById('vm-select').disabled = this.checked;
                    });
                    
                    // Cancel button
                    document.getElementById('cancel-vm-change').addEventListener('click', function() {
                        document.getElementById('voicemail-modal').remove();
                    });
                    
                    // Confirm button
                    document.getElementById('confirm-vm-change').addEventListener('click', function() {
                        const isRandom = document.getElementById('random-vm').checked;
                        const selectedVM = document.getElementById('vm-select').value;
                        
                        let message = isRandom ? 
                            `Applying random voicemail to ${selectedCount} account(s)` : 
                            `Applying "${selectedVM}" to ${selectedCount} account(s)`;
                            
                        alert(message);
                        
                        // In a real implementation, you would send this to the server
                        // and it would initiate the voicemail change process for each selected account
                        
                        document.getElementById('voicemail-modal').remove();
                        
                        // Navigate to the Operations tab to show progress
                        document.querySelector('.tab[data-tab="operations"]').click();
                    });
                } else {
                    alert('Please select at least one account');
                }
            });
            
            // Add click handlers for individual "Change" buttons
            document.querySelectorAll('.account-select').forEach((checkbox, index) => {
                const changeButton = document.querySelectorAll('button.action-button[style*="padding: 5px 10px"]')[index];
                changeButton.addEventListener('click', function() {
                    const row = this.closest('tr');
                    const phoneNumber = row.children[1].textContent;
                    const username = row.children[2].textContent;
                    
                    // Show the same modal but for a single account
                    const voicemailModal = `
                        <div id="voicemail-modal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.7); display: flex; justify-content: center; align-items: center; z-index: 1000;">
                            <div style="background-color: #333; border-radius: 5px; padding: 20px; width: 400px;">
                                <h3 style="margin-top: 0; color: #FFF;">Change Voicemail</h3>
                                <p>Select a voicemail for account ${phoneNumber} (${username}):</p>
                                
                                <div style="display: flex; margin-bottom: 15px;">
                                    <input type="radio" id="random-vm" name="vm-selection" checked style="margin-right: 10px;">
                                    <label for="random-vm">Assign Random Voicemail</label>
                                </div>
                                
                                <div style="display: flex; margin-bottom: 15px;">
                                    <input type="radio" id="specific-vm" name="vm-selection" style="margin-right: 10px;">
                                    <label for="specific-vm">Choose Specific Voicemail</label>
                                </div>
                                
                                <select id="vm-select" style="width: 100%; padding: 8px; background-color: #222; color: white; border: 1px solid #444; border-radius: 3px; margin-bottom: 20px;" disabled>
                                    <option value="">Select a voicemail file...</option>
                                    <option value="greeting_001.mp3">greeting_001.mp3</option>
                                    <option value="casual_greeting_002.mp3">casual_greeting_002.mp3</option>
                                    <option value="professional_001.mp3">professional_001.mp3</option>
                                    <option value="formal_greeting_005.mp3">formal_greeting_005.mp3</option>
                                    <option value="casual_female_003.mp3">casual_female_003.mp3</option>
                                </select>
                                
                                <div style="text-align: right;">
                                    <button id="cancel-vm-change" class="secondary-button" style="margin-right: 10px;">Cancel</button>
                                    <button id="confirm-vm-change" class="action-button">Apply Change</button>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    document.body.insertAdjacentHTML('beforeend', voicemailModal);
                    
                    // Radio button toggle for select
                    document.getElementById('specific-vm').addEventListener('change', function() {
                        document.getElementById('vm-select').disabled = !this.checked;
                    });
                    
                    document.getElementById('random-vm').addEventListener('change', function() {
                        document.getElementById('vm-select').disabled = this.checked;
                    });
                    
                    // Cancel button
                    document.getElementById('cancel-vm-change').addEventListener('click', function() {
                        document.getElementById('voicemail-modal').remove();
                    });
                    
                    // Confirm button
                    document.getElementById('confirm-vm-change').addEventListener('click', function() {
                        const isRandom = document.getElementById('random-vm').checked;
                        const selectedVM = document.getElementById('vm-select').value;
                        
                        let message = isRandom ? 
                            `Applying random voicemail to account ${phoneNumber}` : 
                            `Applying "${selectedVM}" to account ${phoneNumber}`;
                            
                        alert(message);
                        
                        // In a real implementation, you would send this to the server
                        // and it would initiate the voicemail change process
                        
                        document.getElementById('voicemail-modal').remove();
                        
                        // Navigate to the Operations tab to show progress
                        document.querySelector('.tab[data-tab="operations"]').click();
                    });
                });
            });
            
            // Import voicemails
            document.getElementById('import-vms').addEventListener('click', function() {
                document.getElementById('folder-picker').click();
            });
            
            // Handle folder selection
            document.getElementById('folder-picker').addEventListener('change', function(e) {
                const files = e.target.files;
                if (files.length > 0) {
                    alert(`Selected ${files.length} files for import`);
                    // In a real implementation, you would upload these files
                }
            });
            
            // Drag and drop functionality
            const dropZone = document.getElementById('drag-drop-zone');
            
            dropZone.addEventListener('dragover', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.style.borderColor = '#FF6600';
                this.style.backgroundColor = 'rgba(255, 102, 0, 0.1)';
            });
            
            dropZone.addEventListener('dragleave', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.style.borderColor = '#444';
                this.style.backgroundColor = 'transparent';
            });
            
            dropZone.addEventListener('drop', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.style.borderColor = '#444';
                this.style.backgroundColor = 'transparent';
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    alert(`Dropped ${files.length} files for import`);
                    // In a real implementation, you would upload these files
                }
            });
            
            // Start/stop setup
            document.getElementById('start-setup').addEventListener('click', function() {
                // In a real implementation, you would start the setup process
                this.disabled = true;
                document.getElementById('stop-setup').disabled = false;
                alert('Started voicemail setup process');
            });
            
            document.getElementById('stop-setup').addEventListener('click', function() {
                // In a real implementation, you would stop the setup process
                this.disabled = true;
                document.getElementById('start-setup').disabled = false;
                alert('Stopped voicemail setup process');
            });
            
            // Play buttons
            const playButtons = document.querySelectorAll('.file-play');
            playButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const fileName = this.parentNode.previousElementSibling.textContent;
                    alert(`Playing ${fileName}`);
                    // In a real implementation, you would play the audio file
                });
            });
        </script>
    </body>
    </html>
    ''', logo_exists=logo_exists)