"""
Image Management Dashboard for ProgressGhostCreator

This module provides a Flask route to display the image management interface
for managing the large pool of images used in TextNow messages.
"""

import os
import json
from datetime import datetime, timedelta
from flask import render_template_string, request, jsonify, redirect, url_for

from image_manager import get_image_manager

def format_file_size(size_bytes):
    """Format file size into human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

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

def image_dashboard_page():
    """Return the image management dashboard HTML"""
    logo_exists = os.path.exists("static/progress_logo.png")
    
    # Get image manager
    image_manager = get_image_manager()
    
    # Get image counts
    image_counts = image_manager.get_image_counts()
    
    # Get categories
    categories = image_manager.categories
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ProgressGhostCreator - Image Manager</title>
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
                padding: 10px 15px;
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
            
            .tabs {
                display: flex;
                border-bottom: 1px solid #444;
                margin-bottom: 20px;
            }
            
            .tab {
                padding: 10px 20px;
                cursor: pointer;
                border-bottom: 2px solid transparent;
                color: #CCC;
            }
            
            .tab.active {
                color: white;
                border-bottom: 2px solid #FF6600;
            }
            
            .category-list {
                margin-bottom: 20px;
            }
            
            .category-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 5px;
                cursor: pointer;
            }
            
            .category-item:hover {
                background-color: #2A2A2A;
            }
            
            .category-item.active {
                background-color: #2A2A2A;
                border-left: 2px solid #FF6600;
            }
            
            .category-name {
                display: flex;
                align-items: center;
            }
            
            .category-icon {
                margin-right: 10px;
                font-size: 16px;
                color: #AAA;
            }
            
            .category-count {
                background-color: #333;
                padding: 3px 8px;
                border-radius: 10px;
                font-size: 12px;
                color: #CCC;
            }
            
            .stats-container {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
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
            
            .image-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }
            
            .image-card {
                background-color: #333;
                border-radius: 5px;
                overflow: hidden;
                cursor: pointer;
                position: relative;
            }
            
            .image-card:hover {
                transform: scale(1.03);
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
                transition: all 0.2s ease;
            }
            
            .image-card.selected {
                border: 2px solid #FF6600;
            }
            
            .image-thumbnail {
                width: 100%;
                height: 120px;
                object-fit: cover;
                display: block;
            }
            
            .image-info {
                padding: 10px;
                font-size: 12px;
            }
            
            .image-filename {
                color: #EEE;
                font-weight: bold;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                margin-bottom: 5px;
            }
            
            .image-meta {
                color: #AAA;
                display: flex;
                justify-content: space-between;
            }
            
            .image-badge {
                position: absolute;
                top: 5px;
                right: 5px;
                background-color: rgba(255, 102, 0, 0.8);
                color: white;
                font-size: 11px;
                padding: 2px 6px;
                border-radius: 10px;
            }
            
            .image-checkbox {
                position: absolute;
                top: 5px;
                left: 5px;
                background-color: rgba(0, 0, 0, 0.5);
                padding: 3px;
                border-radius: 3px;
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
            
            .image-detail {
                display: flex;
                flex-direction: column;
                height: 100%;
            }
            
            .image-preview {
                text-align: center;
                padding: 20px;
                background-color: #222;
                margin-bottom: 20px;
                border-radius: 5px;
            }
            
            .image-preview img {
                max-width: 100%;
                max-height: 300px;
                object-fit: contain;
            }
            
            .image-actions {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }
            
            .image-properties {
                margin-top: 20px;
            }
            
            .property-row {
                display: flex;
                margin-bottom: 10px;
                border-bottom: 1px solid #333;
                padding-bottom: 10px;
            }
            
            .property-label {
                width: 120px;
                color: #AAA;
                font-size: 14px;
            }
            
            .property-value {
                flex: 1;
                color: #EEE;
                font-size: 14px;
            }
            
            .tag-list {
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
                margin-top: 10px;
            }
            
            .tag {
                background-color: #444;
                color: #EEE;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 12px;
                display: flex;
                align-items: center;
            }
            
            .tag-remove {
                margin-left: 5px;
                cursor: pointer;
                font-size: 14px;
            }
            
            .tag-input {
                display: flex;
                gap: 10px;
                margin-top: 10px;
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
            
            .bulk-actions {
                display: flex;
                gap: 10px;
                margin-top: 20px;
                padding-top: 15px;
                border-top: 1px solid #444;
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
                min-width: 400px;
                max-width: 600px;
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
            
            .form-group {
                margin-bottom: 15px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 5px;
                color: #CCC;
            }
            
            .form-control {
                width: 100%;
                padding: 8px;
                background-color: #222;
                border: 1px solid #444;
                border-radius: 3px;
                color: #EEE;
            }
            
            .empty-state {
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 300px;
                color: #777;
                text-align: center;
            }
            
            .empty-icon {
                font-size: 48px;
                margin-bottom: 20px;
                color: #555;
            }
            
            .placeholder-text {
                margin-bottom: 20px;
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
            
            .tag-cloud {
                margin-top: 20px;
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            
            .tag-cloud-item {
                background-color: #333;
                color: #EEE;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 13px;
                cursor: pointer;
            }
            
            .tag-cloud-item:hover {
                background-color: #444;
            }
            
            .tag-cloud-item.active {
                background-color: #FF6600;
                color: white;
            }
            
            .footer {
                padding: 10px;
                background-color: #222;
                border-top: 1px solid #444;
                text-align: center;
                font-size: 12px;
                color: #AAA;
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
                    <a href="/image-dashboard" class="nav-button active">Images</a>
                    <a href="/voicemail-manager" class="nav-button">Voicemails</a>
                </div>
            </div>
            
            <div class="app-content">
                <div class="left-panel">
                    <div class="panel-header">
                        <span>Image Library</span>
                        <button class="secondary-button" id="import-images-btn" style="padding: 5px 10px; font-size: 12px;">Import</button>
                    </div>
                    
                    <div class="panel-content">
                        <div class="stats-container">
                            <div class="stat-box">
                                <div class="stat-value">{{ image_counts.total_images }}</div>
                                <div class="stat-label">Total Images</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-value">{{ image_counts.unused_images }}</div>
                                <div class="stat-label">Unused Images</div>
                            </div>
                        </div>
                        
                        <div class="category-list">
                            <div class="category-item active" data-category="all">
                                <div class="category-name">
                                    <span class="category-icon">📁</span>
                                    All Images
                                </div>
                                <span class="category-count">{{ image_counts.total_images }}</span>
                            </div>
                            
                            {% for category in categories %}
                            <div class="category-item" data-category="{{ category }}">
                                <div class="category-name">
                                    <span class="category-icon">📁</span>
                                    {{ category|capitalize }}
                                </div>
                                <span class="category-count">{{ image_counts.categories.get(category, 0) }}</span>
                            </div>
                            {% endfor %}
                        </div>
                        
                        <div>
                            <div style="margin-bottom: 10px; color: #CCC; font-size: 14px;">Popular Tags</div>
                            <div class="tag-cloud">
                                <div class="tag-cloud-item">sports</div>
                                <div class="tag-cloud-item">betting</div>
                                <div class="tag-cloud-item">football</div>
                                <div class="tag-cloud-item">basketball</div>
                                <div class="tag-cloud-item">baseball</div>
                                <div class="tag-cloud-item">odds</div>
                                <div class="tag-cloud-item">casino</div>
                                <div class="tag-cloud-item">money</div>
                                <div class="tag-cloud-item">winning</div>
                                <div class="tag-cloud-item">logo</div>
                            </div>
                        </div>
                        
                        <div class="drag-drop-area" id="drag-drop-zone">
                            <div class="upload-icon">⬆️</div>
                            <div>Drag & drop image files here</div>
                            <div style="font-size: 12px; color: #AAA; margin-top: 5px;">JPG, PNG, GIF, etc.</div>
                        </div>
                    </div>
                </div>
                
                <div class="right-panel">
                    <div class="panel-header">
                        <div class="search-box">
                            <span class="search-icon">🔍</span>
                            <input type="text" class="search-input" placeholder="Search images...">
                        </div>
                        
                        <div class="filter-controls" style="margin-bottom: 0; margin-left: 15px;">
                            <select id="sort-by" style="width: auto;">
                                <option value="newest">Newest First</option>
                                <option value="oldest">Oldest First</option>
                                <option value="most_used">Most Used</option>
                                <option value="least_used">Least Used</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="panel-content">
                        <div class="tabs">
                            <div class="tab active" data-tab="grid">Grid View</div>
                            <div class="tab" data-tab="details">Details View</div>
                        </div>
                        
                        <div class="tab-content" id="grid-tab">
                            <div class="image-grid">
                                <!-- Sample images - these would be generated from your database -->
                                <div class="image-card">
                                    <div class="image-checkbox">
                                        <input type="checkbox" class="select-image">
                                    </div>
                                    <div class="image-badge">New</div>
                                    <img src="https://via.placeholder.com/200x150" class="image-thumbnail">
                                    <div class="image-info">
                                        <div class="image-filename">sports_betting.jpg</div>
                                        <div class="image-meta">
                                            <span>Sports</span>
                                            <span>0 uses</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="image-card">
                                    <div class="image-checkbox">
                                        <input type="checkbox" class="select-image">
                                    </div>
                                    <img src="https://via.placeholder.com/200x150/444" class="image-thumbnail">
                                    <div class="image-info">
                                        <div class="image-filename">football_odds.jpg</div>
                                        <div class="image-meta">
                                            <span>Sports</span>
                                            <span>2 uses</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="image-card">
                                    <div class="image-checkbox">
                                        <input type="checkbox" class="select-image">
                                    </div>
                                    <img src="https://via.placeholder.com/200x150/333" class="image-thumbnail">
                                    <div class="image-info">
                                        <div class="image-filename">basketball_game.jpg</div>
                                        <div class="image-meta">
                                            <span>Sports</span>
                                            <span>5 uses</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="image-card">
                                    <div class="image-checkbox">
                                        <input type="checkbox" class="select-image">
                                    </div>
                                    <img src="https://via.placeholder.com/200x150/555" class="image-thumbnail">
                                    <div class="image-info">
                                        <div class="image-filename">casino_chips.jpg</div>
                                        <div class="image-meta">
                                            <span>Betting</span>
                                            <span>1 use</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="image-card">
                                    <div class="image-checkbox">
                                        <input type="checkbox" class="select-image">
                                    </div>
                                    <img src="https://via.placeholder.com/200x150/666" class="image-thumbnail">
                                    <div class="image-info">
                                        <div class="image-filename">racing_horses.jpg</div>
                                        <div class="image-meta">
                                            <span>Sports</span>
                                            <span>3 uses</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="image-card">
                                    <div class="image-checkbox">
                                        <input type="checkbox" class="select-image">
                                    </div>
                                    <img src="https://via.placeholder.com/200x150/777" class="image-thumbnail">
                                    <div class="image-info">
                                        <div class="image-filename">betting_slip.jpg</div>
                                        <div class="image-meta">
                                            <span>Betting</span>
                                            <span>7 uses</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="image-card">
                                    <div class="image-checkbox">
                                        <input type="checkbox" class="select-image">
                                    </div>
                                    <div class="image-badge">New</div>
                                    <img src="https://via.placeholder.com/200x150/888" class="image-thumbnail">
                                    <div class="image-info">
                                        <div class="image-filename">bonus_promo.jpg</div>
                                        <div class="image-meta">
                                            <span>Promotional</span>
                                            <span>0 uses</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="image-card">
                                    <div class="image-checkbox">
                                        <input type="checkbox" class="select-image">
                                    </div>
                                    <img src="https://via.placeholder.com/200x150/999" class="image-thumbnail">
                                    <div class="image-info">
                                        <div class="image-filename">jackpot_win.jpg</div>
                                        <div class="image-meta">
                                            <span>Betting</span>
                                            <span>4 uses</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="pagination">
                                <button class="page-button">«</button>
                                <button class="page-button active">1</button>
                                <button class="page-button">2</button>
                                <button class="page-button">3</button>
                                <button class="page-button">»</button>
                            </div>
                            
                            <div class="bulk-actions">
                                <button class="secondary-button" id="select-all-btn">Select All</button>
                                <button class="secondary-button" id="change-category-btn" disabled>Change Category</button>
                                <button class="secondary-button" id="add-tag-btn" disabled>Add Tags</button>
                                <button class="secondary-button danger-action" id="delete-selected-btn" disabled>Delete Selected</button>
                            </div>
                        </div>
                        
                        <div class="tab-content" id="details-tab" style="display: none;">
                            <!-- This would show when an image is selected -->
                            <div class="image-detail">
                                <div class="image-preview">
                                    <img src="https://via.placeholder.com/500x300" alt="Selected image">
                                </div>
                                
                                <div class="image-actions">
                                    <button class="action-button">Change Category</button>
                                    <button class="secondary-button">Add Tag</button>
                                    <button class="secondary-button danger-action">Delete</button>
                                </div>
                                
                                <div class="image-properties">
                                    <div class="property-row">
                                        <div class="property-label">Filename</div>
                                        <div class="property-value">sports_betting.jpg</div>
                                    </div>
                                    
                                    <div class="property-row">
                                        <div class="property-label">Category</div>
                                        <div class="property-value">Sports</div>
                                    </div>
                                    
                                    <div class="property-row">
                                        <div class="property-label">Dimensions</div>
                                        <div class="property-value">800 × 600 pixels</div>
                                    </div>
                                    
                                    <div class="property-row">
                                        <div class="property-label">File Size</div>
                                        <div class="property-value">256 KB</div>
                                    </div>
                                    
                                    <div class="property-row">
                                        <div class="property-label">Created</div>
                                        <div class="property-value">April 24, 2025</div>
                                    </div>
                                    
                                    <div class="property-row">
                                        <div class="property-label">Last Used</div>
                                        <div class="property-value">Never</div>
                                    </div>
                                    
                                    <div class="property-row">
                                        <div class="property-label">Usage Count</div>
                                        <div class="property-value">0</div>
                                    </div>
                                    
                                    <div class="property-row">
                                        <div class="property-label">Tags</div>
                                        <div class="property-value">
                                            <div class="tag-list">
                                                <div class="tag">sports <span class="tag-remove">×</span></div>
                                                <div class="tag">betting <span class="tag-remove">×</span></div>
                                                <div class="tag">football <span class="tag-remove">×</span></div>
                                            </div>
                                            
                                            <div class="tag-input">
                                                <input type="text" class="form-control" placeholder="Add a tag...">
                                                <button class="secondary-button">Add</button>
                                            </div>
                                        </div>
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
        
        <!-- Import Images Modal -->
        <div id="import-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">Import Images</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Select Category</label>
                        <select class="form-control" id="import-category">
                            {% for category in categories %}
                            <option value="{{ category }}">{{ category|capitalize }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Image Source</label>
                        <div style="margin-top: 10px;">
                            <input type="radio" id="source-computer" name="image-source" checked>
                            <label for="source-computer" style="display: inline; margin-left: 5px;">Computer</label>
                            
                            <input type="radio" id="source-url" name="image-source" style="margin-left: 15px;">
                            <label for="source-url" style="display: inline; margin-left: 5px;">URL</label>
                        </div>
                    </div>
                    
                    <div id="computer-source" class="form-group">
                        <label>Select Images</label>
                        <input type="file" class="form-control" id="image-files" multiple accept="image/*">
                    </div>
                    
                    <div id="url-source" class="form-group" style="display: none;">
                        <label>Image URLs (one per line)</label>
                        <textarea class="form-control" rows="5" id="image-urls" placeholder="https://example.com/image1.jpg&#10;https://example.com/image2.jpg"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>Tags (comma separated)</label>
                        <input type="text" class="form-control" id="import-tags" placeholder="sports, betting, football">
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="secondary-button" id="cancel-import">Cancel</button>
                    <button class="action-button" id="start-import">Import Images</button>
                </div>
            </div>
        </div>
        
        <!-- Change Category Modal -->
        <div id="category-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">Change Category</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Select New Category</label>
                        <select class="form-control" id="new-category">
                            {% for category in categories %}
                            <option value="{{ category }}">{{ category|capitalize }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <p>This will move <span id="category-image-count">3</span> images to the selected category.</p>
                </div>
                <div class="modal-footer">
                    <button class="secondary-button" id="cancel-category">Cancel</button>
                    <button class="action-button" id="apply-category">Apply</button>
                </div>
            </div>
        </div>
        
        <!-- Add Tags Modal -->
        <div id="tags-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">Add Tags</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Tags to Add (comma separated)</label>
                        <input type="text" class="form-control" id="new-tags" placeholder="sports, betting, football">
                    </div>
                    
                    <p>This will add these tags to <span id="tags-image-count">3</span> images.</p>
                </div>
                <div class="modal-footer">
                    <button class="secondary-button" id="cancel-tags">Cancel</button>
                    <button class="action-button" id="apply-tags">Apply Tags</button>
                </div>
            </div>
        </div>
        
        <!-- Delete Confirmation Modal -->
        <div id="delete-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">Confirm Deletion</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <p>Are you sure you want to delete <span id="delete-image-count">3</span> images?</p>
                    <p style="color: #FF5555;">This action cannot be undone.</p>
                </div>
                <div class="modal-footer">
                    <button class="secondary-button" id="cancel-delete">Cancel</button>
                    <button class="action-button danger-action" id="confirm-delete">Delete</button>
                </div>
            </div>
        </div>
        
        <script>
            // Tab switching
            document.querySelectorAll('.tabs .tab').forEach(tab => {
                tab.addEventListener('click', function() {
                    // Update tab styling
                    document.querySelectorAll('.tabs .tab').forEach(t => {
                        t.classList.remove('active');
                    });
                    this.classList.add('active');
                    
                    // Hide all tab content
                    document.querySelectorAll('.tab-content').forEach(content => {
                        content.style.display = 'none';
                    });
                    
                    // Show selected tab content
                    const tabId = this.getAttribute('data-tab');
                    document.getElementById(tabId + '-tab').style.display = 'block';
                });
            });
            
            // Category switching
            document.querySelectorAll('.category-item').forEach(item => {
                item.addEventListener('click', function() {
                    document.querySelectorAll('.category-item').forEach(i => {
                        i.classList.remove('active');
                    });
                    this.classList.add('active');
                    
                    // In a real implementation, you would filter images by the selected category
                    const category = this.getAttribute('data-category');
                    console.log('Selected category:', category);
                    
                    // Here you would make an AJAX call to get images for this category
                    // and update the image grid
                });
            });
            
            // Image selection
            document.querySelectorAll('.select-image').forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    const card = this.closest('.image-card');
                    if (this.checked) {
                        card.classList.add('selected');
                    } else {
                        card.classList.remove('selected');
                    }
                    
                    updateBulkActions();
                });
            });
            
            // Select all button
            document.getElementById('select-all-btn').addEventListener('click', function() {
                const checkboxes = document.querySelectorAll('.select-image');
                const allChecked = Array.from(checkboxes).every(cb => cb.checked);
                
                checkboxes.forEach(cb => {
                    cb.checked = !allChecked;
                    const card = cb.closest('.image-card');
                    if (cb.checked) {
                        card.classList.add('selected');
                    } else {
                        card.classList.remove('selected');
                    }
                });
                
                updateBulkActions();
            });
            
            // Update bulk action buttons based on selection
            function updateBulkActions() {
                const selectedCount = document.querySelectorAll('.select-image:checked').length;
                
                document.getElementById('change-category-btn').disabled = selectedCount === 0;
                document.getElementById('add-tag-btn').disabled = selectedCount === 0;
                document.getElementById('delete-selected-btn').disabled = selectedCount === 0;
            }
            
            // Bulk action buttons
            document.getElementById('change-category-btn').addEventListener('click', function() {
                const selectedCount = document.querySelectorAll('.select-image:checked').length;
                document.getElementById('category-image-count').textContent = selectedCount;
                
                showModal('category-modal');
            });
            
            document.getElementById('add-tag-btn').addEventListener('click', function() {
                const selectedCount = document.querySelectorAll('.select-image:checked').length;
                document.getElementById('tags-image-count').textContent = selectedCount;
                
                showModal('tags-modal');
            });
            
            document.getElementById('delete-selected-btn').addEventListener('click', function() {
                const selectedCount = document.querySelectorAll('.select-image:checked').length;
                document.getElementById('delete-image-count').textContent = selectedCount;
                
                showModal('delete-modal');
            });
            
            // Import button
            document.getElementById('import-images-btn').addEventListener('click', function() {
                showModal('import-modal');
            });
            
            // Import source toggle
            document.getElementById('source-computer').addEventListener('change', function() {
                document.getElementById('computer-source').style.display = 'block';
                document.getElementById('url-source').style.display = 'none';
            });
            
            document.getElementById('source-url').addEventListener('change', function() {
                document.getElementById('computer-source').style.display = 'none';
                document.getElementById('url-source').style.display = 'block';
            });
            
            // Modal functions
            function showModal(modalId) {
                const modal = document.getElementById(modalId);
                modal.style.display = 'flex';
            }
            
            function hideModal(modalId) {
                const modal = document.getElementById(modalId);
                modal.style.display = 'none';
            }
            
            // Close buttons for modals
            document.querySelectorAll('.modal-close').forEach(btn => {
                btn.addEventListener('click', function() {
                    const modal = this.closest('.modal');
                    modal.style.display = 'none';
                });
            });
            
            // Modal cancel buttons
            document.getElementById('cancel-import').addEventListener('click', function() {
                hideModal('import-modal');
            });
            
            document.getElementById('cancel-category').addEventListener('click', function() {
                hideModal('category-modal');
            });
            
            document.getElementById('cancel-tags').addEventListener('click', function() {
                hideModal('tags-modal');
            });
            
            document.getElementById('cancel-delete').addEventListener('click', function() {
                hideModal('delete-modal');
            });
            
            // Modal action buttons
            document.getElementById('start-import').addEventListener('click', function() {
                const category = document.getElementById('import-category').value;
                const sourceType = document.querySelector('input[name="image-source"]:checked').id;
                const tags = document.getElementById('import-tags').value;
                
                // In a real implementation, you would upload the files or fetch the URLs
                if (sourceType === 'source-computer') {
                    const files = document.getElementById('image-files').files;
                    console.log('Importing', files.length, 'files to category:', category, 'with tags:', tags);
                    
                    // Here you would make an AJAX call to upload the files
                    
                    // For demo, just close the modal and show an alert
                    alert(`Importing ${files.length} images to ${category} category`);
                } else {
                    const urls = document.getElementById('image-urls').value.split('\n').filter(url => url.trim());
                    console.log('Importing', urls.length, 'URLs to category:', category, 'with tags:', tags);
                    
                    // Here you would make an AJAX call to fetch the URLs
                    
                    // For demo, just close the modal and show an alert
                    alert(`Importing ${urls.length} images from URLs to ${category} category`);
                }
                
                hideModal('import-modal');
            });
            
            document.getElementById('apply-category').addEventListener('click', function() {
                const newCategory = document.getElementById('new-category').value;
                const selectedImages = document.querySelectorAll('.select-image:checked');
                
                console.log('Changing category of', selectedImages.length, 'images to:', newCategory);
                
                // Here you would make an AJAX call to change the category
                
                // For demo, just close the modal and show an alert
                alert(`Changed category of ${selectedImages.length} images to ${newCategory}`);
                
                hideModal('category-modal');
            });
            
            document.getElementById('apply-tags').addEventListener('click', function() {
                const newTags = document.getElementById('new-tags').value;
                const selectedImages = document.querySelectorAll('.select-image:checked');
                
                console.log('Adding tags to', selectedImages.length, 'images:', newTags);
                
                // Here you would make an AJAX call to add the tags
                
                // For demo, just close the modal and show an alert
                alert(`Added tags "${newTags}" to ${selectedImages.length} images`);
                
                hideModal('tags-modal');
            });
            
            document.getElementById('confirm-delete').addEventListener('click', function() {
                const selectedImages = document.querySelectorAll('.select-image:checked');
                
                console.log('Deleting', selectedImages.length, 'images');
                
                // Here you would make an AJAX call to delete the images
                
                // For demo, just remove the selected images from the DOM
                selectedImages.forEach(checkbox => {
                    const card = checkbox.closest('.image-card');
                    card.remove();
                });
                
                hideModal('delete-modal');
                updateBulkActions();
            });
            
            // Image cards click to view details
            document.querySelectorAll('.image-card').forEach(card => {
                card.addEventListener('click', function(e) {
                    // Don't trigger when clicking the checkbox
                    if (e.target.tagName === 'INPUT' || e.target.closest('.image-checkbox')) {
                        return;
                    }
                    
                    // In a real implementation, you would load the image details
                    console.log('Viewing image details');
                    
                    // Switch to details tab
                    document.querySelector('.tab[data-tab="details"]').click();
                });
            });
            
            // Drag and drop for image upload
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
                    // Filter only image files
                    const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
                    
                    if (imageFiles.length > 0) {
                        console.log('Dropped', imageFiles.length, 'image files');
                        
                        // Show import modal with files pre-loaded
                        showModal('import-modal');
                        
                        // In a real implementation, you would handle the file upload
                        // For demo, just show an alert
                        alert(`Ready to import ${imageFiles.length} images`);
                    }
                }
            });
            
            // Tag cloud item click
            document.querySelectorAll('.tag-cloud-item').forEach(item => {
                item.addEventListener('click', function() {
                    this.classList.toggle('active');
                    
                    // In a real implementation, you would filter images by the selected tags
                    // and update the image grid
                });
            });
        </script>
    </body>
    </html>
    ''', logo_exists=logo_exists, image_counts=image_counts, categories=categories)