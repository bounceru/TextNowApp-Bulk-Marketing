"""
Image Management Dashboard for TextNow Max

This module provides a Flask route to display the image management interface
where users can view, upload, and delete images used in TextNow messaging.
"""

import os
import sqlite3
import uuid
import logging
import time
from flask import render_template, request, redirect, url_for, flash, jsonify, Blueprint
from werkzeug.utils import secure_filename

# Configure logging
logger = logging.getLogger('image_dashboard')

# Set up Blueprint
image_dashboard = Blueprint('image_dashboard', __name__)

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db_connection():
    """Get a connection to the SQLite database"""
    conn = sqlite3.connect('ghost_accounts.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_image_database():
    """Initialize the database tables for image management"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create images table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        description TEXT,
        mime_type TEXT,
        size INTEGER,
        width INTEGER,
        height INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        usage_count INTEGER DEFAULT 0,
        tags TEXT
    )
    ''')

    # Create image_usage table to track when images are used
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS image_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_id INTEGER,
        account_id INTEGER,
        usage_type TEXT,
        used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (image_id) REFERENCES images (id),
        FOREIGN KEY (account_id) REFERENCES accounts (id)
    )
    ''')

    conn.commit()
    conn.close()


def get_all_images():
    """Get all images from the database"""
    conn = get_db_connection()
    images = conn.execute('''
    SELECT id, filename, original_filename, description, 
           created_at, usage_count, tags
    FROM images
    ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    return images


@image_dashboard.route('/media-dashboard')
def image_dashboard_page():
    """Return the image management dashboard HTML"""
    # Initialize database if needed
    init_image_database()
    
    # Get all images
    images = get_all_images()
    
    # Get emulator status
    emulator_status = check_emulator_status()
    
    return render_template(
        'image_dashboard.html',
        images=images,
        emulator_status=emulator_status,
        page='image_dashboard'
    )


@image_dashboard.route('/upload-image', methods=['POST'])
def upload_image():
    """Handle image upload"""
    if 'image' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['image']
    
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Generate a unique filename
        original_filename = secure_filename(file.filename)
        extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{extension}"
        
        # Save the file
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Save to database
        conn = get_db_connection()
        conn.execute('''
        INSERT INTO images (filename, original_filename, description, mime_type, size)
        VALUES (?, ?, ?, ?, ?)
        ''', (unique_filename, original_filename, request.form.get('description', ''),
              file.content_type, file_size))
        conn.commit()
        conn.close()
        
        flash('Image uploaded successfully', 'success')
        return redirect(url_for('image_dashboard.image_dashboard_page'))
    
    flash('Invalid file type', 'error')
    return redirect(request.url)


@image_dashboard.route('/delete-image/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    """Delete an image"""
    conn = get_db_connection()
    image = conn.execute('SELECT filename FROM images WHERE id = ?', (image_id,)).fetchone()
    
    if image:
        # Delete the file
        file_path = os.path.join(UPLOAD_FOLDER, image['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        conn.execute('DELETE FROM image_usage WHERE image_id = ?', (image_id,))
        conn.execute('DELETE FROM images WHERE id = ?', (image_id,))
        conn.commit()
        flash('Image deleted successfully', 'success')
    else:
        flash('Image not found', 'error')
    
    conn.close()
    return redirect(url_for('image_dashboard.image_dashboard_page'))


@image_dashboard.route('/api/images', methods=['GET'])
def get_images_api():
    """API endpoint to get all images"""
    images = get_all_images()
    result = []
    
    for img in images:
        result.append({
            'id': img['id'],
            'filename': img['filename'],
            'original_filename': img['original_filename'],
            'description': img['description'],
            'created_at': img['created_at'],
            'usage_count': img['usage_count'],
            'tags': img['tags'],
            'url': url_for('static', filename=f'uploads/images/{img["filename"]}')
        })
    
    return jsonify(result)


# Android emulator integration functions
def check_emulator_status():
    """Check if the Android emulator is running"""
    try:
        # Check for running emulators using adb
        import subprocess
        result = subprocess.run(
            ["adb", "devices"], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        
        # Check if any emulator is in the list
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:  # More than just the "List of devices attached" header
            emulators = [line for line in lines[1:] if 'emulator' in line and 'device' in line]
            if emulators:
                return {
                    'running': True,
                    'count': len(emulators),
                    'devices': emulators
                }
        
        return {
            'running': False,
            'count': 0,
            'devices': []
        }
    except Exception as e:
        return {
            'running': False,
            'error': str(e),
            'count': 0,
            'devices': []
        }


@image_dashboard.route('/start-emulator', methods=['POST'])
def start_emulator():
    """Start the Android emulator"""
    try:
        # Check if already running
        status = check_emulator_status()
        if status['running']:
            return jsonify({
                'success': True,
                'message': f"Emulator already running with {status['count']} devices",
                'emulator_status': status
            })
        
        # Set environment variables
        import os
        
        # Get current directory
        current_dir = os.getcwd()
        sdk_path = os.path.join(current_dir, 'android-sdk')
        os.environ['ANDROID_HOME'] = sdk_path
        
        # Make sure the AVD directory exists
        avd_path = os.path.expanduser('~/.android/avd')
        os.makedirs(avd_path, exist_ok=True)
        
        # Make sure the APK directory exists
        apk_dir = os.path.join(current_dir, 'apk')
        os.makedirs(apk_dir, exist_ok=True)
        
        # Check if emulator exists
        import subprocess
        result = subprocess.run(
            ["avdmanager", "list", "avd"], 
            capture_output=True, 
            text=True,
            env=os.environ
        )
        
        # If the emulator doesn't exist, try to create it
        if "textnow_emulator_1" not in result.stdout:
            logger.info("Creating emulator profile: textnow_emulator_1")
            try:
                # Check for system images
                system_image_path = os.path.join(sdk_path, "system-images", "android-29", "google_apis", "x86_64")
                
                if not os.path.exists(system_image_path):
                    # Install required system image
                    logger.info("Installing required system images")
                    subprocess.run([
                        os.path.join(sdk_path, "tools", "bin", "sdkmanager"),
                        "system-images;android-29;google_apis;x86_64"
                    ], env=os.environ, check=True)
                
                # Create the emulator
                logger.info("Creating Android Virtual Device")
                subprocess.run([
                    os.path.join(sdk_path, "tools", "bin", "avdmanager"),
                    "create", "avd",
                    "-n", "textnow_emulator_1",
                    "-k", "system-images;android-29;google_apis;x86_64",
                    "-d", "pixel_3a"
                ], env=os.environ, check=True)
                
                logger.info("Emulator created successfully")
            except Exception as create_error:
                logger.error(f"Error creating emulator: {create_error}")
                return jsonify({
                    'success': False,
                    'message': f"Error creating emulator: {str(create_error)}",
                    'emulator_status': {
                        'running': False,
                        'error': str(create_error)
                    }
                })
        
        # Start emulator in background with retry logic
        import subprocess
        try:
            # Check if emulator executable exists
            emulator_path = os.path.join(sdk_path, "emulator", "emulator")
            if not os.path.exists(emulator_path):
                return jsonify({
                    'success': False,
                    'message': f"Emulator executable not found at {emulator_path}",
                    'emulator_status': {
                        'running': False,
                        'error': "Emulator executable not found"
                    }
                })
            
            # Start the emulator with optimized parameters
            subprocess.Popen([
                emulator_path,
                "-avd", "textnow_emulator_1",
                "-no-audio",
                "-no-boot-anim",
                "-gpu", "swiftshader_indirect",  # Better compatibility
                "-no-snapshot",  # Avoid snapshot issues
                "-memory", "2048"  # Allocate enough memory
            ], start_new_session=True, env=os.environ)
            
            # Start a monitor thread to check for successful boot
            import threading
            def monitor_boot():
                for _ in range(60):  # Check for 5 minutes (60 * 5 seconds)
                    time.sleep(5)
                    boot_status = check_emulator_status()
                    if boot_status['running']:
                        logger.info("Emulator booted successfully")
                        break
            
            threading.Thread(target=monitor_boot, daemon=True).start()
            
            return jsonify({
                'success': True,
                'message': "Emulator starting. It may take a minute to fully boot.",
                'emulator_status': {
                    'running': True,
                    'starting': True,
                    'count': 1
                }
            })
        except Exception as start_error:
            logger.error(f"Error starting emulator: {start_error}")
            return jsonify({
                'success': False,
                'message': f"Error starting emulator: {str(start_error)}",
                'emulator_status': {
                    'running': False,
                    'error': str(start_error)
                }
            })
    except Exception as e:
        logger.error(f"General error in start_emulator: {e}")
        return jsonify({
            'success': False,
            'message': f"Error starting emulator: {str(e)}",
            'emulator_status': {
                'running': False,
                'error': str(e)
            }
        })


@image_dashboard.route('/stop-emulator', methods=['POST'])
def stop_emulator():
    """Stop the Android emulator"""
    try:
        import subprocess
        subprocess.run(["adb", "emu", "kill"], check=True)
        
        return jsonify({
            'success': True,
            'message': "Emulator stopped successfully",
            'emulator_status': {
                'running': False,
                'count': 0
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error stopping emulator: {str(e)}",
            'emulator_status': check_emulator_status()
        })


@image_dashboard.route('/install-textnow', methods=['POST'])
def install_textnow():
    """Install TextNow APK on the emulator"""
    try:
        # Check if emulator is running
        status = check_emulator_status()
        if not status['running']:
            return jsonify({
                'success': False,
                'message': "Emulator is not running. Please start it first.",
                'emulator_status': status
            })
        
        # Create apk directory if it doesn't exist
        import os
        apk_dir = os.path.join(os.getcwd(), 'apk')
        os.makedirs(apk_dir, exist_ok=True)
        
        # Check if APK exists
        apk_path = os.path.join(apk_dir, 'textnow.apk')
        if not os.path.exists(apk_path):
            import time
            # Check if any APK files exist in the directory
            apk_files = [f for f in os.listdir(apk_dir) if f.endswith('.apk')]
            
            if apk_files:
                # Use the first APK found but rename it
                first_apk = apk_files[0]
                try:
                    import shutil
                    shutil.copy(os.path.join(apk_dir, first_apk), apk_path)
                    return jsonify({
                        'success': True,
                        'message': f"Found APK '{first_apk}' and renamed it to 'textnow.apk'. Proceeding with installation.",
                        'emulator_status': status
                    })
                except Exception as copy_error:
                    return jsonify({
                        'success': False,
                        'message': f"Found APK '{first_apk}' but failed to rename it: {str(copy_error)}. Please rename it manually to 'textnow.apk'.",
                        'emulator_status': status
                    })
            else:
                return jsonify({
                    'success': False,
                    'message': "TextNow APK not found. Please place it in the 'apk' folder as 'textnow.apk'. You can download it from APKPure or similar sites.",
                    'emulator_status': status
                })
        
        # Get device ID
        import subprocess
        device_result = subprocess.run(
            ["adb", "devices"], 
            capture_output=True, 
            text=True
        )
        
        device_lines = device_result.stdout.strip().split('\n')
        if len(device_lines) <= 1:
            return jsonify({
                'success': False,
                'message': "No connected devices found. Please make sure the emulator is running.",
                'emulator_status': status
            })
        
        device_id = None
        for line in device_lines[1:]:  # Skip header line
            if 'device' in line:
                device_id = line.split('\t')[0].strip()
                break
        
        if not device_id:
            return jsonify({
                'success': False,
                'message': "No ready devices found. The emulator might still be booting.",
                'emulator_status': status
            })
        
        # Check APK file size - warn if it's suspiciously small
        apk_size = os.path.getsize(apk_path)
        if apk_size < 1000000:  # Less than 1MB
            return jsonify({
                'success': False,
                'message': f"The APK file is suspiciously small ({apk_size} bytes). It might be corrupted or incomplete. Please download a valid TextNow APK.",
                'emulator_status': status
            })
        
        # Check if TextNow is already installed
        pkg_check = subprocess.run(
            ["adb", "-s", device_id, "shell", "pm", "list", "packages", "com.enflick.android.TextNow"],
            capture_output=True,
            text=True
        )
        
        if "com.enflick.android.TextNow" in pkg_check.stdout:
            # App already installed, check version
            version_check = subprocess.run(
                ["adb", "-s", device_id, "shell", "dumpsys", "package", "com.enflick.android.TextNow", "|", "grep", "versionName"],
                capture_output=True,
                text=True,
                shell=True
            )
            
            version = "unknown"
            if "versionName" in version_check.stdout:
                version = version_check.stdout.strip().split("=")[1].strip()
            
            return jsonify({
                'success': True,
                'message': f"TextNow is already installed (version {version}). You can proceed with account creation.",
                'emulator_status': status,
                'already_installed': True,
                'version': version
            })
        
        # Install APK with detailed error handling
        logger.info(f"Installing TextNow APK from {apk_path} to device {device_id}")
        
        # Install the APK
        result = subprocess.run(
            ["adb", "-s", device_id, "install", "-r", apk_path],
            capture_output=True,
            text=True,
            timeout=120  # Allow 2 minutes for installation
        )
        
        # Check for common error patterns
        if "INSTALL_FAILED_ALREADY_EXISTS" in result.stdout or "INSTALL_FAILED_ALREADY_EXISTS" in result.stderr:
            # Try uninstalling first
            subprocess.run(
                ["adb", "-s", device_id, "uninstall", "com.enflick.android.TextNow"],
                capture_output=True
            )
            
            # Try installing again
            result = subprocess.run(
                ["adb", "-s", device_id, "install", "-r", apk_path],
                capture_output=True,
                text=True
            )
        
        if "Success" in result.stdout or "success" in result.stdout.lower():
            # Verify it's actually installed
            verification = subprocess.run(
                ["adb", "-s", device_id, "shell", "pm", "list", "packages", "com.enflick.android.TextNow"],
                capture_output=True,
                text=True
            )
            
            if "com.enflick.android.TextNow" in verification.stdout:
                logger.info("TextNow APK installed successfully")
                return jsonify({
                    'success': True,
                    'message': "TextNow APK installed successfully",
                    'emulator_status': status
                })
            else:
                logger.error(f"Installation reported success but package not found: {verification.stdout}")
                return jsonify({
                    'success': False,
                    'message': "Installation reported success but the app was not found. The APK might be corrupted.",
                    'emulator_status': status
                })
        else:
            error_message = result.stderr if result.stderr else result.stdout
            logger.error(f"APK installation failed: {error_message}")
            
            # Check for specific error patterns
            if "INSTALL_FAILED_INVALID_APK" in error_message:
                return jsonify({
                    'success': False,
                    'message': "Invalid APK file. The TextNow APK might be corrupted. Please download a new copy.",
                    'emulator_status': status
                })
            elif "INSTALL_FAILED_INSUFFICIENT_STORAGE" in error_message:
                return jsonify({
                    'success': False,
                    'message': "Insufficient storage on the emulator. Try clearing space or creating a new emulator.",
                    'emulator_status': status
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f"Error installing APK: {error_message}",
                    'emulator_status': status
                })
    except subprocess.TimeoutExpired:
        logger.error("APK installation timed out")
        return jsonify({
            'success': False,
            'message': "Installation process timed out. The emulator might be running slowly or the APK might be too large.",
            'emulator_status': check_emulator_status()
        })
    except Exception as e:
        logger.error(f"Error installing TextNow APK: {e}")
        return jsonify({
            'success': False,
            'message': f"Error installing TextNow APK: {str(e)}",
            'emulator_status': check_emulator_status()
        })