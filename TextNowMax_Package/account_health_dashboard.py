"""
Account Health Dashboard for ProgressGhostCreator

This module provides a Flask route to display the account health monitoring interface
which shows accounts that are flagged, blocked, or degraded.
"""

import os
import json
from datetime import datetime, timedelta
from flask import render_template_string, request, jsonify, redirect, url_for

def format_relative_time(timestamp_str):
    """Format a timestamp into a relative time (e.g., '2 hours ago')"""
    if not timestamp_str:
        return "Never"
    
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
    except ValueError:
        # Try parsing as a different format if the ISO format fails
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 7:
        return timestamp.strftime("%b %d, %Y")
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

def account_health_dashboard_page():
    """Return the account health monitoring dashboard HTML"""
    logo_exists = os.path.exists("static/progress_logo.png")
    
    # Sample data for demo - in a real implementation, this would come from the database
    sample_health_data = [
        {
            "id": 1,
            "phone_number": "(954) 123-4567",
            "username": "ghost_user_456",
            "email": "ghost456@progressmail.com",
            "health_score": 98.5,
            "status": "healthy",
            "last_check": (datetime.now() - timedelta(hours=2)).isoformat(),
            "flags": [],
            "risk_level": "low"
        },
        {
            "id": 2,
            "phone_number": "(754) 234-5678",
            "username": "phantom_bet_789",
            "email": "phantom789@progressmail.com",
            "health_score": 92.0,
            "status": "healthy",
            "last_check": (datetime.now() - timedelta(hours=5)).isoformat(),
            "flags": [],
            "risk_level": "low"
        },
        {
            "id": 3,
            "phone_number": "(305) 345-6789",
            "username": "shadow_play_123",
            "email": "shadow123@progressmail.com",
            "health_score": 75.5,
            "status": "degraded",
            "last_check": (datetime.now() - timedelta(hours=1)).isoformat(),
            "flags": ["slow_response", "message_delivery_issues"],
            "risk_level": "medium"
        },
        {
            "id": 4,
            "phone_number": "(786) 456-7890",
            "username": "invisible_win_234",
            "email": "invisible234@progressmail.com",
            "health_score": 45.0,
            "status": "flagged",
            "last_check": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "flags": ["login_failures", "captcha_challenges", "message_delivery_issues"],
            "risk_level": "high"
        },
        {
            "id": 5,
            "phone_number": "(561) 567-8901",
            "username": "stealth_bet_567",
            "email": "stealth567@progressmail.com",
            "health_score": 94.5,
            "status": "healthy",
            "last_check": (datetime.now() - timedelta(hours=8)).isoformat(),
            "flags": [],
            "risk_level": "low"
        },
        {
            "id": 6,
            "phone_number": "(954) 678-9012",
            "username": "under_radar_890",
            "email": "under890@progressmail.com",
            "health_score": 25.0,
            "status": "blocked",
            "last_check": (datetime.now() - timedelta(minutes=10)).isoformat(),
            "flags": ["account_locked", "suspicious_activity_detected", "message_delivery_blocked"],
            "risk_level": "critical"
        },
        {
            "id": 7,
            "phone_number": "(754) 789-0123",
            "username": "ghost_runner_321",
            "email": "runner321@progressmail.com",
            "health_score": 88.0,
            "status": "healthy",
            "last_check": (datetime.now() - timedelta(hours=4)).isoformat(),
            "flags": [],
            "risk_level": "low"
        },
        {
            "id": 8,
            "phone_number": "(305) 890-1234",
            "username": "silent_bet_432",
            "email": "silent432@progressmail.com",
            "health_score": 65.5,
            "status": "degraded",
            "last_check": (datetime.now() - timedelta(hours=1, minutes=15)).isoformat(),
            "flags": ["slow_response", "occasional_login_issues"],
            "risk_level": "medium"
        }
    ]
    
    # Health check types with descriptions
    health_check_types = {
        "login": "Verifies account can log in successfully without captchas or security challenges",
        "message_send": "Tests the ability to send messages to contacts",
        "message_receive": "Verifies the account can receive incoming messages",
        "profile_access": "Checks if the profile page loads correctly and settings can be accessed",
        "api_throttling": "Monitors for any API rate limiting or throttling signs",
        "account_limits": "Checks if the account has hit any usage limits imposed by TextNow"
    }
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ProgressGhostCreator - Account Health Dashboard</title>
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
                width: 1100px;
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
                display: flex;
                justify-content: space-between;
                align-items: center;
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
                padding: 8px 15px;
                cursor: pointer;
                border-radius: 3px;
                font-weight: bold;
                display: inline-block;
                font-size: 13px;
            }
            
            .action-button:hover {
                background-color: #FF7722;
            }
            
            .secondary-button {
                background-color: #444;
                color: white;
                border: none;
                padding: 8px 15px;
                cursor: pointer;
                border-radius: 3px;
                font-weight: bold;
                display: inline-block;
                font-size: 13px;
            }
            
            .secondary-button:hover {
                background-color: #555;
            }
            
            .filter-controls {
                display: flex;
                margin-bottom: 15px;
                gap: 15px;
                flex-wrap: wrap;
            }
            
            .filter-controls select {
                padding: 8px;
                background-color: #333;
                color: white;
                border: 1px solid #444;
                border-radius: 3px;
            }
            
            .health-status-summary {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .status-card {
                background-color: #333;
                border-radius: 5px;
                padding: 15px;
                text-align: center;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .status-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 5px 10px rgba(0, 0, 0, 0.3);
            }
            
            .status-value {
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .status-label {
                font-size: 14px;
                color: #AAA;
            }
            
            .status-healthy {
                border-left: 4px solid #2A2;
            }
            
            .status-healthy .status-value {
                color: #3C3;
            }
            
            .status-degraded {
                border-left: 4px solid #FA0;
            }
            
            .status-degraded .status-value {
                color: #FB3;
            }
            
            .status-flagged {
                border-left: 4px solid #F60;
            }
            
            .status-flagged .status-value {
                color: #F83;
            }
            
            .status-blocked {
                border-left: 4px solid #E33;
            }
            
            .status-blocked .status-value {
                color: #F55;
            }
            
            .actions-bar {
                margin-top: 15px;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .search-box {
                position: relative;
                flex: 1;
                max-width: 300px;
                display: flex;
                align-items: center;
            }
            
            .search-input {
                width: 100%;
                padding: 8px 10px 8px 30px;
                background-color: #444;
                border: none;
                border-radius: 3px;
                color: white;
            }
            
            .search-icon {
                position: absolute;
                left: 10px;
                color: #AAA;
            }
            
            .action-buttons {
                display: flex;
                gap: 10px;
            }
            
            .accounts-table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            
            .accounts-table th {
                background-color: #333;
                padding: 10px;
                text-align: left;
                font-weight: bold;
                border-bottom: 1px solid #444;
                color: #EEE;
            }
            
            .accounts-table td {
                padding: 10px;
                border-bottom: 1px solid #333;
                color: #CCC;
            }
            
            .accounts-table tr:hover td {
                background-color: #2A2A2A;
            }
            
            .health-indicator {
                width: 80px;
                height: 8px;
                background-color: #444;
                border-radius: 4px;
                overflow: hidden;
                display: inline-block;
                vertical-align: middle;
                margin-right: 10px;
            }
            
            .health-fill {
                height: 100%;
                border-radius: 4px;
            }
            
            .health-value {
                display: inline-block;
                vertical-align: middle;
                font-weight: bold;
            }
            
            .status-pill {
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
                text-transform: uppercase;
                display: inline-block;
                text-align: center;
            }
            
            .status-healthy-pill {
                background-color: rgba(34, 170, 34, 0.2);
                color: #3C3;
                border: 1px solid #3C3;
            }
            
            .status-degraded-pill {
                background-color: rgba(255, 170, 0, 0.2);
                color: #FB3;
                border: 1px solid #FA0;
            }
            
            .status-flagged-pill {
                background-color: rgba(255, 102, 0, 0.2);
                color: #F83;
                border: 1px solid #F60;
            }
            
            .status-blocked-pill {
                background-color: rgba(238, 51, 51, 0.2);
                color: #F55;
                border: 1px solid #E33;
            }
            
            .flag-list {
                display: flex;
                gap: 5px;
                flex-wrap: wrap;
            }
            
            .flag-tag {
                background-color: #333;
                color: #CCC;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 11px;
            }
            
            .pagination {
                margin-top: 20px;
                display: flex;
                justify-content: center;
                gap: 5px;
            }
            
            .page-button {
                background-color: #333;
                color: #CCC;
                border: none;
                padding: 5px 10px;
                cursor: pointer;
                border-radius: 3px;
            }
            
            .page-button:hover {
                background-color: #444;
                color: white;
            }
            
            .page-button.active {
                background-color: #FF6600;
                color: white;
            }
            
            .sidebar-section {
                padding: 15px;
                border-bottom: 1px solid #333;
            }
            
            .sidebar-title {
                font-size: 14px;
                font-weight: bold;
                color: #EEE;
                margin-bottom: 10px;
            }
            
            .status-filters {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            
            .filter-item {
                display: flex;
                align-items: center;
                color: #CCC;
                font-size: 14px;
                cursor: pointer;
            }
            
            .filter-item:hover {
                color: white;
            }
            
            .filter-item.active {
                color: #FF6600;
                font-weight: bold;
            }
            
            .filter-count {
                margin-left: auto;
                background-color: #333;
                padding: 2px 6px;
                border-radius: 10px;
                font-size: 12px;
                color: #AAA;
            }
            
            .filter-item.active .filter-count {
                background-color: #FF6600;
                color: white;
            }
            
            .risk-level-filters {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            
            .health-overview {
                width: 100%;
                height: 60px;
                background-color: #333;
                border-radius: 5px;
                margin-bottom: 15px;
                position: relative;
                overflow: hidden;
            }
            
            .health-segment {
                height: 100%;
                position: absolute;
                top: 0;
            }
            
            .critical-segment {
                left: 0;
                width: 10%;
                background-color: #E33;
            }
            
            .high-segment {
                left: 10%;
                width: 5%;
                background-color: #F60;
            }
            
            .medium-segment {
                left: 15%;
                width: 10%;
                background-color: #FA0;
            }
            
            .low-segment {
                left: 25%;
                width: 75%;
                background-color: #2A2;
            }
            
            .health-legend {
                display: flex;
                justify-content: space-between;
                margin-top: 5px;
                font-size: 11px;
                color: #AAA;
            }
            
            .legend-item {
                display: flex;
                align-items: center;
                gap: 5px;
            }
            
            .legend-color {
                width: 10px;
                height: 10px;
                border-radius: 2px;
            }
            
            .critical-color {
                background-color: #E33;
            }
            
            .high-color {
                background-color: #F60;
            }
            
            .medium-color {
                background-color: #FA0;
            }
            
            .low-color {
                background-color: #2A2;
            }
            
            .last-check-info {
                font-size: 12px;
                color: #AAA;
                margin-top: 20px;
                text-align: center;
            }
            
            .tab-container {
                display: flex;
                border-bottom: 1px solid #444;
                background-color: #2A2A2A;
            }
            
            .tab {
                padding: 12px 20px;
                cursor: pointer;
                font-size: 14px;
                color: #CCC;
                border-bottom: 3px solid transparent;
            }
            
            .tab:hover {
                color: white;
                background-color: #333;
            }
            
            .tab.active {
                color: white;
                border-bottom-color: #FF6600;
                background-color: #333;
            }
            
            .account-detail {
                display: none;
                padding: 20px;
                background-color: #2A2A2A;
                border-radius: 5px;
                margin-top: 20px;
            }
            
            .detail-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 1px solid #444;
            }
            
            .account-info {
                display: flex;
                flex-direction: column;
            }
            
            .account-number {
                font-size: 20px;
                font-weight: bold;
                color: white;
                margin-bottom: 5px;
            }
            
            .account-username {
                font-size: 14px;
                color: #CCC;
            }
            
            .detail-actions {
                display: flex;
                gap: 10px;
                align-items: center;
            }
            
            .detail-content {
                display: flex;
                gap: 20px;
            }
            
            .detail-left {
                flex: 1;
            }
            
            .detail-right {
                width: 300px;
                background-color: #333;
                border-radius: 5px;
                padding: 15px;
            }
            
            .detail-section {
                margin-bottom: 20px;
            }
            
            .detail-section-title {
                font-size: 16px;
                font-weight: bold;
                color: #EEE;
                margin-bottom: 10px;
                border-bottom: 1px solid #444;
                padding-bottom: 5px;
            }
            
            .property-list {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            .property-item {
                display: flex;
            }
            
            .property-name {
                width: 140px;
                color: #AAA;
                font-size: 14px;
            }
            
            .property-value {
                flex: 1;
                color: #EEE;
                font-size: 14px;
            }
            
            .check-history {
                margin-top: 20px;
            }
            
            .check-item {
                padding: 10px;
                border-bottom: 1px solid #333;
            }
            
            .check-header {
                display: flex;
                justify-content: space-between;
                font-size: 14px;
                margin-bottom: 5px;
            }
            
            .check-type {
                font-weight: bold;
                color: #EEE;
            }
            
            .check-time {
                color: #AAA;
                font-size: 12px;
            }
            
            .check-result {
                font-size: 13px;
                color: #CCC;
            }
            
            .check-success {
                color: #3C3;
            }
            
            .check-failure {
                color: #F55;
            }
            
            .check-warning {
                color: #FB3;
            }
            
            .footer {
                padding: 10px;
                background-color: #222;
                border-top: 1px solid #444;
                text-align: center;
                font-size: 12px;
                color: #AAA;
            }
            
            .modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(0, 0, 0, 0.7);
                z-index: 1000;
                justify-content: center;
                align-items: center;
            }
            
            .modal-content {
                background-color: #333;
                padding: 20px;
                border-radius: 5px;
                width: 400px;
                max-width: 90%;
            }
            
            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 1px solid #444;
            }
            
            .modal-title {
                font-size: 18px;
                font-weight: bold;
                color: #EEE;
            }
            
            .modal-close {
                background: none;
                border: none;
                color: #AAA;
                font-size: 20px;
                cursor: pointer;
            }
            
            .modal-body {
                margin-bottom: 20px;
            }
            
            .modal-footer {
                display: flex;
                justify-content: flex-end;
                gap: 10px;
            }
            
            .check-detail-card {
                background-color: #2A2A2A;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 15px;
            }
            
            .check-detail-title {
                font-size: 16px;
                font-weight: bold;
                color: #EEE;
                margin-bottom: 10px;
            }
            
            .check-detail-description {
                color: #CCC;
                font-size: 14px;
                margin-bottom: 15px;
            }
            
            .check-status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 5px;
            }
            
            .indicator-healthy {
                background-color: #2A2;
                box-shadow: 0 0 5px #2A2;
            }
            
            .indicator-warning {
                background-color: #FA0;
                box-shadow: 0 0 5px #FA0;
            }
            
            .indicator-error {
                background-color: #E33;
                box-shadow: 0 0 5px #E33;
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
                    <a href="/message-dashboard" class="nav-button">Messages</a>
                    <a href="/campaigns" class="nav-button">Campaigns</a>
                    <a href="/image-dashboard" class="nav-button">Images</a>
                    <a href="/voicemail-manager" class="nav-button">Voicemails</a>
                    <a href="/account-health" class="nav-button active">Health</a>
                </div>
            </div>
            
            <div class="app-content">
                <div class="left-panel">
                    <div class="sidebar-section">
                        <div class="sidebar-title">Account Health Overview</div>
                        <div class="health-overview">
                            <div class="health-segment critical-segment"></div>
                            <div class="health-segment high-segment"></div>
                            <div class="health-segment medium-segment"></div>
                            <div class="health-segment low-segment"></div>
                        </div>
                        <div class="health-legend">
                            <div class="legend-item">
                                <div class="legend-color critical-color"></div>
                                <span>Critical</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color high-color"></div>
                                <span>High</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color medium-color"></div>
                                <span>Medium</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color low-color"></div>
                                <span>Low</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="sidebar-section">
                        <div class="sidebar-title">Status Filters</div>
                        <div class="status-filters">
                            <div class="filter-item active" data-filter="all">
                                <span>All Accounts</span>
                                <span class="filter-count">8</span>
                            </div>
                            <div class="filter-item" data-filter="healthy">
                                <span>Healthy</span>
                                <span class="filter-count">4</span>
                            </div>
                            <div class="filter-item" data-filter="degraded">
                                <span>Degraded</span>
                                <span class="filter-count">2</span>
                            </div>
                            <div class="filter-item" data-filter="flagged">
                                <span>Flagged</span>
                                <span class="filter-count">1</span>
                            </div>
                            <div class="filter-item" data-filter="blocked">
                                <span>Blocked</span>
                                <span class="filter-count">1</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="sidebar-section">
                        <div class="sidebar-title">Risk Level</div>
                        <div class="risk-level-filters">
                            <div class="filter-item" data-filter="critical">
                                <span>Critical Risk</span>
                                <span class="filter-count">1</span>
                            </div>
                            <div class="filter-item" data-filter="high">
                                <span>High Risk</span>
                                <span class="filter-count">1</span>
                            </div>
                            <div class="filter-item" data-filter="medium">
                                <span>Medium Risk</span>
                                <span class="filter-count">2</span>
                            </div>
                            <div class="filter-item" data-filter="low">
                                <span>Low Risk</span>
                                <span class="filter-count">4</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="last-check-info">
                        Last full system check: {{ health_data[0].last_check | format_relative_time }}
                    </div>
                </div>
                
                <div class="right-panel">
                    <div class="panel-header">
                        <span>Account Health Monitor</span>
                        <button class="action-button" id="run-checks-btn">Run Health Checks</button>
                    </div>
                    
                    <div class="panel-content">
                        <div class="health-status-summary">
                            <div class="status-card status-healthy">
                                <div class="status-value">4</div>
                                <div class="status-label">Healthy Accounts</div>
                            </div>
                            <div class="status-card status-degraded">
                                <div class="status-value">2</div>
                                <div class="status-label">Degraded Accounts</div>
                            </div>
                            <div class="status-card status-flagged">
                                <div class="status-value">1</div>
                                <div class="status-label">Flagged Accounts</div>
                            </div>
                            <div class="status-card status-blocked">
                                <div class="status-value">1</div>
                                <div class="status-label">Blocked Accounts</div>
                            </div>
                        </div>
                        
                        <div class="actions-bar">
                            <div class="search-box">
                                <span class="search-icon">🔍</span>
                                <input type="text" class="search-input" placeholder="Search accounts...">
                            </div>
                            
                            <div class="action-buttons">
                                <button class="action-button" id="replace-accounts-btn">Replace Flagged</button>
                                <button class="secondary-button" id="export-report-btn">Export Report</button>
                            </div>
                        </div>
                        
                        <table class="accounts-table">
                            <thead>
                                <tr>
                                    <th style="width: 120px;">Phone Number</th>
                                    <th style="width: 120px;">Username</th>
                                    <th style="width: 160px;">Health Score</th>
                                    <th style="width: 100px;">Status</th>
                                    <th>Flags</th>
                                    <th style="width: 100px;">Last Check</th>
                                    <th style="width: 120px;">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for account in health_data %}
                                <tr data-account-id="{{ account.id }}">
                                    <td>{{ account.phone_number }}</td>
                                    <td>{{ account.username }}</td>
                                    <td>
                                        <div class="health-indicator">
                                            <div class="health-fill" style="width: {{ account.health_score }}%; 
                                            background-color: {{ 
                                                '#2A2' if account.health_score >= 80 else 
                                                '#FA0' if account.health_score >= 60 else 
                                                '#F60' if account.health_score >= 40 else '#E33' 
                                            }};"></div>
                                        </div>
                                        <span class="health-value" style="color: {{ 
                                            '#3C3' if account.health_score >= 80 else 
                                            '#FB3' if account.health_score >= 60 else 
                                            '#F83' if account.health_score >= 40 else '#F55' 
                                        }};">{{ account.health_score }}%</span>
                                    </td>
                                    <td>
                                        <span class="status-pill status-{{ account.status }}-pill">{{ account.status }}</span>
                                    </td>
                                    <td>
                                        <div class="flag-list">
                                            {% for flag in account.flags %}
                                            <span class="flag-tag">{{ flag | replace('_', ' ') }}</span>
                                            {% endfor %}
                                            {% if account.flags|length == 0 %}
                                            <span style="color: #777; font-style: italic; font-size: 12px;">No flags</span>
                                            {% endif %}
                                        </div>
                                    </td>
                                    <td>{{ account.last_check | format_relative_time }}</td>
                                    <td>
                                        <button class="secondary-button view-account-btn" style="padding: 4px 8px; font-size: 12px;" 
                                            data-account-id="{{ account.id }}">Details</button>
                                            
                                        {% if account.status in ['flagged', 'blocked'] %}
                                        <button class="secondary-button replace-account-btn" style="padding: 4px 8px; font-size: 12px; 
                                            background-color: #A22;" data-account-id="{{ account.id }}">Replace</button>
                                        {% endif %}
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                        
                        <div class="pagination">
                            <button class="page-button">«</button>
                            <button class="page-button active">1</button>
                            <button class="page-button">»</button>
                        </div>
                        
                        <!-- Account Detail View (initially hidden) -->
                        <div class="account-detail" id="account-detail-view">
                            <div class="detail-header">
                                <div class="account-info">
                                    <div class="account-number">(954) 123-4567</div>
                                    <div class="account-username">ghost_user_456</div>
                                </div>
                                <div class="detail-actions">
                                    <button class="secondary-button" id="close-detail-btn">Close</button>
                                    <button class="action-button" id="run-specific-checks-btn">Run Checks</button>
                                </div>
                            </div>
                            
                            <div class="tab-container">
                                <div class="tab active" data-tab="overview">Overview</div>
                                <div class="tab" data-tab="checks">Health Checks</div>
                                <div class="tab" data-tab="history">Check History</div>
                                <div class="tab" data-tab="graphs">Performance Graphs</div>
                            </div>
                            
                            <div class="detail-content">
                                <div class="detail-left">
                                    <div class="detail-section">
                                        <div class="detail-section-title">Account Properties</div>
                                        <div class="property-list">
                                            <div class="property-item">
                                                <div class="property-name">Phone Number:</div>
                                                <div class="property-value">(954) 123-4567</div>
                                            </div>
                                            <div class="property-item">
                                                <div class="property-name">Username:</div>
                                                <div class="property-value">ghost_user_456</div>
                                            </div>
                                            <div class="property-item">
                                                <div class="property-name">Email:</div>
                                                <div class="property-value">ghost456@progressmail.com</div>
                                            </div>
                                            <div class="property-item">
                                                <div class="property-name">Created:</div>
                                                <div class="property-value">April 10, 2025</div>
                                            </div>
                                            <div class="property-item">
                                                <div class="property-name">Area Code:</div>
                                                <div class="property-value">954 (Florida)</div>
                                            </div>
                                            <div class="property-item">
                                                <div class="property-name">Health Score:</div>
                                                <div class="property-value" style="color: #3C3;">98.5%</div>
                                            </div>
                                            <div class="property-item">
                                                <div class="property-name">Status:</div>
                                                <div class="property-value">
                                                    <span class="status-pill status-healthy-pill">Healthy</span>
                                                </div>
                                            </div>
                                            <div class="property-item">
                                                <div class="property-name">Risk Level:</div>
                                                <div class="property-value">Low</div>
                                            </div>
                                            <div class="property-item">
                                                <div class="property-name">Message Count:</div>
                                                <div class="property-value">345</div>
                                            </div>
                                            <div class="property-item">
                                                <div class="property-name">Conversation Count:</div>
                                                <div class="property-value">42</div>
                                            </div>
                                            <div class="property-item">
                                                <div class="property-name">Last Used:</div>
                                                <div class="property-value">2 hours ago</div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="detail-section">
                                        <div class="detail-section-title">Recent Health Checks</div>
                                        <div class="check-history">
                                            <div class="check-item">
                                                <div class="check-header">
                                                    <span class="check-type">Login Check</span>
                                                    <span class="check-time">2 hours ago</span>
                                                </div>
                                                <div class="check-result check-success">Successful login without any security challenges</div>
                                            </div>
                                            <div class="check-item">
                                                <div class="check-header">
                                                    <span class="check-type">Message Send Test</span>
                                                    <span class="check-time">2 hours ago</span>
                                                </div>
                                                <div class="check-result check-success">Test message sent successfully</div>
                                            </div>
                                            <div class="check-item">
                                                <div class="check-header">
                                                    <span class="check-type">Message Receive Test</span>
                                                    <span class="check-time">2 hours ago</span>
                                                </div>
                                                <div class="check-result check-success">Successfully received test message</div>
                                            </div>
                                            <div class="check-item">
                                                <div class="check-header">
                                                    <span class="check-type">Profile Access</span>
                                                    <span class="check-time">2 hours ago</span>
                                                </div>
                                                <div class="check-result check-success">Successfully accessed profile settings</div>
                                            </div>
                                            <div class="check-item">
                                                <div class="check-header">
                                                    <span class="check-type">API Throttling Check</span>
                                                    <span class="check-time">2 hours ago</span>
                                                </div>
                                                <div class="check-result check-success">No API rate limiting detected</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="detail-right">
                                    <div class="detail-section-title">Health Summary</div>
                                    <div style="text-align: center; margin: 20px 0;">
                                        <div style="font-size: 48px; font-weight: bold; color: #3C3;">98.5%</div>
                                        <div style="color: #AAA; font-size: 14px;">Overall Health Score</div>
                                    </div>
                                    
                                    <div class="check-detail-card">
                                        <div class="check-detail-title">
                                            <span class="check-status-indicator indicator-healthy"></span>
                                            Account Status
                                        </div>
                                        <div class="check-detail-description">
                                            This account is operating normally with no detected issues. Regular usage is recommended to maintain health.
                                        </div>
                                    </div>
                                    
                                    <div style="font-size: 14px; color: #CCC;">
                                        <p>This account has been active for 15 days and has sent 345 messages across 42 conversations.</p>
                                        <p>No suspicious activity has been detected. The account is performing well within normal parameters.</p>
                                    </div>
                                    
                                    <div style="margin-top: 20px;">
                                        <button class="action-button" style="width: 100%;">Run Full Health Scan</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                © ProgressBets™ | TextNow v1.0.0 | 5 Accounts Active
            </div>
        </div>
        
        <!-- Run Health Checks Modal -->
        <div id="health-checks-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">Run Health Checks</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <p>Select the types of health checks to run:</p>
                    
                    <div style="margin-top: 15px;">
                        {% for check_type, description in health_check_types.items() %}
                        <div style="margin-bottom: 10px;">
                            <label style="display: flex; align-items: flex-start;">
                                <input type="checkbox" checked style="margin-top: 2px; margin-right: 8px;">
                                <div>
                                    <div style="font-weight: bold; color: #EEE;">{{ check_type | replace('_', ' ') | title }}</div>
                                    <div style="font-size: 12px; color: #AAA;">{{ description }}</div>
                                </div>
                            </label>
                        </div>
                        {% endfor %}
                    </div>
                    
                    <div style="margin-top: 15px;">
                        <label style="display: block; margin-bottom: 5px; color: #CCC;">Accounts to check:</label>
                        <select style="width: 100%; padding: 8px; background-color: #222; color: #EEE; border: 1px solid #444; border-radius: 3px;">
                            <option value="all">All accounts</option>
                            <option value="active">Active accounts only</option>
                            <option value="flagged">Flagged accounts only</option>
                            <option value="degraded">Degraded accounts only</option>
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="secondary-button" id="cancel-checks">Cancel</button>
                    <button class="action-button" id="start-checks">Start Checks</button>
                </div>
            </div>
        </div>
        
        <!-- Replace Account Modal -->
        <div id="replace-account-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">Replace Account</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <p>Are you sure you want to replace this TextNow account?</p>
                    
                    <div style="margin-top: 15px; background-color: #2A2A2A; padding: 10px; border-radius: 5px;">
                        <div><strong>Phone Number:</strong> <span id="replace-phone">(954) 456-7890</span></div>
                        <div><strong>Username:</strong> <span id="replace-username">invisible_win_234</span></div>
                        <div><strong>Health Score:</strong> <span id="replace-health" style="color: #F55;">45.0%</span></div>
                        <div><strong>Status:</strong> <span class="status-pill status-flagged-pill">Flagged</span></div>
                    </div>
                    
                    <p style="margin-top: 15px;">The system will:</p>
                    <ol style="color: #CCC; padding-left: 20px;">
                        <li>Backup conversation data from this account</li>
                        <li>Create a new TextNow account</li>
                        <li>Configure the new account with similar settings</li>
                        <li>Mark the old account as replaced</li>
                    </ol>
                    
                    <div style="margin-top: 15px;">
                        <label style="display: block; margin-bottom: 5px; color: #CCC;">Area code for new account:</label>
                        <select style="width: 100%; padding: 8px; background-color: #222; color: #EEE; border: 1px solid #444; border-radius: 3px;">
                            <option value="954">954 (Florida)</option>
                            <option value="754">754 (Florida)</option>
                            <option value="305">305 (Florida)</option>
                            <option value="786">786 (Florida)</option>
                            <option value="561">561 (Florida)</option>
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="secondary-button" id="cancel-replace">Cancel</button>
                    <button class="action-button" id="confirm-replace">Replace Account</button>
                </div>
            </div>
        </div>
        
        <script>
            // Filter functionality
            document.querySelectorAll('.filter-item').forEach(item => {
                item.addEventListener('click', function() {
                    // Update active state for filter items in the same group
                    const parentGroup = this.closest('.status-filters, .risk-level-filters');
                    if (parentGroup) {
                        parentGroup.querySelectorAll('.filter-item').forEach(i => {
                            i.classList.remove('active');
                        });
                    }
                    this.classList.add('active');
                    
                    // In a real application, you would filter the accounts based on the selected filter
                    // For demo purposes, we'll just log the filter
                    console.log('Selected filter:', this.getAttribute('data-filter'));
                });
            });
            
            // Run health checks button
            document.getElementById('run-checks-btn').addEventListener('click', function() {
                const modal = document.getElementById('health-checks-modal');
                modal.style.display = 'flex';
            });
            
            // Replace accounts button
            document.getElementById('replace-accounts-btn').addEventListener('click', function() {
                alert('This will replace all flagged and blocked accounts with new ones.');
            });
            
            // Export report button
            document.getElementById('export-report-btn').addEventListener('click', function() {
                alert('Exporting health report to CSV...');
            });
            
            // View account details buttons
            document.querySelectorAll('.view-account-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const accountId = this.getAttribute('data-account-id');
                    console.log('Viewing account details for ID:', accountId);
                    
                    // Show account detail view
                    document.getElementById('account-detail-view').style.display = 'block';
                    
                    // In a real application, you would load the account details for the specific account
                    // For demo purposes, we're just showing a static view
                    
                    // Scroll to the account detail view
                    document.getElementById('account-detail-view').scrollIntoView({ behavior: 'smooth' });
                });
            });
            
            // Close account detail view button
            document.getElementById('close-detail-btn').addEventListener('click', function() {
                document.getElementById('account-detail-view').style.display = 'none';
            });
            
            // Run specific checks button
            document.getElementById('run-specific-checks-btn').addEventListener('click', function() {
                alert('Running health checks for this specific account...');
            });
            
            // Detail tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.addEventListener('click', function() {
                    // Update active tab
                    document.querySelectorAll('.tab').forEach(t => {
                        t.classList.remove('active');
                    });
                    this.classList.add('active');
                    
                    // In a real application, you would show/hide content based on the selected tab
                    // For demo purposes, we'll just log the tab
                    console.log('Selected tab:', this.getAttribute('data-tab'));
                });
            });
            
            // Replace account buttons
            document.querySelectorAll('.replace-account-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const accountId = this.getAttribute('data-account-id');
                    console.log('Replace account with ID:', accountId);
                    
                    // Show replace account modal
                    const modal = document.getElementById('replace-account-modal');
                    modal.style.display = 'flex';
                    
                    // In a real application, you would populate the modal with the account details
                    // For demo purposes, we're using static content
                });
            });
            
            // Modal close buttons
            document.querySelectorAll('.modal-close').forEach(btn => {
                btn.addEventListener('click', function() {
                    const modal = this.closest('.modal');
                    modal.style.display = 'none';
                });
            });
            
            // Health checks modal buttons
            document.getElementById('cancel-checks').addEventListener('click', function() {
                document.getElementById('health-checks-modal').style.display = 'none';
            });
            
            document.getElementById('start-checks').addEventListener('click', function() {
                document.getElementById('health-checks-modal').style.display = 'none';
                alert('Starting health checks. This process will run in the background.');
            });
            
            // Replace account modal buttons
            document.getElementById('cancel-replace').addEventListener('click', function() {
                document.getElementById('replace-account-modal').style.display = 'none';
            });
            
            document.getElementById('confirm-replace').addEventListener('click', function() {
                document.getElementById('replace-account-modal').style.display = 'none';
                alert('Account replacement process started. A new account will be created and configured.');
            });
            
            // Table row click for account details
            document.querySelectorAll('.accounts-table tbody tr').forEach(row => {
                row.addEventListener('click', function(e) {
                    // Don't trigger when clicking buttons
                    if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                        return;
                    }
                    
                    const accountId = this.getAttribute('data-account-id');
                    console.log('Viewing account details for ID:', accountId);
                    
                    // Show account detail view
                    document.getElementById('account-detail-view').style.display = 'block';
                    
                    // In a real application, you would load the account details for the specific account
                    // For demo purposes, we're just showing a static view
                    
                    // Scroll to the account detail view
                    document.getElementById('account-detail-view').scrollIntoView({ behavior: 'smooth' });
                });
            });
        </script>
    </body>
    </html>
    ''', logo_exists=logo_exists, health_data=sample_health_data, health_check_types=health_check_types, format_relative_time=format_relative_time)