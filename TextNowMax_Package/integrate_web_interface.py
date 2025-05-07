"""
Integration script for TextNow Max Creator web interface

This script integrates the real account creation and management functionality
with the existing web interface.
"""

import os
import time
import logging
import threading
from flask import Flask, jsonify, request, render_template

# Import the TextNow integration module
from textnow_integration import get_integrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("web_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WebIntegration")

# Get the integrator instance
integrator = get_integrator()

def add_api_routes(app):
    """Add real API routes to the Flask app"""
    
    @app.route('/api/real/create_accounts', methods=['POST'])
    def handle_create_accounts():
        """Handle account creation request"""
        try:
            data = request.json
            count = int(data.get('count', 1))
            area_codes = data.get('area_codes', '')
            
            # Parse area codes
            if isinstance(area_codes, list) and area_codes:
                area_code = area_codes[0]
            elif isinstance(area_codes, str) and area_codes:
                area_code = area_codes.split(',')[0].strip()
            else:
                area_code = None
            
            logger.info(f"Creating {count} accounts with area code {area_code}")
            
            # Start account creation in background
            def creation_thread():
                result = integrator.create_multiple_accounts(count, area_code)
                logger.info(f"Account creation completed: {result}")
            
            thread = threading.Thread(target=creation_thread)
            thread.daemon = True
            thread.start()
            
            return jsonify({
                "success": True,
                "message": f"Started creating {count} accounts with area code {area_code}"
            })
        except Exception as e:
            logger.error(f"Error creating accounts: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            })
    
    @app.route('/api/real/accounts', methods=['GET'])
    def handle_get_accounts():
        """Get all accounts from the database"""
        try:
            status = request.args.get('status')
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))
            
            accounts = integrator.get_all_accounts(status, limit, offset)
            
            return jsonify({
                "success": True,
                "accounts": accounts,
                "count": len(accounts)
            })
        except Exception as e:
            logger.error(f"Error getting accounts: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            })
    
    @app.route('/api/real/accounts/<int:account_id>', methods=['GET'])
    def handle_get_account(account_id):
        """Get account details by ID"""
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
            logger.error(f"Error getting account: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            })
    
    @app.route('/api/real/send_message', methods=['POST'])
    def handle_send_message():
        """Send a message from an account"""
        try:
            data = request.json
            account_id = data.get('account_id')
            recipient = data.get('recipient')
            message = data.get('message')
            
            if not all([account_id, recipient, message]):
                return jsonify({
                    "success": False,
                    "error": "Missing required parameters"
                })
            
            # Start message sending in background
            def send_thread():
                result = integrator.send_message(account_id, recipient, message)
                logger.info(f"Message sending completed: {result}")
            
            thread = threading.Thread(target=send_thread)
            thread.daemon = True
            thread.start()
            
            return jsonify({
                "success": True,
                "message": f"Started sending message to {recipient}"
            })
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            })
    
    @app.route('/api/real/rotate_ip', methods=['POST'])
    def handle_rotate_ip():
        """Rotate the IP address"""
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
            logger.error(f"Error rotating IP: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            })
    
    logger.info("Real API routes added to Flask app")
    return app

def modify_frontend_js(app_dir='.'):
    """Modify the frontend JavaScript to use the real API endpoints"""
    try:
        # Find the static folder
        static_dir = os.path.join(app_dir, 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        
        # Create or update the integration.js file
        js_file = os.path.join(static_dir, 'integration.js')
        
        with open(js_file, 'w') as f:
            f.write("""
// TextNow Max Creator - Real API Integration

// Override the demo API calls with real functionality
window.realAPI = {
    createAccounts: function(count, areaCodes) {
        return fetch('/api/real/create_accounts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ count, area_codes: areaCodes })
        }).then(response => response.json());
    },
    
    getAccounts: function(status, limit, offset) {
        let url = '/api/real/accounts';
        let params = new URLSearchParams();
        
        if (status) params.append('status', status);
        if (limit) params.append('limit', limit);
        if (offset) params.append('offset', offset);
        
        if (params.toString()) url += '?' + params.toString();
        
        return fetch(url).then(response => response.json());
    },
    
    getAccount: function(accountId) {
        return fetch(`/api/real/accounts/${accountId}`).then(response => response.json());
    },
    
    sendMessage: function(accountId, recipient, message) {
        return fetch('/api/real/send_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ account_id: accountId, recipient, message })
        }).then(response => response.json());
    },
    
    rotateIP: function() {
        return fetch('/api/real/rotate_ip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        }).then(response => response.json());
    }
};

// Hook into the UI to replace demo functionality with real API calls
document.addEventListener('DOMContentLoaded', function() {
    console.log('TextNow Max Creator - Real API Integration Loaded');
    
    // Replace account creation form submit
    const accountForm = document.querySelector('form[action*="create"]');
    if (accountForm) {
        accountForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const countInput = this.querySelector('input[name="count"]');
            const areaCodesInput = this.querySelector('input[name="area_codes"]');
            
            const count = countInput ? parseInt(countInput.value) : 1;
            const areaCodes = areaCodesInput ? areaCodesInput.value : '';
            
            console.log(`Creating ${count} accounts with area codes: ${areaCodes}`);
            
            window.realAPI.createAccounts(count, areaCodes)
                .then(result => {
                    if (result.success) {
                        alert('Account creation started! Check the logs for progress.');
                    } else {
                        alert('Error: ' + result.error);
                    }
                })
                .catch(err => {
                    console.error('Error creating accounts:', err);
                    alert('Error creating accounts. Check the console for details.');
                });
        });
    }
    
    // Replace IP rotation button
    const rotateIpButton = document.querySelector('button[onclick*="rotate"]');
    if (rotateIpButton) {
        rotateIpButton.onclick = function(e) {
            e.preventDefault();
            
            console.log('Rotating IP address...');
            
            window.realAPI.rotateIP()
                .then(result => {
                    if (result.success) {
                        alert(`IP rotated successfully! Old: ${result.old_ip}, New: ${result.new_ip}`);
                    } else {
                        alert('Error: ' + result.error);
                    }
                })
                .catch(err => {
                    console.error('Error rotating IP:', err);
                    alert('Error rotating IP. Check the console for details.');
                });
        };
    }
});
""")
        
        # Add the script tag to the templates
        templates_dir = os.path.join(app_dir, 'templates')
        if os.path.exists(templates_dir):
            # Look for HTML files in templates folder
            for filename in os.listdir(templates_dir):
                if filename.endswith('.html'):
                    file_path = os.path.join(templates_dir, filename)
                    
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Add the integration.js script if not already present
                    if '</body>' in content and 'integration.js' not in content:
                        new_content = content.replace(
                            '</body>',
                            '<script src="/static/integration.js"></script>\n</body>'
                        )
                        
                        with open(file_path, 'w') as f:
                            f.write(new_content)
        
        logger.info("Frontend integration JS created and added to templates")
        return True
    except Exception as e:
        logger.error(f"Error modifying frontend: {str(e)}")
        return False

def integrate_with_app(app):
    """Integrate the real functionality with the Flask app"""
    # Add real API routes
    app = add_api_routes(app)
    
    # Modify frontend JS
    modify_frontend_js()
    
    return app

if __name__ == "__main__":
    # Create a simple Flask app for testing
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    app = integrate_with_app(app)
    
    app.run(host='0.0.0.0', port=5000, debug=True)