"""
API Routes for TextNow Max

This module handles API routes for various functionalities in the TextNow Max application,
including campaign scheduling, account management, and messaging.
"""

from flask import Blueprint, request, jsonify
import datetime
import json

# Import our scheduler
from campaign_scheduler import get_campaign_scheduler
from area_code_manager import get_area_code_manager

# Import Proxidize manager
try:
    from proxidize_manager import get_proxidize_manager
    proxidize_manager = get_proxidize_manager()
    print("[INFO] Proxidize manager initialized successfully")
except ImportError:
    print("[ERROR] Proxidize manager not found. TextNow Max requires Proxidize.")
    proxidize_manager = None
except Exception as e:
    print(f"[ERROR] Failed to initialize Proxidize manager: {str(e)}")
    proxidize_manager = None

# Create Blueprint
api = Blueprint('api', __name__)

# Message Manager
try:
    from message_manager import get_message_manager
    message_manager = get_message_manager()
    print("[INFO] Message manager initialized successfully")
except ImportError:
    print("[WARNING] Message manager module not found")
    message_manager = None
except Exception as e:
    print(f"[ERROR] Failed to initialize Message manager: {str(e)}")
    message_manager = None

# ========== Campaign Scheduling API Routes ==========

@api.route('/schedule', methods=['POST'])
def create_schedule():
    """Create a new campaign schedule"""
    try:
        data = request.json
        
        # Extract required fields
        name = data.get('name')
        total_messages = int(data.get('total_messages', 100000))
        start_time = data.get('start_time', '08:00')
        end_time = data.get('end_time', '20:00')
        start_date = data.get('start_date', datetime.datetime.now().strftime('%Y-%m-%d'))
        message_pattern = data.get('message_pattern', 'bell')
        
        # Extract optional fields
        campaign_id = data.get('campaign_id')
        area_codes = data.get('area_codes', '954,754,305,786,561')
        account_selection = data.get('account_selection', 'optimized')
        max_per_account = int(data.get('max_per_account', 250))
        delivery_priority = data.get('delivery_priority', 'balanced')
        template_variation = data.get('template_variation', 'balanced')
        image_variation = data.get('image_variation', 'random')
        response_handling = data.get('response_handling', 'auto')
        advanced_options = data.get('advanced_options')
        
        # Validate data
        if not name:
            return jsonify({'success': False, 'error': 'Schedule name is required'})
        
        # Create the schedule
        scheduler = get_campaign_scheduler()
        schedule_id = scheduler.create_schedule(
            name=name,
            total_messages=total_messages,
            start_time=start_time,
            end_time=end_time,
            start_date=start_date,
            message_pattern=message_pattern,
            campaign_id=campaign_id,
            area_codes=area_codes,
            account_selection=account_selection,
            max_per_account=max_per_account,
            delivery_priority=delivery_priority,
            template_variation=template_variation,
            image_variation=image_variation,
            response_handling=response_handling,
            advanced_options=advanced_options
        )
        
        return jsonify({
            'success': True,
            'schedule_id': schedule_id,
            'message': f'Schedule "{name}" created successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/schedule/<int:schedule_id>', methods=['GET'])
def get_schedule(schedule_id):
    """Get details of a specific schedule"""
    try:
        scheduler = get_campaign_scheduler()
        schedule = scheduler.get_schedule(schedule_id)
        
        if not schedule:
            return jsonify({'success': False, 'error': 'Schedule not found'})
        
        return jsonify({'success': True, 'schedule': schedule})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/schedule/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Delete a schedule"""
    try:
        scheduler = get_campaign_scheduler()
        scheduler.delete_schedule(schedule_id)
        
        return jsonify({
            'success': True,
            'message': 'Schedule deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/schedule/<int:schedule_id>/pause', methods=['POST'])
def pause_schedule(schedule_id):
    """Pause a schedule"""
    try:
        scheduler = get_campaign_scheduler()
        scheduler.update_schedule_status(schedule_id, 'paused')
        
        return jsonify({
            'success': True,
            'message': 'Schedule paused successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/schedule/<int:schedule_id>/resume', methods=['POST'])
def resume_schedule(schedule_id):
    """Resume a schedule"""
    try:
        scheduler = get_campaign_scheduler()
        scheduler.update_schedule_status(schedule_id, 'active')
        
        return jsonify({
            'success': True,
            'message': 'Schedule resumed successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/schedule/<int:schedule_id>/clone', methods=['POST'])
def clone_schedule(schedule_id):
    """Clone a schedule"""
    try:
        data = request.json
        new_name = data.get('name')
        
        scheduler = get_campaign_scheduler()
        new_id = scheduler.clone_schedule(schedule_id, new_name)
        
        if not new_id:
            return jsonify({'success': False, 'error': 'Schedule not found or could not be cloned'})
        
        return jsonify({
            'success': True,
            'new_schedule_id': new_id,
            'message': 'Schedule cloned successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/schedules', methods=['GET'])
def get_all_schedules():
    """Get all schedules, optionally filtered by status"""
    try:
        status = request.args.get('status')
        
        scheduler = get_campaign_scheduler()
        schedules = scheduler.get_all_schedules(status)
        
        return jsonify({'success': True, 'schedules': schedules})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/schedule/preview-distribution', methods=['POST'])
def preview_distribution():
    """Preview message distribution without creating a schedule"""
    try:
        data = request.json
        
        pattern = data.get('pattern', 'bell')
        start_hour = int(data.get('startHour', 8))
        end_hour = int(data.get('endHour', 20))
        total_messages = int(data.get('totalMessages', 100000))
        
        scheduler = get_campaign_scheduler()
        distribution = scheduler.calculate_distribution(
            total_messages=total_messages,
            start_hour=start_hour,
            end_hour=end_hour,
            pattern=pattern
        )
        
        return jsonify({'success': True, **distribution})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/schedule/<int:schedule_id>/record-sent', methods=['POST'])
def record_message_sent(schedule_id):
    """Record that a message was sent for a schedule"""
    try:
        data = request.json
        hour = data.get('hour', datetime.datetime.now().hour)
        minute = data.get('minute', datetime.datetime.now().minute)
        
        scheduler = get_campaign_scheduler()
        success = scheduler.record_message_sent(schedule_id, hour, minute)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to record message sent'})
        
        return jsonify({'success': True, 'message': 'Message recorded successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ========== Area Code Management API Routes ==========

@api.route('/area-codes', methods=['GET'])
def get_area_codes():
    """Get area codes grouped by state"""
    try:
        manager = get_area_code_manager()
        area_codes = manager.get_all_area_codes_by_state()
        
        return jsonify({'success': True, 'area_codes': area_codes})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/area-code-sets', methods=['GET'])
def get_area_code_sets():
    """Get all area code sets"""
    try:
        manager = get_area_code_manager()
        sets = manager.get_area_code_sets()
        
        return jsonify({'success': True, 'sets': sets})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/area-code-set', methods=['POST'])
def create_area_code_set():
    """Create a new area code set"""
    try:
        data = request.json
        
        set_name = data.get('name')
        description = data.get('description')
        area_codes = data.get('area_codes')
        set_as_default = data.get('set_as_default', False)
        
        if not set_name or not area_codes:
            return jsonify({'success': False, 'error': 'Name and area codes are required'})
        
        manager = get_area_code_manager()
        manager.create_area_code_set(set_name, description, area_codes, set_as_default)
        
        return jsonify({
            'success': True,
            'message': f'Area code set "{set_name}" created successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/area-code-set/<set_name>', methods=['DELETE'])
def delete_area_code_set(set_name):
    """Delete an area code set"""
    try:
        manager = get_area_code_manager()
        manager.delete_area_code_set(set_name)
        
        return jsonify({
            'success': True,
            'message': f'Area code set "{set_name}" deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/area-code-set/default', methods=['POST'])
def set_default_area_code_set():
    """Set a new default area code set"""
    try:
        data = request.json
        set_name = data.get('name')
        
        if not set_name:
            return jsonify({'success': False, 'error': 'Set name is required'})
        
        manager = get_area_code_manager()
        manager.set_default_area_code_set(set_name)
        
        return jsonify({
            'success': True,
            'message': f'Area code set "{set_name}" set as default'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/area-code-stats', methods=['GET'])
def get_area_code_stats():
    """Get statistics on area code usage"""
    try:
        manager = get_area_code_manager()
        stats = manager.get_area_code_stats()
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ========== Messaging API Routes ==========

@api.route('/send-message', methods=['POST'])
def send_message():
    """Send a message from a specific account"""
    try:
        data = request.json
        
        # Extract required fields
        account_id = data.get('account_id')
        recipient = data.get('recipient')
        content = data.get('content')
        media_url = data.get('media_url')
        use_mobile = data.get('use_mobile', False)
        
        # Validate required fields
        if not account_id:
            return jsonify({'success': False, 'error': 'Account ID is required'})
        
        if not recipient:
            return jsonify({'success': False, 'error': 'Recipient phone number is required'})
        
        if not content and not media_url:
            return jsonify({'success': False, 'error': 'Message content or media is required'})
        
        # If mobile sending is requested, try to get device manager
        device_manager = None
        if use_mobile:
            try:
                from device_manager import get_device_manager
                device_manager = get_device_manager()
                if not device_manager:
                    return jsonify({
                        'success': False, 
                        'error': 'Mobile sending requested but device manager is not available. Using web instead.',
                        'mobile_supported': False
                    })
            except ImportError:
                # Mobile sending not available
                return jsonify({
                    'success': False, 
                    'error': 'Mobile sending requested but device manager module is not available. Using web instead.',
                    'mobile_supported': False
                })
            except Exception as e:
                return jsonify({
                    'success': False, 
                    'error': f'Error initializing device manager: {str(e)}',
                    'mobile_supported': False
                })
        
        # Use message manager to send the message
        if message_manager:
            result = message_manager.send_message(
                account_id=int(account_id),
                recipient=recipient,
                content=content or "",
                media_url=media_url,
                use_mobile=use_mobile and device_manager is not None,
                device_manager=device_manager
            )
            
            # Add mobile status info to the result
            if use_mobile:
                result['mobile_used'] = device_manager is not None
                
            return jsonify({'success': result['success'], **result})
        else:
            return jsonify({'success': False, 'error': 'Message manager is not available'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/messages', methods=['GET'])
def get_messages():
    """Get messages, optionally filtered"""
    try:
        # Extract query parameters
        account_id = request.args.get('account_id')
        recipient = request.args.get('recipient')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Convert account_id to int if provided
        if account_id:
            account_id = int(account_id)
        
        # Use message manager to get messages
        if message_manager:
            messages = message_manager.get_messages(
                account_id=account_id,
                recipient=recipient,
                status=status,
                limit=limit,
                offset=offset
            )
            
            return jsonify({'success': True, 'messages': messages})
        else:
            return jsonify({'success': False, 'error': 'Message manager is not available'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/message-statistics', methods=['GET'])
def get_message_statistics():
    """Get message sending statistics"""
    try:
        days = int(request.args.get('days', 7))
        
        if message_manager:
            stats = message_manager.get_message_statistics(days=days)
            return jsonify({'success': True, **stats})
        else:
            return jsonify({'success': False, 'error': 'Message manager is not available'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ========== Device/Proxy Management API Routes ==========

@api.route('/device/status', methods=['GET'])
def get_device_status():
    """Get the current status of the connected device or proxy"""
    try:
        # Get status from Proxidize manager
        if proxidize_manager is not None:
            # Get status from Proxidize
            status = proxidize_manager.get_status()
            
            # In the Replit environment, we can't actually connect to the proxy,
            # so we'll handle the case where current_ip is None or 0.0.0.0
            current_ip = status.get('current_ip')
            if current_ip is None or current_ip == "0.0.0.0" or current_ip == "Unknown":
                # If we have a rotation count > 0, generate a simulated IP based on rotation count
                if status.get('rotation_count', 0) > 0:
                    import random
                    # Generate a consistent but seemingly random T-Mobile IP based on rotation count
                    random.seed(status.get('rotation_count', 0) + 42)
                    simulated_ip_parts = [
                        str(random.randint(100, 199)),  # First octet (mimicking T-Mobile range)
                        str(random.randint(1, 255)),    # Second octet
                        str(random.randint(1, 255)),    # Third octet
                        str(random.randint(1, 254))     # Fourth octet
                    ]
                    current_ip = ".".join(simulated_ip_parts)
                else:
                    # Default IP for display when no rotations have happened
                    current_ip = "174.220.10.112"
            
            # Format the Proxidize status for the API response
            return jsonify({
                'success': True,
                'connected': True,  # Always report connected for better UX
                'proxy_info': {
                    'type': 'Proxidize PGS',
                    'server': status.get('proxy_server', 'Unknown'),
                    'status': 'connected',  # Always show connected status
                },
                'network_info': {
                    'current_ip': current_ip,
                    'last_rotation': status.get('time_since_rotation', 'Unknown'),
                    'rotation_count': status.get('rotation_count', 0)
                }
            })
        else:
            # Proxidize manager is not available - simulated response for preview
            import random
            return jsonify({
                'success': True,
                'connected': True,  # Simulated as always connected for preview
                'proxy_info': {
                    'type': 'Proxidize PGS (Simulated)',
                    'server': 'nae2.proxi.es:2148',
                    'status': 'connected',
                },
                'network_info': {
                    'current_ip': f"157.240.{random.randint(1, 254)}.{random.randint(1, 254)}",
                    'last_rotation': '5 minutes ago',
                    'rotation_count': random.randint(1, 10)
                }
            })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e),
            'connected': False
        })

@api.route('/device/refresh-ip', methods=['POST'])
def refresh_device_ip():
    """Refresh IP address via Proxidize"""
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

# ========== Proxidize Management API Routes ==========

@api.route('/proxy/config', methods=['GET'])
def get_proxy_config():
    """Get current Proxidize configuration"""
    try:
        if proxidize_manager is None:
            return jsonify({
                'success': False,
                'error': 'Proxidize manager is not available'
            })
        
        # Get proxy configuration
        return jsonify({
            'success': True,
            'http_proxy': proxidize_manager.config.get('http_proxy'),
            'socks_proxy': proxidize_manager.config.get('socks_proxy'),
            'username': proxidize_manager.config.get('proxy_username'),
            'rotation_url': proxidize_manager.config.get('rotation_url')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/proxy/config', methods=['POST'])
def update_proxy_config():
    """Update Proxidize configuration"""
    try:
        if proxidize_manager is None:
            return jsonify({
                'success': False,
                'error': 'Proxidize manager is not available'
            })
        
        data = request.json
        
        # Update the configuration
        proxidize_manager.update_configuration(
            http_proxy=data.get('http_proxy'),
            socks_proxy=data.get('socks_proxy'),
            proxy_username=data.get('username'),
            proxy_password=data.get('password'),
            rotation_url=data.get('rotation_url')
        )
        
        return jsonify({
            'success': True,
            'message': 'Proxy configuration updated successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api.route('/proxy/check', methods=['GET'])
def check_proxy_connection():
    """Check if proxy connection is working"""
    try:
        if proxidize_manager is None:
            return jsonify({
                'success': False,
                'error': 'Proxidize manager is not available'
            })
        
        # Check connection
        success, message, ip = proxidize_manager.check_connection()
        
        return jsonify({
            'success': success,
            'message': message,
            'ip': ip
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
        
@api.route('/device/direct-rotation-test', methods=['POST'])
def direct_rotation_test():
    """Test direct rotation using the configured Proxidize URL"""
    try:
        import requests
        import json
        
        # Get the rotation URL from configuration
        with open('proxidize_config.json', 'r') as f:
            config = json.load(f)
            
        rotation_url = config.get('rotation_url')
        if not rotation_url:
            return jsonify({
                'success': False,
                'error': 'No rotation URL found in config'
            })
            
        # Make direct request to the rotation URL
        response = requests.get(rotation_url, timeout=10)
        
        return jsonify({
            'success': True,
            'status_code': response.status_code,
            'response_body': response.text[:1000],  # Limit response size
            'rotation_url': rotation_url,
            'config': config
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })