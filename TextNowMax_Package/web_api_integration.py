"""
Web API Integration for TextNow Max

This module connects the real TextNow automation backend with the web API routes
in fixed_clickable_original.py.
"""

import os
import json
import logging
import asyncio
import threading
import time
from flask import jsonify, request

# Import the TextNow integration module
from textnow_integration import get_integrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("web_api_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WebAPIIntegration")

# Get the integrator instance
integrator = get_integrator()

def handle_create_accounts():
    """Handle the account creation API request"""
    try:
        # Get parameters from request
        data = request.json
        count = int(data.get('count', 1))
        area_codes = data.get('area_codes', '')
        
        # Extract first area code if multiple are provided
        if isinstance(area_codes, list) and area_codes:
            area_code = area_codes[0]
        elif isinstance(area_codes, str) and area_codes:
            area_code = area_codes.split(',')[0].strip()
        else:
            area_code = None
        
        # Start account creation in background
        def callback(result):
            logger.info(f"Account creation completed: {result['successful']} successful, {result['failed']} failed")
        
        result = integrator.create_accounts_background(count, area_code, callback)
        
        return jsonify({
            "success": True,
            "message": f"Started creating {count} accounts with area code {area_code}",
            "task_id": time.time()  # Use timestamp as task ID
        })
    except Exception as e:
        logger.error(f"Error handling create accounts request: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

def handle_get_accounts():
    """Handle the get accounts API request"""
    try:
        # Get parameters from request
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Get accounts from database
        accounts = integrator.get_all_accounts(status, limit, offset)
        
        return jsonify({
            "success": True,
            "accounts": accounts,
            "count": len(accounts)
        })
    except Exception as e:
        logger.error(f"Error handling get accounts request: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

def handle_get_account(account_id):
    """Handle the get single account API request"""
    try:
        account = integrator.get_account(account_id=account_id)
        
        if account:
            return jsonify({
                "success": True,
                "account": account
            })
        else:
            return jsonify({
                "success": False,
                "error": "Account not found"
            })
    except Exception as e:
        logger.error(f"Error handling get account request: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

def handle_delete_account(account_id):
    """Handle the delete account API request"""
    try:
        # For now, just update the account status to 'deleted'
        # Actual deletion is usually not recommended for audit purposes
        success = integrator.db.update_account(account_id, status="deleted")
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Account {account_id} marked as deleted"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Account not found or could not be deleted"
            })
    except Exception as e:
        logger.error(f"Error handling delete account request: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

def handle_send_message():
    """Handle the send message API request"""
    try:
        # Get parameters from request
        data = request.json
        account_id = data.get('account_id')
        recipient = data.get('recipient')
        message = data.get('message')
        
        if not all([account_id, recipient, message]):
            return jsonify({
                "success": False,
                "error": "Missing required parameters: account_id, recipient, message"
            })
        
        # Send message in background thread to avoid blocking
        def send_in_background():
            result = integrator.send_message(account_id, recipient, message)
            logger.info(f"Message sent result: {result}")
        
        thread = threading.Thread(target=send_in_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "message": f"Started sending message to {recipient}",
            "task_id": time.time()  # Use timestamp as task ID
        })
    except Exception as e:
        logger.error(f"Error handling send message request: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

def handle_rotate_ip():
    """Handle the rotate IP API request"""
    try:
        old_ip = integrator.get_current_ip()
        success = integrator.rotate_ip()
        new_ip = integrator.get_current_ip()
        
        return jsonify({
            "success": success,
            "old_ip": old_ip,
            "new_ip": new_ip,
            "changed": old_ip != new_ip
        })
    except Exception as e:
        logger.error(f"Error handling rotate IP request: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

def handle_check_ip():
    """Handle the check current IP API request"""
    try:
        ip = integrator.get_current_ip()
        
        return jsonify({
            "success": True,
            "ip": ip
        })
    except Exception as e:
        logger.error(f"Error handling check IP request: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

def handle_get_stats():
    """Handle the get stats API request"""
    try:
        # Get account statistics
        total_accounts = len(integrator.get_all_accounts(limit=1000000))
        active_accounts = len(integrator.get_all_accounts(status="active", limit=1000000))
        blocked_accounts = len(integrator.get_all_accounts(status="blocked", limit=1000000))
        
        # Get recent accounts
        recent_accounts = integrator.get_all_accounts(limit=10)
        
        return jsonify({
            "success": True,
            "stats": {
                "total_accounts": total_accounts,
                "active_accounts": active_accounts,
                "blocked_accounts": blocked_accounts,
                "recent_accounts": recent_accounts
            }
        })
    except Exception as e:
        logger.error(f"Error handling get stats request: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

def register_api_routes(app):
    """Register API routes with the Flask app"""
    # Account creation
    app.route('/api/accounts/create', methods=['POST'])(handle_create_accounts)
    
    # Account retrieval
    app.route('/api/accounts', methods=['GET'])(handle_get_accounts)
    app.route('/api/accounts/<int:account_id>', methods=['GET'])(handle_get_account)
    
    # Account deletion
    app.route('/api/accounts/<int:account_id>', methods=['DELETE'])(handle_delete_account)
    
    # Messaging
    app.route('/api/messages/send', methods=['POST'])(handle_send_message)
    
    # IP management
    app.route('/api/proxy/rotate', methods=['POST'])(handle_rotate_ip)
    app.route('/api/proxy/check', methods=['GET'])(handle_check_ip)
    
    # Stats
    app.route('/api/stats', methods=['GET'])(handle_get_stats)
    
    logger.info("API routes registered")
    
    return app