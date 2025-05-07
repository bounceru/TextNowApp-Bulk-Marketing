"""
Campaign Scheduling module for ProgressGhostCreator

This script creates a Flask route to preview the campaign scheduling interface
"""

from flask import render_template_string
import os

def campaign_schedule_page(logo_exists=False, nav_menu=""):
    """Return the campaign scheduling interface HTML"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ProgressGhostCreator - Campaign Schedule</title>
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
            
            .left-panel {
                width: 300px;
                background-color: #252525;
                border-right: 1px solid #444;
                display: flex;
                flex-direction: column;
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
            
            .campaign-title {
                font-size: 18px;
                font-weight: bold;
                color: #EEE;
            }
            
            .action-buttons {
                display: flex;
            }
            
            .action-button {
                background-color: #555;
                color: white;
                border: none;
                padding: 6px 12px;
                margin-left: 8px;
                cursor: pointer;
                border-radius: 3px;
                font-size: 13px;
            }
            
            .action-button:hover {
                background-color: #666;
            }
            
            .primary-action {
                background-color: #FF6600;
            }
            
            .primary-action:hover {
                background-color: #FF7722;
            }
            
            .danger-action {
                background-color: #A22;
            }
            
            .danger-action:hover {
                background-color: #C33;
            }
            
            .schedule-container {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
            }
            
            .schedule-section {
                background-color: #333;
                border-radius: 5px;
                padding: 20px;
                margin-bottom: 20px;
            }
            
            .section-title {
                font-size: 18px;
                font-weight: bold;
                color: #EEE;
                margin-bottom: 15px;
                border-bottom: 1px solid #444;
                padding-bottom: 10px;
            }
            
            .form-row {
                display: flex;
                margin-bottom: 15px;
                align-items: center;
            }
            
            .form-label {
                width: 180px;
                color: #CCC;
                font-size: 14px;
            }
            
            .form-controls {
                flex: 1;
            }
            
            .time-inputs {
                display: flex;
                align-items: center;
            }
            
            .time-input {
                width: 80px;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #222;
                color: #EEE;
                font-size: 14px;
                text-align: center;
            }
            
            .time-separator {
                margin: 0 10px;
                color: #AAA;
            }
            
            .day-checkboxes {
                display: flex;
                flex-wrap: wrap;
            }
            
            .day-checkbox {
                display: flex;
                align-items: center;
                margin-right: 15px;
                margin-bottom: 8px;
            }
            
            .day-checkbox input {
                margin-right: 5px;
            }
            
            .day-label {
                color: #CCC;
                font-size: 14px;
            }
            
            .throttling-control {
                width: 70px;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #222;
                color: #EEE;
                font-size: 14px;
                text-align: center;
            }
            
            .throttling-label {
                margin-left: 10px;
                color: #AAA;
                font-size: 13px;
            }
            
            .slider-container {
                flex: 1;
                display: flex;
                align-items: center;
            }
            
            .slider {
                flex: 1;
                margin: 0 10px;
                -webkit-appearance: none;
                appearance: none;
                height: 10px;
                background: #444;
                border-radius: 5px;
                outline: none;
            }
            
            .slider::-webkit-slider-thumb {
                -webkit-appearance: none;
                appearance: none;
                width: 20px;
                height: 20px;
                border-radius: 50%;
                background: #FF6600;
                cursor: pointer;
            }
            
            .toggle-switch {
                position: relative;
                display: inline-block;
                width: 50px;
                height: 24px;
            }
            
            .toggle-switch input {
                opacity: 0;
                width: 0;
                height: 0;
            }
            
            .toggle-slider {
                position: absolute;
                cursor: pointer;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: #666;
                border-radius: 24px;
                transition: .4s;
            }
            
            .toggle-slider:before {
                position: absolute;
                content: "";
                height: 16px;
                width: 16px;
                left: 4px;
                bottom: 4px;
                background-color: white;
                border-radius: 50%;
                transition: .4s;
            }
            
            input:checked + .toggle-slider {
                background-color: #FF6600;
            }
            
            input:checked + .toggle-slider:before {
                transform: translateX(26px);
            }
            
            .schedule-distribution {
                display: flex;
                height: 200px;
                background-color: #222;
                border-radius: 4px;
                margin-top: 10px;
                position: relative;
                padding: 10px;
                border: 1px solid #444;
            }
            
            .hour-marker {
                position: absolute;
                top: 0;
                height: 100%;
                width: 1px;
                background-color: #444;
            }
            
            .hour-label {
                position: absolute;
                bottom: -20px;
                transform: translateX(-50%);
                color: #AAA;
                font-size: 11px;
            }
            
            .message-bar {
                position: absolute;
                bottom: 30px;
                width: 8px;
                background-color: #FF6600;
                border-radius: 4px;
                transform: translateX(-50%);
            }
            
            .save-schedule {
                margin-top: 20px;
                text-align: right;
            }
            
            .schedule-status {
                display: flex;
                justify-content: space-between;
                margin-top: 20px;
                border-top: 1px solid #444;
                padding-top: 15px;
            }
            
            .status-item {
                display: flex;
                align-items: center;
                color: #CCC;
                font-size: 14px;
            }
            
            .status-indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }
            
            .indicator-active {
                background-color: #2A2;
                box-shadow: 0 0 5px #2A2;
            }
            
            .indicator-inactive {
                background-color: #AAA;
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
                    <div style="padding: 15px; border-bottom: 1px solid #444; color: #CCC; font-size: 16px; font-weight: bold;">
                        Campaign Settings
                    </div>
                    <div style="padding: 15px;">
                        <div style="color: #AAA; margin-bottom: 15px; font-size: 14px;">
                            <div style="margin-bottom: 5px; font-weight: bold;">Campaign Name:</div>
                            March Madness Promotion
                        </div>
                        <div style="color: #AAA; margin-bottom: 15px; font-size: 14px;">
                            <div style="margin-bottom: 5px; font-weight: bold;">Status:</div>
                            <span style="padding: 3px 8px; background-color: #2A2; border-radius: 3px; color: white; font-size: 12px;">Active</span>
                        </div>
                        <div style="color: #AAA; margin-bottom: 15px; font-size: 14px;">
                            <div style="margin-bottom: 5px; font-weight: bold;">Total Messages:</div>
                            10,000
                        </div>
                        <div style="color: #AAA; margin-bottom: 15px; font-size: 14px;">
                            <div style="margin-bottom: 5px; font-weight: bold;">Completed:</div>
                            3,500 (35%)
                        </div>
                        <div style="height: 8px; background-color: #333; border-radius: 4px; overflow: hidden; margin-bottom: 15px;">
                            <div style="height: 100%; background-color: #FF6600; width: 35%"></div>
                        </div>
                        <div style="color: #AAA; margin-bottom: 15px; font-size: 14px;">
                            <div style="margin-bottom: 5px; font-weight: bold;">Settings:</div>
                            <div style="margin-top: 5px; font-size: 13px;">• <a href="/campaigns" style="color: #FF6600; text-decoration: none;">Overview</a></div>
                            <div style="margin-top: 5px; font-size: 13px;">• <a href="#" style="color: #FF6600; text-decoration: none;">Accounts</a></div>
                            <div style="margin-top: 5px; font-size: 13px;">• <a href="#" style="color: #FF6600; text-decoration: none;">Message</a></div>
                            <div style="margin-top: 5px; font-size: 13px; font-weight: bold;">• <a href="/campaign_schedule" style="color: #FF6600; text-decoration: none;">Schedule</a></div>
                        </div>
                    </div>
                </div>
                
                <div class="right-panel">
                    <div class="right-header">
                        <div class="campaign-title">Campaign Schedule Settings</div>
                        <div class="action-buttons">
                            <button class="action-button">Cancel</button>
                            <button class="action-button primary-action">Save Changes</button>
                        </div>
                    </div>
                    
                    <div class="schedule-container">
                        <div class="schedule-section">
                            <div class="section-title">Active Hours</div>
                            <div class="form-row">
                                <div class="form-label">Message Sending Window:</div>
                                <div class="form-controls">
                                    <div class="time-inputs">
                                        <input type="text" class="time-input" value="08:00">
                                        <span class="time-separator">to</span>
                                        <input type="text" class="time-input" value="20:00">
                                    </div>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-label">Active Days:</div>
                                <div class="form-controls">
                                    <div class="day-checkboxes">
                                        <div class="day-checkbox">
                                            <input type="checkbox" id="day-mon" checked>
                                            <label for="day-mon" class="day-label">Monday</label>
                                        </div>
                                        <div class="day-checkbox">
                                            <input type="checkbox" id="day-tue" checked>
                                            <label for="day-tue" class="day-label">Tuesday</label>
                                        </div>
                                        <div class="day-checkbox">
                                            <input type="checkbox" id="day-wed" checked>
                                            <label for="day-wed" class="day-label">Wednesday</label>
                                        </div>
                                        <div class="day-checkbox">
                                            <input type="checkbox" id="day-thu" checked>
                                            <label for="day-thu" class="day-label">Thursday</label>
                                        </div>
                                        <div class="day-checkbox">
                                            <input type="checkbox" id="day-fri" checked>
                                            <label for="day-fri" class="day-label">Friday</label>
                                        </div>
                                        <div class="day-checkbox">
                                            <input type="checkbox" id="day-sat" checked>
                                            <label for="day-sat" class="day-label">Saturday</label>
                                        </div>
                                        <div class="day-checkbox">
                                            <input type="checkbox" id="day-sun" checked>
                                            <label for="day-sun" class="day-label">Sunday</label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="schedule-section">
                            <div class="section-title">Throttling Settings</div>
                            <div class="form-row">
                                <div class="form-label">Messages per Account per Day:</div>
                                <div class="form-controls">
                                    <input type="number" class="throttling-control" value="100">
                                    <span class="throttling-label">Maximum messages each account can send in one day</span>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-label">Messages per Account per Hour:</div>
                                <div class="form-controls">
                                    <input type="number" class="throttling-control" value="15">
                                    <span class="throttling-label">Maximum messages each account can send in one hour</span>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-label">Delay Between Messages:</div>
                                <div class="form-controls slider-container">
                                    <span>5s</span>
                                    <input type="range" min="5" max="60" value="15" class="slider" id="delay-slider">
                                    <span>60s</span>
                                    <input type="number" class="throttling-control" value="15" style="margin-left: 15px;">
                                    <span class="throttling-label">seconds</span>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-label">Batch Size:</div>
                                <div class="form-controls">
                                    <input type="number" class="throttling-control" value="10">
                                    <span class="throttling-label">Messages to send before cooldown period</span>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-label">Cooldown After Batch:</div>
                                <div class="form-controls slider-container">
                                    <span>1m</span>
                                    <input type="range" min="1" max="30" value="5" class="slider" id="cooldown-slider">
                                    <span>30m</span>
                                    <input type="number" class="throttling-control" value="5" style="margin-left: 15px;">
                                    <span class="throttling-label">minutes</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="schedule-section">
                            <div class="section-title">Distribution Pattern</div>
                            <div class="form-row">
                                <div class="form-label">Message Distribution:</div>
                                <div class="form-controls">
                                    <div class="day-checkbox">
                                        <input type="radio" id="dist-even" name="distribution" checked>
                                        <label for="dist-even" class="day-label">Evenly distribute messages throughout active hours</label>
                                    </div>
                                    <div class="day-checkbox">
                                        <input type="radio" id="dist-peak" name="distribution">
                                        <label for="dist-peak" class="day-label">Concentrate messages during peak hours (10am-2pm, 6pm-8pm)</label>
                                    </div>
                                    <div class="day-checkbox">
                                        <input type="radio" id="dist-random" name="distribution">
                                        <label for="dist-random" class="day-label">Randomized distribution with natural patterns</label>
                                    </div>
                                </div>
                            </div>
                            <div class="schedule-distribution">
                                <!-- Hour markers -->
                                <div class="hour-marker" style="left: 0%"><div class="hour-label">8am</div></div>
                                <div class="hour-marker" style="left: 8.33%"><div class="hour-label">9am</div></div>
                                <div class="hour-marker" style="left: 16.66%"><div class="hour-label">10am</div></div>
                                <div class="hour-marker" style="left: 25%"><div class="hour-label">11am</div></div>
                                <div class="hour-marker" style="left: 33.33%"><div class="hour-label">12pm</div></div>
                                <div class="hour-marker" style="left: 41.66%"><div class="hour-label">1pm</div></div>
                                <div class="hour-marker" style="left: 50%"><div class="hour-label">2pm</div></div>
                                <div class="hour-marker" style="left: 58.33%"><div class="hour-label">3pm</div></div>
                                <div class="hour-marker" style="left: 66.66%"><div class="hour-label">4pm</div></div>
                                <div class="hour-marker" style="left: 75%"><div class="hour-label">5pm</div></div>
                                <div class="hour-marker" style="left: 83.33%"><div class="hour-label">6pm</div></div>
                                <div class="hour-marker" style="left: 91.66%"><div class="hour-label">7pm</div></div>
                                <div class="hour-marker" style="left: 100%"><div class="hour-label">8pm</div></div>
                                
                                <!-- Message distribution visualization -->
                                <div class="message-bar" style="left: 4.16%; height: 100px;"></div>
                                <div class="message-bar" style="left: 12.5%; height: 120px;"></div>
                                <div class="message-bar" style="left: 20.83%; height: 140px;"></div>
                                <div class="message-bar" style="left: 29.16%; height: 130px;"></div>
                                <div class="message-bar" style="left: 37.5%; height: 120px;"></div>
                                <div class="message-bar" style="left: 45.83%; height: 110px;"></div>
                                <div class="message-bar" style="left: 54.16%; height: 100px;"></div>
                                <div class="message-bar" style="left: 62.5%; height: 90px;"></div>
                                <div class="message-bar" style="left: 70.83%; height: 100px;"></div>
                                <div class="message-bar" style="left: 79.16%; height: 110px;"></div>
                                <div class="message-bar" style="left: 87.5%; height: 130px;"></div>
                                <div class="message-bar" style="left: 95.83%; height: 120px;"></div>
                            </div>
                        </div>
                        
                        <div class="schedule-section">
                            <div class="section-title">Advanced Options</div>
                            <div class="form-row">
                                <div class="form-label">Natural Typing Simulation:</div>
                                <div class="form-controls">
                                    <label class="toggle-switch">
                                        <input type="checkbox" checked>
                                        <span class="toggle-slider"></span>
                                    </label>
                                    <span class="throttling-label">Simulate natural typing patterns and delays</span>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-label">Human-like Response Time:</div>
                                <div class="form-controls">
                                    <label class="toggle-switch">
                                        <input type="checkbox" checked>
                                        <span class="toggle-slider"></span>
                                    </label>
                                    <span class="throttling-label">Add natural delays between receiving and responding to messages</span>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-label">Auto-Adjust for Engagement:</div>
                                <div class="form-controls">
                                    <label class="toggle-switch">
                                        <input type="checkbox" checked>
                                        <span class="toggle-slider"></span>
                                    </label>
                                    <span class="throttling-label">Prioritize accounts with higher engagement rates</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="save-schedule">
                            <button class="action-button primary-action">Save Schedule Settings</button>
                        </div>
                        
                        <div class="schedule-status">
                            <div class="status-item">
                                <div class="status-indicator indicator-active"></div>
                                Campaign Running
                            </div>
                            <div class="status-item">
                                Next Message: 2 minutes
                            </div>
                            <div class="status-item">
                                Estimated Completion: 4 days, 8 hours
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="app-footer">
                © PB BETTING™ | ProgressGhostCreator v1.0.0 | Messaging System Active
            </div>
        </div>
    </body>
    </html>
    ''', logo_exists=logo_exists)