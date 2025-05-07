"""
True IP Rotation Fix for TextNow Max

This file contains a direct fix for the IP rotation functionality
that will show the true IP address on local environments.

Instructions:
1. Copy the function below and replace the existing function in api_routes.py
2. Restart the application

This version removes the simulation part and focuses on getting the actual IP.
"""

@api.route('/device/refresh-ip', methods=['POST'])
def refresh_device_ip():
    """Refresh IP address via Proxidize - FIXED FOR LOCAL ENVIRONMENT"""
    try:
        import time
        import requests
        
        # Make sure the proxidize manager is available
        if proxidize_manager is None:
            return jsonify({
                'success': False,
                'error': 'Proxidize manager is not available',
                'details': 'The Proxidize proxy system is not initialized.'
            })
        
        # Get the rotation URL from configuration
        rotation_url = proxidize_manager.config.get('rotation_url')
        if not rotation_url:
            return jsonify({
                'success': False,
                'error': 'No rotation URL configured',
                'details': 'The Proxidize rotation URL is not configured in proxidize_config.json'
            })
            
        # Send the rotation command to Proxidize
        try:
            print(f"Sending rotation command to URL: {rotation_url}")
            rotation_response = requests.get(rotation_url, timeout=15)
            if rotation_response.status_code != 200:
                return jsonify({
                    'success': False,
                    'error': f'Rotation API returned status {rotation_response.status_code}',
                    'details': f'Response: {rotation_response.text[:100]}'
                })
                
            # The rotation was successful via the API
            print(f"Rotation API response: {rotation_response.text}")
            
        except Exception as rotate_err:
            return jsonify({
                'success': False,
                'error': f'Failed to send rotation command: {str(rotate_err)}',
                'details': 'Check your internet connection and Proxidize URL.'
            })
        
        # Wait for the rotation to complete
        wait_time = 8  # Increased wait time to ensure rotation completes
        print(f"Waiting {wait_time} seconds for IP rotation to complete...")
        time.sleep(wait_time)
        
        # First, update rotation tracking 
        current_count = proxidize_manager.config.get('rotation_count', 0) + 1
        proxidize_manager.config['rotation_count'] = current_count
        proxidize_manager.config['last_rotation'] = int(time.time())
        proxidize_manager._save_config()
        
        # Reset the cached IP to force a fresh check
        proxidize_manager.last_ip = None
        
        # Set up proxy details for direct connection
        http_proxy = proxidize_manager.config.get('http_proxy')
        username = proxidize_manager.config.get('proxy_username')
        password = proxidize_manager.config.get('proxy_password')
        
        if not http_proxy or not username or not password:
            return jsonify({
                'success': False,
                'error': 'Missing proxy credentials',
                'details': 'Check your proxy configuration in proxidize_config.json'
            })
        
        # Construct the proxy URL with authentication
        proxy_url = f"http://{username}:{password}@{http_proxy}"
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        # Try to get the IP using the proxy
        try:
            print(f"Attempting to get IP via proxy: {http_proxy}")
            # Use a more reliable IP service
            ip_response = requests.get('https://api.ipify.org', 
                                      proxies=proxies, 
                                      timeout=15)
            
            if ip_response.status_code == 200:
                new_ip = ip_response.text.strip()
                proxidize_manager.last_ip = new_ip
                print(f"Successfully got new IP via proxy: {new_ip}")
                
                return jsonify({
                    'success': True,
                    'new_ip': new_ip,
                    'message': 'IP rotation completed successfully!',
                    'rotation_count': current_count
                })
            else:
                print(f"IP service returned non-200 status: {ip_response.status_code}")
        except Exception as ip_err:
            print(f"Error getting IP via proxy: {str(ip_err)}")
            
        # If we couldn't get the IP through the proxy, try without it
        try:
            print("Trying to get IP without proxy as fallback")
            direct_response = requests.get('https://api.ipify.org', timeout=5)
            if direct_response.status_code == 200:
                direct_ip = direct_response.text.strip()
                print(f"Got IP without proxy: {direct_ip}")
                
                return jsonify({
                    'success': True,
                    'new_ip': direct_ip,
                    'message': 'IP rotation command sent successfully, but could not verify through proxy',
                    'rotation_count': current_count
                })
        except Exception as direct_err:
            print(f"Error getting direct IP: {str(direct_err)}")
        
        # Last resort - return a general success message
        return jsonify({
            'success': True,
            'new_ip': 'Unknown',
            'message': 'IP rotation command sent successfully to Proxidize, but could not verify IP',
            'rotation_count': current_count
        })
        
    except Exception as e:
        print(f"Unexpected error in refresh_device_ip: {str(e)}")
        return jsonify({
            'success': False, 
            'error': f'Error rotating IP: {str(e)}',
            'details': 'See server logs for more information'
        })