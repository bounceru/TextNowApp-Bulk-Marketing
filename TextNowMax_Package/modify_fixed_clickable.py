"""
Modify Fixed Clickable script to integrate real functionality

This script adds the integration JavaScript to the fixed_clickable_original.py
Flask application, enabling real account creation and management.
"""

import os
import re
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('integration.log')
    ]
)
logger = logging.getLogger('Integrator')

def add_real_api_routes():
    """Add the real API routes to fixed_clickable_original.py"""
    try:
        # Read the fixed_clickable_original.py file
        with open('fixed_clickable_original.py', 'r') as f:
            content = f.read()
        
        # Import the integration module at the top
        import_section = "import os\nimport time\nimport random\nimport logging\nimport json\nfrom flask import Flask, render_template, jsonify, request, redirect, url_for\n\n"
        new_import = "# Import the real API integration\nfrom integrate_web_interface import integrate_with_app\n\n"
        
        if new_import not in content:
            content = content.replace(import_section, import_section + new_import)
        
        # Add integration after app creation
        app_creation = "app = Flask(__name__)\n"
        integration_code = "# Integrate real API functionality\napp = integrate_with_app(app)\n\n"
        
        if integration_code not in content:
            content = content.replace(app_creation, app_creation + integration_code)
        
        # Write the modified content back
        with open('fixed_clickable_original.py', 'w') as f:
            f.write(content)
        
        logger.info("Successfully added real API routes to fixed_clickable_original.py")
        return True
    except Exception as e:
        logger.error(f"Error adding real API routes: {str(e)}")
        return False

def modify_templates():
    """Modify the HTML templates to include the real_integration.js script"""
    try:
        templates_dir = 'templates'
        if not os.path.exists(templates_dir):
            logger.error(f"Templates directory not found: {templates_dir}")
            return False
        
        # Find all HTML files in the templates directory
        html_files = [f for f in os.listdir(templates_dir) if f.endswith('.html')]
        
        for filename in html_files:
            file_path = os.path.join(templates_dir, filename)
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check if the script tag is already there
            if '<script src="/static/real_integration.js"></script>' not in content:
                # Add the script tag before the closing body tag
                if '</body>' in content:
                    modified_content = content.replace(
                        '</body>',
                        '  <script src="/static/real_integration.js"></script>\n  </body>'
                    )
                    
                    with open(file_path, 'w') as f:
                        f.write(modified_content)
                    
                    logger.info(f"Added real integration script to {filename}")
        
        return True
    except Exception as e:
        logger.error(f"Error modifying templates: {str(e)}")
        return False

def add_data_attributes():
    """Add data attributes to buttons for real functionality"""
    try:
        templates_dir = 'templates'
        
        # Look for the creator.html template
        creator_path = os.path.join(templates_dir, 'creator.html')
        if os.path.exists(creator_path):
            with open(creator_path, 'r') as f:
                content = f.read()
            
            # Add ID to start button
            if 'id="start-creation-btn"' not in content:
                content = re.sub(
                    r'<button[^>]*>Start Creation</button>',
                    '<button id="start-creation-btn" class="btn btn-primary">Start Creation</button>',
                    content
                )
            
            # Add creation status div
            if 'id="creation-status"' not in content:
                status_div = '<div id="creation-status" class="alert alert-info mt-3" style="display: none;"></div>'
                content = re.sub(
                    r'</form>',
                    f'</form>\n        {status_div}',
                    content
                )
            
            with open(creator_path, 'w') as f:
                f.write(content)
            
            logger.info("Added data attributes to creator.html")
        
        # Look for device status page
        device_status_pages = [
            os.path.join(templates_dir, 'device.html'),
            os.path.join(templates_dir, 'device_status.html'),
            os.path.join(templates_dir, 'proxy.html')
        ]
        
        for path in device_status_pages:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    content = f.read()
                
                # Add ID to rotate button
                if 'id="rotate-ip-btn"' not in content:
                    content = re.sub(
                        r'<button[^>]*>Rotate IP</button>',
                        '<button id="rotate-ip-btn" class="btn btn-warning">Rotate IP</button>',
                        content
                    )
                    
                    # Add status span
                    if 'id="ip-status"' not in content:
                        content = re.sub(
                            r'<h2>Device Status</h2>',
                            '<h2>Device Status <span id="ip-status" class="badge badge-info"></span></h2>',
                            content
                        )
                    
                    with open(path, 'w') as f:
                        f.write(content)
                    
                    logger.info(f"Added data attributes to {os.path.basename(path)}")
        
        return True
    except Exception as e:
        logger.error(f"Error adding data attributes: {str(e)}")
        return False

def check_static_directory():
    """Ensure the static directory exists"""
    static_dir = 'static'
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        logger.info(f"Created static directory: {static_dir}")
    return True

def main():
    """Main function to modify the application"""
    logger.info("Starting integration of real functionality")
    
    # Check static directory
    check_static_directory()
    
    # Add real API routes
    add_real_api_routes()
    
    # Modify templates
    modify_templates()
    
    # Add data attributes to buttons
    add_data_attributes()
    
    logger.info("Integration complete. Restart the application to apply changes.")

if __name__ == "__main__":
    main()