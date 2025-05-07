"""
Dashboard Filters and Account Management for TextNow Max

This module handles dashboard filters, account adding/editing and 
implements the individual account messaging system.
"""

import os
import json
import sqlite3
import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, Blueprint

# Import from our modules
from data_manager import get_data_manager

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/add-account', methods=['GET', 'POST'])
def add_account_page():
    """Display and handle the add account form"""
    if request.method == 'POST':
        # Process form submission
        account_data = {
            'username': request.form.get('username'),
            'password': request.form.get('password'),
            'phone_number': request.form.get('phone_number'),
            'area_code': request.form.get('area_code'),
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'birth_date': request.form.get('birth_date'),
            'registration_ip': request.form.get('registration_ip'),
            'ip_family': request.form.get('ip_family'),
            'browser_fingerprint': request.form.get('browser_fingerprint'),
            'device_fingerprint': request.form.get('device_fingerprint'),
            'health_score': int(request.form.get('health_score', 100)),
            'status': request.form.get('status', 'active'),
            'notes': request.form.get('notes', '')
        }
        
        # Handle date fields
        created_at = request.form.get('created_at')
        if created_at:
            account_data['created_at'] = created_at
            
        last_login = request.form.get('last_login')
        if last_login:
            account_data['last_login'] = last_login
            
        last_message_sent = request.form.get('last_message_sent')
        if last_message_sent:
            account_data['last_message_sent'] = last_message_sent
        
        # Get the data manager and add the account
        data_manager = get_data_manager()
        success, message, account_id = data_manager.add_account(account_data)
        
        if success:
            # Redirect to account details page
            return redirect(url_for('dashboard.view_account', account_id=account_id))
        else:
            # Re-render the form with error message
            return render_template('add_account.html', error=message, form_data=account_data)
    
    # GET request - display the form
    return render_template('add_account.html')

@dashboard_bp.route('/edit-account/<int:account_id>', methods=['GET', 'POST'])
def edit_account_page(account_id):
    """Display and handle the edit account form"""
    data_manager = get_data_manager()
    
    if request.method == 'POST':
        # Process form submission
        account_data = {
            'username': request.form.get('username'),
            'password': request.form.get('password'),
            'phone_number': request.form.get('phone_number'),
            'area_code': request.form.get('area_code'),
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'birth_date': request.form.get('birth_date'),
            'registration_ip': request.form.get('registration_ip'),
            'ip_family': request.form.get('ip_family'),
            'browser_fingerprint': request.form.get('browser_fingerprint'),
            'device_fingerprint': request.form.get('device_fingerprint'),
            'health_score': int(request.form.get('health_score', 100)),
            'status': request.form.get('status', 'active'),
            'notes': request.form.get('notes', '')
        }
        
        # Handle date fields
        created_at = request.form.get('created_at')
        if created_at:
            account_data['created_at'] = created_at
            
        last_login = request.form.get('last_login')
        if last_login:
            account_data['last_login'] = last_login
            
        last_message_sent = request.form.get('last_message_sent')
        if last_message_sent:
            account_data['last_message_sent'] = last_message_sent
        
        # Update the account
        success, message = data_manager.update_account(account_id, account_data)
        
        if success:
            # Redirect to account details page
            return redirect(url_for('dashboard.view_account', account_id=account_id))
        else:
            # Re-render the form with error message
            account = data_manager.get_account(account_id)
            return render_template('edit_account.html', error=message, account=account)
    
    # GET request - display the form with current data
    account = data_manager.get_account(account_id)
    if not account:
        # Account not found
        return redirect(url_for('dashboard'))
        
    return render_template('edit_account.html', account=account)

@dashboard_bp.route('/view-account/<int:account_id>')
def view_account(account_id):
    """Display account details including messaging capability"""
    data_manager = get_data_manager()
    account = data_manager.get_account(account_id)
    
    if not account:
        # Account not found
        return redirect(url_for('dashboard'))
    
    return render_template('view_account.html', account=account)

@dashboard_bp.route('/send-message/<int:account_id>', methods=['POST'])
def send_message(account_id):
    """Send a message from a specific account via the dashboard"""
    data_manager = get_data_manager()
    
    # Get form data
    to_number = request.form.get('to_number')
    message = request.form.get('message')
    
    # Handle file upload for image/multimedia
    image_path = None
    multimedia_path = None
    
    if 'image' in request.files and request.files['image'].filename:
        image = request.files['image']
        # Save to a temporary location or permanent storage
        image_path = os.path.join('static', 'uploads', 'images', image.filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image.save(image_path)
    
    if 'multimedia' in request.files and request.files['multimedia'].filename:
        multimedia = request.files['multimedia']
        # Save to a temporary location or permanent storage
        multimedia_path = os.path.join('static', 'uploads', 'multimedia', multimedia.filename)
        os.makedirs(os.path.dirname(multimedia_path), exist_ok=True)
        multimedia.save(multimedia_path)
    
    # Send the message
    success, message_result = data_manager.send_message_from_account(
        account_id, to_number, message, image_path, multimedia_path
    )
    
    if success:
        return jsonify({'success': True, 'message': message_result})
    else:
        return jsonify({'success': False, 'error': message_result})

@dashboard_bp.route('/dashboard/filter', methods=['GET', 'POST'])
def filter_accounts():
    """Apply filters to the accounts dashboard"""
    data_manager = get_data_manager()
    
    # Get filter parameters
    filters = {}
    
    # Text filters
    for text_filter in ['username', 'phone_number', 'area_code', 'name', 'email', 'status', 
                       'creation_method', 'registration_ip', 'ip_family']:
        if request.args.get(text_filter):
            filters[text_filter] = request.args.get(text_filter)
    
    # Numeric range filters
    for range_filter in ['health_score', 'usage_count']:
        min_val = request.args.get(f'{range_filter}_min')
        if min_val and min_val.isdigit():
            filters[f'{range_filter}_min'] = int(min_val)
            
        max_val = request.args.get(f'{range_filter}_max')
        if max_val and max_val.isdigit():
            filters[f'{range_filter}_max'] = int(max_val)
    
    # Date range filters
    for date_filter in ['creation_date', 'last_login']:
        start = request.args.get(f'{date_filter}_start')
        if start:
            filters[f'{date_filter}_start'] = start
            
        end = request.args.get(f'{date_filter}_end')
        if end:
            filters[f'{date_filter}_end'] = end
    
    # Pagination
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 50))
    
    # Sorting
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Get filtered accounts
    result = data_manager.get_accounts(filters, page, page_size, sort_by, sort_order)
    
    # Return JSON if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(result)
    
    # Otherwise render the template
    return render_template('dashboard.html', 
                          accounts=result['accounts'], 
                          pagination=result['pagination'],
                          filters=filters,
                          sort_by=sort_by,
                          sort_order=sort_order)

@dashboard_bp.route('/delete-account/<int:account_id>', methods=['POST'])
def delete_account(account_id):
    """Delete an account"""
    data_manager = get_data_manager()
    success, message = data_manager.delete_account(account_id)
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'error': message})

def register_dashboard_blueprint(app):
    """Register the dashboard blueprint with the Flask app"""
    app.register_blueprint(dashboard_bp)