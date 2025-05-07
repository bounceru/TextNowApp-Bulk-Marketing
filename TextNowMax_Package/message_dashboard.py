"""
Message Monitoring Dashboard for ProgressGhostCreator

This module provides a Flask route to display the message monitoring dashboard interface
for tracking and managing all incoming messages across TextNow accounts.
"""

import os
import json
from datetime import datetime, timedelta
from flask import render_template_string, request, jsonify

from message_monitor import get_message_monitor

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

def message_dashboard_page(logo_exists=False, nav_menu=""):
    """Return the message monitoring dashboard HTML"""
    if not logo_exists:
        logo_exists = os.path.exists("static/progress_logo.png")
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ProgressGhostCreator - Message Dashboard</title>
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
            
            .filter-controls {
                display: flex;
                margin-bottom: 15px;
                gap: 15px;
                flex-wrap: wrap;
            }
            
            .filter-controls label {
                display: block;
                margin-bottom: 5px;
                color: #CCC;
                font-size: 14px;
            }
            
            .filter-controls input, .filter-controls select {
                padding: 8px;
                background-color: #333;
                color: white;
                border: 1px solid #444;
                border-radius: 3px;
                width: 180px;
            }
            
            .message-tabs {
                display: flex;
                border-bottom: 1px solid #444;
                margin-bottom: 20px;
            }
            
            .message-tab {
                padding: 10px 20px;
                cursor: pointer;
                border-bottom: 2px solid transparent;
                color: #CCC;
            }
            
            .message-tab.active {
                color: white;
                border-bottom: 2px solid #FF6600;
            }
            
            .message-list {
                flex: 1;
                overflow-y: auto;
            }
            
            .message-item {
                margin-bottom: 15px;
                padding: 15px;
                background-color: #333;
                border-radius: 5px;
                cursor: pointer;
                border-left: 3px solid transparent;
            }
            
            .message-item:hover {
                background-color: #393939;
            }
            
            .message-item.unread {
                border-left: 3px solid #FF6600;
            }
            
            .message-item.selected {
                background-color: #3A3A3A;
                border: 1px solid #555;
            }
            
            .message-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 10px;
            }
            
            .message-meta {
                display: flex;
                flex-direction: column;
            }
            
            .message-account {
                font-weight: bold;
                color: #EEE;
                margin-bottom: 5px;
            }
            
            .message-contact {
                color: #AAA;
                font-size: 13px;
            }
            
            .message-time {
                color: #999;
                font-size: 12px;
                text-align: right;
            }
            
            .message-preview {
                color: #CCC;
                font-size: 14px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .message-status {
                font-size: 12px;
                margin-top: 5px;
                text-align: right;
            }
            
            .status-responded {
                color: #28A745;
            }
            
            .status-pending {
                color: #FFC107;
            }
            
            .status-failed {
                color: #DC3545;
            }
            
            .conversation-view {
                display: flex;
                flex-direction: column;
                height: 100%;
            }
            
            .conversation-header {
                padding: 15px;
                background-color: #333;
                border-bottom: 1px solid #444;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .contact-info {
                display: flex;
                flex-direction: column;
            }
            
            .contact-name {
                font-weight: bold;
                color: #EEE;
                font-size: 16px;
            }
            
            .contact-number {
                color: #AAA;
                font-size: 13px;
            }
            
            .conversation-actions {
                display: flex;
                gap: 10px;
            }
            
            .action-icon {
                background-color: transparent;
                color: #CCC;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                cursor: pointer;
                font-size: 14px;
            }
            
            .action-icon:hover {
                color: white;
                background-color: #444;
            }
            
            .messages-container {
                flex: 1;
                overflow-y: auto;
                padding: 15px;
                display: flex;
                flex-direction: column;
            }
            
            .message-bubble {
                max-width: 70%;
                padding: 12px;
                border-radius: 10px;
                margin-bottom: 15px;
                position: relative;
            }
            
            .message-incoming {
                align-self: flex-start;
                background-color: #333;
                border-top-left-radius: 0;
            }
            
            .message-outgoing {
                align-self: flex-end;
                background-color: #0B93F6;
                border-top-right-radius: 0;
            }
            
            .message-text {
                color: white;
                font-size: 14px;
                margin: 0;
            }
            
            .message-timestamp {
                font-size: 11px;
                margin-top: 5px;
                color: rgba(255, 255, 255, 0.6);
                text-align: right;
            }
            
            .reply-form {
                padding: 15px;
                background-color: #333;
                border-top: 1px solid #444;
                display: flex;
                gap: 10px;
            }
            
            .reply-input {
                flex: 1;
                padding: 12px;
                background-color: #222;
                color: white;
                border: 1px solid #444;
                border-radius: 5px;
                resize: none;
            }
            
            .send-button {
                background-color: #FF6600;
                color: white;
                border: none;
                padding: 0 15px;
                cursor: pointer;
                border-radius: 5px;
                font-weight: bold;
            }
            
            .send-button:hover {
                background-color: #FF7722;
            }
            
            .conversation-placeholder {
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100%;
                color: #777;
                text-align: center;
                padding: 20px;
            }
            
            .placeholder-icon {
                font-size: 48px;
                margin-bottom: 20px;
                color: #555;
            }
            
            .placeholder-text {
                font-size: 16px;
                margin-bottom: 10px;
            }
            
            .placeholder-subtext {
                font-size: 14px;
                color: #666;
            }
            
            .accounts-list {
                max-height: 300px;
                overflow-y: auto;
                margin-top: 15px;
            }
            
            .account-item {
                padding: 10px;
                border-radius: 5px;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 5px;
            }
            
            .account-item:hover {
                background-color: #2A2A2A;
            }
            
            .account-item.active {
                background-color: #2A2A2A;
                border-left: 2px solid #FF6600;
            }
            
            .account-info {
                display: flex;
                flex-direction: column;
            }
            
            .account-number {
                font-weight: bold;
                color: #EEE;
            }
            
            .account-details {
                font-size: 12px;
                color: #AAA;
            }
            
            .account-badge {
                background-color: #FF6600;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            
            .quick-stats {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
                margin-bottom: 20px;
            }
            
            .stat-box {
                background-color: #333;
                border-radius: 5px;
                padding: 15px;
                text-align: center;
            }
            
            .stat-value {
                font-size: 24px;
                font-weight: bold;
                color: #FF6600;
                margin-bottom: 5px;
            }
            
            .stat-label {
                font-size: 12px;
                color: #CCC;
            }
            
            .filters-section {
                padding: 15px;
                background-color: #333;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            
            .refresh-button {
                background-color: transparent;
                color: #CCC;
                border: 1px solid #555;
                padding: 8px 15px;
                cursor: pointer;
                border-radius: 3px;
                display: flex;
                align-items: center;
                gap: 5px;
            }
            
            .refresh-button:hover {
                background-color: #444;
                color: white;
            }
            
            .refresh-icon {
                font-size: 16px;
            }
            
            .footer {
                padding: 10px;
                background-color: #222;
                border-top: 1px solid #444;
                text-align: center;
                font-size: 12px;
                color: #AAA;
            }
            
            /* Empty state */
            .empty-state {
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100%;
                color: #777;
                text-align: center;
                padding: 20px;
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
                {{ nav_menu|safe }}
            </div>
            
            <div class="app-content">
                <div class="left-panel">
                    <div class="panel-header">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>Messages</div>
                            <button class="refresh-button">
                                <span class="refresh-icon">↻</span>
                                Refresh
                            </button>
                        </div>
                    </div>
                    
                    <div class="panel-content">
                        <div class="filter-controls">
                            <div>
                                <label>Search</label>
                                <input type="text" placeholder="Search messages..." id="message-search">
                            </div>
                        </div>
                        
                        <div class="message-tabs">
                            <div class="message-tab active" data-tab="all">All Messages</div>
                            <div class="message-tab" data-tab="unread">Unread (12)</div>
                            <div class="message-tab" data-tab="important">Important (3)</div>
                        </div>
                        
                        <div class="message-list">
                            <div class="message-item unread" data-id="1">
                                <div class="message-header">
                                    <div class="message-meta">
                                        <div class="message-account">+1 (954) 555-1234</div>
                                        <div class="message-contact">From: +1 (305) 987-6543</div>
                                    </div>
                                    <div class="message-time">10 min ago</div>
                                </div>
                                <div class="message-preview">Hey there, I got your message. I'm interested in learning more about your service.</div>
                                <div class="message-status status-pending">Awaiting Reply</div>
                            </div>
                            
                            <div class="message-item" data-id="2">
                                <div class="message-header">
                                    <div class="message-meta">
                                        <div class="message-account">+1 (754) 555-2345</div>
                                        <div class="message-contact">From: +1 (786) 765-4321</div>
                                    </div>
                                    <div class="message-time">1 hour ago</div>
                                </div>
                                <div class="message-preview">Thanks for the info. Can we schedule a call to discuss this further?</div>
                                <div class="message-status status-responded">Replied</div>
                            </div>
                            
                            <div class="message-item unread" data-id="3">
                                <div class="message-header">
                                    <div class="message-meta">
                                        <div class="message-account">+1 (305) 555-3456</div>
                                        <div class="message-contact">From: +1 (954) 543-2109</div>
                                    </div>
                                    <div class="message-time">3 hours ago</div>
                                </div>
                                <div class="message-preview">This is exactly what I've been looking for. When can we start?</div>
                                <div class="message-status status-pending">Awaiting Reply</div>
                            </div>
                            
                            <div class="message-item" data-id="4">
                                <div class="message-header">
                                    <div class="message-meta">
                                        <div class="message-account">+1 (786) 555-4567</div>
                                        <div class="message-contact">From: +1 (561) 234-5678</div>
                                    </div>
                                    <div class="message-time">5 hours ago</div>
                                </div>
                                <div class="message-preview">Can you send me more details about pricing? I want to make sure it's within my budget.</div>
                                <div class="message-status status-responded">Replied</div>
                            </div>
                            
                            <div class="message-item" data-id="5">
                                <div class="message-header">
                                    <div class="message-meta">
                                        <div class="message-account">+1 (561) 555-5678</div>
                                        <div class="message-contact">From: +1 (305) 876-5432</div>
                                    </div>
                                    <div class="message-time">Yesterday</div>
                                </div>
                                <div class="message-preview">I'm not interested at this time. Please remove me from your list.</div>
                                <div class="message-status status-responded">Replied</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="right-panel">
                    <!-- Will show selected conversation or placeholder -->
                    <div class="conversation-placeholder">
                        <div class="placeholder-icon">✉️</div>
                        <div class="placeholder-text">Select a message to view the conversation</div>
                        <div class="placeholder-subtext">You can reply to messages, mark as important, or add notes</div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                © ProgressBets™ | TextNow v1.0.0 | 5 Accounts Active
            </div>
        </div>
        
        <script>
            // Message item click handler
            document.querySelectorAll('.message-item').forEach(item => {
                item.addEventListener('click', function() {
                    // Deselect all
                    document.querySelectorAll('.message-item').forEach(i => {
                        i.classList.remove('selected');
                    });
                    
                    // Select this one
                    this.classList.add('selected');
                    
                    // Remove unread status (if applicable)
                    this.classList.remove('unread');
                    
                    // Get message ID
                    const messageId = this.getAttribute('data-id');
                    
                    // In a real implementation, you would fetch the conversation from the server
                    // For this demo, we'll just display a mock conversation
                    showConversation(messageId);
                });
            });
            
            // Tab switching
            document.querySelectorAll('.message-tab').forEach(tab => {
                tab.addEventListener('click', function() {
                    // Update tab styling
                    document.querySelectorAll('.message-tab').forEach(t => {
                        t.classList.remove('active');
                    });
                    this.classList.add('active');
                    
                    // Filter messages based on selected tab
                    const tabType = this.getAttribute('data-tab');
                    filterMessages(tabType);
                });
            });
            
            // Search input functionality
            document.getElementById('message-search').addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase();
                filterMessagesByText(searchTerm);
            });
            
            // Filter messages based on tab
            function filterMessages(tabType) {
                const messageItems = document.querySelectorAll('.message-item');
                
                messageItems.forEach(item => {
                    if (tabType === 'all') {
                        item.style.display = 'block';
                    } else if (tabType === 'unread' && item.classList.contains('unread')) {
                        item.style.display = 'block';
                    } else if (tabType === 'important' && (item.getAttribute('data-id') === '1' || item.getAttribute('data-id') === '3' || item.getAttribute('data-id') === '4')) {
                        // This is a mock implementation. In a real app, you would check if the message is marked as important
                        item.style.display = 'block';
                    } else {
                        item.style.display = 'none';
                    }
                });
            }
            
            // Filter messages by search text
            function filterMessagesByText(searchTerm) {
                const messageItems = document.querySelectorAll('.message-item');
                
                messageItems.forEach(item => {
                    const account = item.querySelector('.message-account').textContent.toLowerCase();
                    const contact = item.querySelector('.message-contact').textContent.toLowerCase();
                    const preview = item.querySelector('.message-preview').textContent.toLowerCase();
                    
                    if (account.includes(searchTerm) || contact.includes(searchTerm) || preview.includes(searchTerm)) {
                        item.style.display = 'block';
                    } else {
                        item.style.display = 'none';
                    }
                });
            }
            
            // Show conversation for a message
            function showConversation(messageId) {
                // Mock conversations data
                const conversations = {
                    '1': {
                        contact: {
                            name: 'John Smith',
                            number: '+1 (305) 987-6543'
                        },
                        messages: [
                            {
                                outgoing: true,
                                text: 'Hi there! I wanted to reach out about our new service that I think would be perfect for your needs.',
                                timestamp: '10:45 AM'
                            },
                            {
                                outgoing: false,
                                text: 'Hey there, I got your message. I\'m interested in learning more about your service.',
                                timestamp: '11:02 AM'
                            }
                        ]
                    },
                    '2': {
                        contact: {
                            name: 'Lisa Johnson',
                            number: '+1 (786) 765-4321'
                        },
                        messages: [
                            {
                                outgoing: true,
                                text: 'Hello Lisa, I\'m reaching out to tell you about our new promotion. Would you like to hear more?',
                                timestamp: 'Yesterday, 3:25 PM'
                            },
                            {
                                outgoing: false,
                                text: 'Thanks for the info. Can we schedule a call to discuss this further?',
                                timestamp: 'Today, 9:12 AM'
                            },
                            {
                                outgoing: true,
                                text: 'Absolutely! When would be a good time for you?',
                                timestamp: 'Today, 9:30 AM'
                            }
                        ]
                    },
                    '3': {
                        contact: {
                            name: 'Michael Brown',
                            number: '+1 (954) 543-2109'
                        },
                        messages: [
                            {
                                outgoing: true,
                                text: 'Hi Michael, we have a special offer that I thought might interest you. It includes...',
                                timestamp: 'Today, 8:15 AM'
                            },
                            {
                                outgoing: false,
                                text: 'This is exactly what I\'ve been looking for. When can we start?',
                                timestamp: 'Today, 8:45 AM'
                            }
                        ]
                    },
                    '4': {
                        contact: {
                            name: 'Sarah Davis',
                            number: '+1 (561) 234-5678'
                        },
                        messages: [
                            {
                                outgoing: true,
                                text: 'Hello Sarah, I wanted to introduce you to our service that has been helping many people like you.',
                                timestamp: 'Today, 7:30 AM'
                            },
                            {
                                outgoing: false,
                                text: 'Can you send me more details about pricing? I want to make sure it\'s within my budget.',
                                timestamp: 'Today, 7:45 AM'
                            },
                            {
                                outgoing: true,
                                text: 'Of course! Our standard package is $X per month, but we also have custom options available.',
                                timestamp: 'Today, 8:00 AM'
                            }
                        ]
                    },
                    '5': {
                        contact: {
                            name: 'Robert Wilson',
                            number: '+1 (305) 876-5432'
                        },
                        messages: [
                            {
                                outgoing: true,
                                text: 'Hi Robert, I wanted to reach out about a service that might benefit you.',
                                timestamp: 'Yesterday, 2:15 PM'
                            },
                            {
                                outgoing: false,
                                text: 'I\'m not interested at this time. Please remove me from your list.',
                                timestamp: 'Yesterday, 3:30 PM'
                            },
                            {
                                outgoing: true,
                                text: 'I understand. I\'ve removed you from our contact list. Thank you for your time.',
                                timestamp: 'Yesterday, 4:00 PM'
                            }
                        ]
                    }
                };
                
                // Get conversation data
                const conversation = conversations[messageId];
                if (!conversation) return;
                
                // Create conversation HTML
                const conversationHTML = `
                    <div class="conversation-view">
                        <div class="conversation-header">
                            <div class="contact-info">
                                <div class="contact-name">${conversation.contact.name}</div>
                                <div class="contact-number">${conversation.contact.number}</div>
                            </div>
                            <div class="conversation-actions">
                                <button class="action-icon">⭐</button>
                                <button class="action-icon">🗑️</button>
                                <button class="action-icon">⚙️</button>
                            </div>
                        </div>
                        
                        <div class="messages-container">
                            ${conversation.messages.map(msg => `
                                <div class="message-bubble ${msg.outgoing ? 'message-outgoing' : 'message-incoming'}">
                                    <p class="message-text">${msg.text}</p>
                                    <div class="message-timestamp">${msg.timestamp}</div>
                                </div>
                            `).join('')}
                        </div>
                        
                        <div class="reply-form">
                            <textarea class="reply-input" placeholder="Type your reply..."></textarea>
                            <button class="send-button">Send</button>
                        </div>
                    </div>
                `;
                
                // Set the conversation view
                document.querySelector('.right-panel').innerHTML = conversationHTML;
                
                // Scroll to bottom of messages
                const messagesContainer = document.querySelector('.messages-container');
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                
                // Add send button functionality
                document.querySelector('.send-button').addEventListener('click', function() {
                    const replyInput = document.querySelector('.reply-input');
                    const replyText = replyInput.value.trim();
                    
                    if (replyText) {
                        // Add the new message to the UI
                        const newMessage = document.createElement('div');
                        newMessage.className = 'message-bubble message-outgoing';
                        newMessage.innerHTML = `
                            <p class="message-text">${replyText}</p>
                            <div class="message-timestamp">Just now</div>
                        `;
                        
                        messagesContainer.appendChild(newMessage);
                        
                        // Clear input
                        replyInput.value = '';
                        
                        // Scroll to new message
                        messagesContainer.scrollTop = messagesContainer.scrollHeight;
                        
                        // Update message item status to "Replied"
                        const messageItem = document.querySelector(`.message-item[data-id="${messageId}"]`);
                        const statusElement = messageItem.querySelector('.message-status');
                        statusElement.className = 'message-status status-responded';
                        statusElement.textContent = 'Replied';
                        
                        // In a real implementation, you would send this to the server
                        alert(`Reply sent: "${replyText}"`);
                    }
                });
                
                // Handle enter key in textarea
                document.querySelector('.reply-input').addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        document.querySelector('.send-button').click();
                    }
                });
                
                // Star (important) button functionality
                document.querySelector('.action-icon:nth-child(1)').addEventListener('click', function() {
                    this.textContent = this.textContent === '⭐' ? '★' : '⭐';
                    if (this.textContent === '★') {
                        this.style.color = '#FFC107';
                    } else {
                        this.style.color = '';
                    }
                });
                
                // Delete button functionality
                document.querySelector('.action-icon:nth-child(2)').addEventListener('click', function() {
                    if (confirm('Are you sure you want to delete this conversation?')) {
                        // In a real implementation, you would send this to the server
                        document.querySelector('.right-panel').innerHTML = `
                            <div class="conversation-placeholder">
                                <div class="placeholder-icon">✉️</div>
                                <div class="placeholder-text">Select a message to view the conversation</div>
                                <div class="placeholder-subtext">You can reply to messages, mark as important, or add notes</div>
                            </div>
                        `;
                        
                        // Remove the message item from the list
                        const messageItem = document.querySelector(`.message-item[data-id="${messageId}"]`);
                        messageItem.remove();
                    }
                });
            }
        </script>
    </body>
    </html>
    ''', logo_exists=logo_exists)

def get_message_data():
    """Get message data from the message monitor"""
    monitor = get_message_monitor()
    
    # In a real implementation, this would query the monitor for actual message data
    # For this demo, we're using mock data
    
    # Example structure that would be returned:
    return {
        "total_messages": 137,
        "unread_count": 12,
        "important_count": 3,
        "messages": [
            {
                "id": 1,
                "account_id": 42,
                "account_phone": "+1 (954) 555-1234",
                "contact": "+1 (305) 987-6543",
                "contact_name": "John Smith",
                "text": "Hey there, I got your message. I'm interested in learning more about your service.",
                "received_at": (datetime.now() - timedelta(minutes=10)).isoformat(),
                "status": "pending",
                "is_read": False
            },
            # More messages would be here
        ]
    }