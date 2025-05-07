def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

def process_assets():
    """Process and copy assets to static folder"""
    # Check if attached logo exists and copy it to static folder if needed
    attached_logo = "attached_assets/progress_logo.png"
    if os.path.exists(attached_logo) and not os.path.exists("static/progress_logo.png"):
        import shutil
        shutil.copy(attached_logo, "static/progress_logo.png")
    
    # Check if attached background exists and copy it to static folder if needed
    attached_bg = "attached_assets/progress_background.jpg"
    if os.path.exists(attached_bg) and not os.path.exists("static/progress_background.jpg"):
        import shutil
        shutil.copy(attached_bg, "static/progress_background.jpg")

@app.route('/manual_messaging')
def manual_messaging_page():
    """The manual messaging page where you can send messages from a list of numbers"""
    process_assets()
    nav_menu = get_nav_menu('/manual_messaging')
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ProgressGhostCreator - Manual Messaging</title>
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
            
            .app-content {
                display: flex;
                flex: 1;
                overflow: hidden;
            }
            
            .accounts-panel {
                width: 250px;
                background-color: #2A2A2A;
                border-right: 1px solid #444;
                display: flex;
                flex-direction: column;
            }
            
            .accounts-header {
                padding: 15px;
                border-bottom: 1px solid #444;
                font-weight: bold;
            }
            
            .accounts-search {
                padding: 10px;
                border-bottom: 1px solid #444;
            }
            
            .search-input {
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 12px;
            }
            
            .accounts-list {
                flex: 1;
                overflow-y: auto;
            }
            
            .account-item {
                padding: 12px 15px;
                border-bottom: 1px solid #444;
                cursor: pointer;
                display: flex;
                align-items: center;
            }
            
            .account-item:hover {
                background-color: #333;
            }
            
            .account-item.active {
                background-color: #3A3A3A;
            }
            
            .account-status {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                margin-right: 10px;
            }
            
            .status-active {
                background-color: #5F5;
            }
            
            .status-inactive {
                background-color: #F55;
            }
            
            .status-warning {
                background-color: #FF5;
            }
            
            .account-name {
                font-size: 13px;
                flex: 1;
            }
            
            .account-phone {
                color: #999;
                font-size: 12px;
            }
            
            .messaging-panel {
                flex: 1;
                display: flex;
                flex-direction: column;
                padding: 20px;
            }
            
            .panel-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            
            .panel-title {
                font-size: 18px;
                font-weight: bold;
            }
            
            .recipient-section {
                background-color: #2A2A2A;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 15px;
            }
            
            .section-title {
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 10px;
                color: #EEE;
            }
            
            .recipient-input {
                width: 100%;
                height: 100px;
                padding: 10px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 14px;
                resize: none;
                font-family: monospace;
            }
            
            .recipient-hint {
                font-size: 12px;
                color: #AAA;
                margin-top: 5px;
            }
            
            .message-section {
                background-color: #2A2A2A;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 15px;
                flex: 1;
                display: flex;
                flex-direction: column;
            }
            
            .message-input {
                width: 100%;
                flex: 1;
                padding: 10px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 14px;
                resize: none;
                font-family: Arial, sans-serif;
                margin-bottom: 10px;
            }
            
            .send-options {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .send-from {
                display: flex;
                align-items: center;
            }
            
            .send-label {
                margin-right: 10px;
                font-size: 14px;
                color: #CCC;
            }
            
            .send-select {
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #333;
                color: #EEE;
                font-size: 14px;
            }
            
            .send-button {
                background-color: #FF6600;
                color: white;
                border: none;
                padding: 10px 20px;
                cursor: pointer;
                border-radius: 4px;
                font-weight: bold;
            }
            
            .send-button:hover {
                background-color: #FF7722;
            }
            
            .stats-panel {
                width: 250px;
                background-color: #2A2A2A;
                border-left: 1px solid #444;
                padding: 15px;
                overflow-y: auto;
            }
            
            .stats-header {
                font-weight: bold;
                margin-bottom: 15px;
                border-bottom: 1px solid #444;
                padding-bottom: 10px;
            }
            
            .stat-group {
                margin-bottom: 20px;
            }
            
            .stat-title {
                font-size: 13px;
                color: #CCC;
                margin-bottom: 5px;
            }
            
            .stat-value {
                font-size: 18px;
                font-weight: bold;
                color: #EEE;
            }
            
            .stat-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            
            .stat-label {
                font-size: 13px;
                color: #AAA;
            }
            
            .account-filter {
                margin-top: 10px;
                font-size: 13px;
                color: #AAA;
                display: flex;
                align-items: center;
            }
            
            .filter-checkbox {
                margin-right: 5px;
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
                <div class="accounts-panel">
                    <div class="accounts-header">
                        Available Accounts (15)
                    </div>
                    <div class="accounts-search">
                        <input type="text" class="search-input" placeholder="Search accounts...">
                    </div>
                    <div class="accounts-list">
                        <div class="account-item active">
                            <div class="account-status status-active"></div>
                            <div class="account-name">ghost_user_123</div>
                            <div class="account-phone">(954) 555-1234</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-active"></div>
                            <div class="account-name">phantom_754</div>
                            <div class="account-phone">(754) 555-2345</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-active"></div>
                            <div class="account-name">shadow_play_305</div>
                            <div class="account-phone">(305) 555-3456</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-warning"></div>
                            <div class="account-name">stealth_786</div>
                            <div class="account-phone">(786) 555-4567</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-active"></div>
                            <div class="account-name">ghost_561</div>
                            <div class="account-phone">(561) 555-5678</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-inactive"></div>
                            <div class="account-name">shadow_904</div>
                            <div class="account-phone">(904) 555-6789</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-active"></div>
                            <div class="account-name">phantom_850</div>
                            <div class="account-phone">(850) 555-7890</div>
                        </div>
                        <div class="account-item">
                            <div class="account-status status-active"></div>
                            <div class="account-name">ghost_386</div>
                            <div class="account-phone">(386) 555-8901</div>
                        </div>
                    </div>
                </div>
                
                <div class="messaging-panel">
                    <div class="panel-header">
                        <div class="panel-title">Manual Message Sending</div>
                    </div>
                    
                    <div class="recipient-section">
                        <div class="section-title">Recipients (phone numbers)</div>
                        <textarea class="recipient-input" placeholder="Enter phone numbers, one per line or comma-separated">5555551234
5555552345
5555553456, 5555554567
5555555678</textarea>
                        <div class="recipient-hint">Enter one number per line or comma-separated. Format: 10 digits, with or without formatting.</div>
                    </div>
                    
                    <div class="message-section">
                        <div class="section-title">Message Content</div>
                        <textarea class="message-input" placeholder="Type your message here...">Hey there! Check out our latest promo at PB Betting. Reply STOP to opt out.</textarea>
                        
                        <div class="mms-section" style="margin-bottom: 10px; border-top: 1px solid #444; padding-top: 10px;">
                            <div class="section-title">MMS Attachments</div>
                            <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px;">
                                <div style="display: flex; flex-direction: column; align-items: center;">
                                    <div style="width: 80px; height: 80px; background: #333; border: 1px dashed #666; border-radius: 5px; display: flex; justify-content: center; align-items: center; cursor: pointer;">
                                        <span style="font-size: 24px; color: #666;">+</span>
                                    </div>
                                    <span style="font-size: 12px; color: #AAA; margin-top: 5px;">Add Image</span>
                                </div>
                                <div style="display: flex; flex-direction: column; align-items: center;">
                                    <div style="width: 80px; height: 80px; background: #333; border-radius: 5px; position: relative; overflow: hidden;">
                                        <div style="position: absolute; top: 0; right: 0; background: rgba(0,0,0,0.5); width: 20px; height: 20px; display: flex; justify-content: center; align-items: center; cursor: pointer;">
                                            <span style="color: #FFF; font-size: 14px;">×</span>
                                        </div>
                                        <div style="width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; color: #AAA; font-size: 10px; padding: 5px; text-align: center;">
                                            example.jpg
                                        </div>
                                    </div>
                                    <span style="font-size: 12px; color: #AAA; margin-top: 5px;">20 KB</span>
                                </div>
                            </div>
                            <div style="margin-top: 10px;">
                                <input type="file" id="mms-file" style="display: none;" multiple accept="image/*,video/*,.csv,.txt,.xlsx,.xls">
                                <button style="background-color: #444; color: white; border: none; padding: 6px 12px; cursor: pointer; border-radius: 3px; font-size: 12px;" onclick="document.getElementById('mms-file').click()">Upload Files</button>
                                <span style="font-size: 11px; color: #AAA; margin-left: 10px;">Supported: JPG, PNG, GIF, MP4, CSV, TXT, XLSX, XLS (max 5MB)</span>
                            </div>
                        </div>
                        
                        <div class="time-distribution" style="margin-bottom: 15px; border-top: 1px solid #444; padding-top: 15px;">
                            <div class="section-title">Time Distribution</div>
                            <div style="display: flex; margin-top: 10px; align-items: center; justify-content: space-between;">
                                <div style="flex: 1;">
                                    <div style="margin-bottom: 8px; display: flex; align-items: center;">
                                        <input type="radio" id="dist-none" name="distribution" checked style="margin-right: 8px;">
                                        <label for="dist-none" style="font-size: 13px; color: #CCC;">No Distribution (Send Immediately)</label>
                                    </div>
                                    <div style="margin-bottom: 8px; display: flex; align-items: center;">
                                        <input type="radio" id="dist-1h" name="distribution" style="margin-right: 8px;">
                                        <label for="dist-1h" style="font-size: 13px; color: #CCC;">1 Hour Distribution</label>
                                    </div>
                                    <div style="margin-bottom: 8px; display: flex; align-items: center;">
                                        <input type="radio" id="dist-2h" name="distribution" style="margin-right: 8px;">
                                        <label for="dist-2h" style="font-size: 13px; color: #CCC;">2 Hour Distribution</label>
                                    </div>
                                </div>
                                <div style="flex: 1;">
                                    <div style="margin-bottom: 8px; display: flex; align-items: center;">
                                        <input type="radio" id="dist-4h" name="distribution" style="margin-right: 8px;">
                                        <label for="dist-4h" style="font-size: 13px; color: #CCC;">4 Hour Distribution</label>
                                    </div>
                                    <div style="margin-bottom: 8px; display: flex; align-items: center;">
                                        <input type="radio" id="dist-12h" name="distribution" style="margin-right: 8px;">
                                        <label for="dist-12h" style="font-size: 13px; color: #CCC;">12 Hour Distribution</label>
                                    </div>
                                    <div style="margin-bottom: 8px; display: flex; align-items: center;">
                                        <input type="radio" id="dist-24h" name="distribution" style="margin-right: 8px;">
                                        <label for="dist-24h" style="font-size: 13px; color: #CCC;">24 Hour Distribution</label>
                                    </div>
                                </div>
                            </div>
                            <div style="margin-top: 5px; font-size: 11px; color: #AAA;">
                                Messages will be distributed evenly over the selected time period to avoid detection. The system will automatically vary timing between messages.
                            </div>
                        </div>
                        
                        <div class="send-options">
                            <div class="send-from">
                                <div class="send-label">Send from:</div>
                                <select class="send-select">
                                    <option>ghost_user_123 (954-555-1234)</option>
                                    <option>phantom_754 (754-555-2345)</option>
                                    <option>Random Account</option>
                                    <option>Distribute Among All</option>
                                </select>
                            </div>
                            
                            <div style="display: flex;">
                                <button id="start-button" class="send-button" style="background-color: #FF6600; margin-right: 10px; padding: 10px 20px; border: none; color: white; font-weight: bold; border-radius: 4px; cursor: pointer;">Start</button>
                                <button id="pause-button" style="background-color: #DDAA00; margin-right: 10px; padding: 10px 15px; border: none; color: white; font-weight: bold; border-radius: 4px; cursor: pointer; opacity: 0.5;" disabled>Pause</button>
                                <button id="stop-button" style="background-color: #DD3300; padding: 10px 15px; border: none; color: white; font-weight: bold; border-radius: 4px; cursor: pointer; opacity: 0.5;" disabled>Stop</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="stats-panel">
                    <div class="stats-header">Messaging Statistics</div>
                    
                    <div class="stat-group">
                        <div class="stat-title">Today's Activity</div>
                        <div class="stat-row">
                            <div class="stat-label">Messages Sent:</div>
                            <div class="stat-value">1,256</div>
                        </div>
                        <div class="stat-row">
                            <div class="stat-label">Delivery Rate:</div>
                            <div class="stat-value">98.5%</div>
                        </div>
                        <div class="stat-row">
                            <div class="stat-label">Response Rate:</div>
                            <div class="stat-value">12.3%</div>
                        </div>
                    </div>
                    
                    <div class="stat-group">
                        <div class="stat-title">Account Health</div>
                        <div class="stat-row">
                            <div class="stat-label">Active Accounts:</div>
                            <div class="stat-value">12/15</div>
                        </div>
                        <div class="stat-row">
                            <div class="stat-label">At Risk:</div>
                            <div class="stat-value">2</div>
                        </div>
                        <div class="stat-row">
                            <div class="stat-label">Blocked:</div>
                            <div class="stat-value">1</div>
                        </div>
                    </div>
                    
                    <div class="stat-group">
                        <div class="stat-title">Rate Limits</div>
                        <div class="stat-row">
                            <div class="stat-label">Daily Limit:</div>
                            <div class="stat-value">100K</div>
                        </div>
                        <div class="stat-row">
                            <div class="stat-label">Used Today:</div>
                            <div class="stat-value">1.3%</div>
                        </div>
                        <div class="stat-row">
                            <div class="stat-label">Per Account:</div>
                            <div class="stat-value">~105</div>
                        </div>
                    </div>
                    
                    <div class="account-filter">
                        <input type="checkbox" id="show-active" class="filter-checkbox" checked>
                        <label for="show-active">Show only active accounts</label>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Get distribution time
            function getSelectedDistribution() {
                const distributions = document.querySelectorAll('input[name="distribution"]');
                for (const dist of distributions) {
                    if (dist.checked) {
                        return dist.id;
                    }
                }
                return 'dist-none';
            }
            
            // Variables to track messaging job
            let messagingActive = false;
            let messagingPaused = false;
            let progressInterval = null;
            let progressCounter = 0;
            let totalMessages = 0;
            let sentMessages = 0;
            
            // Handle button states
            function updateButtonStates() {
                const startButton = document.getElementById('start-button');
                const pauseButton = document.getElementById('pause-button');
                const stopButton = document.getElementById('stop-button');
                
                if (messagingActive) {
                    startButton.disabled = true;
                    startButton.style.opacity = '0.5';
                    stopButton.disabled = false;
                    stopButton.style.opacity = '1';
                    
                    if (messagingPaused) {
                        pauseButton.innerHTML = 'Resume';
                        pauseButton.style.backgroundColor = '#55AA00';
                    } else {
                        pauseButton.innerHTML = 'Pause';
                        pauseButton.style.backgroundColor = '#DDAA00';
                    }
                    
                    pauseButton.disabled = false;
                    pauseButton.style.opacity = '1';
                } else {
                    startButton.disabled = false;
                    startButton.style.opacity = '1';
                    pauseButton.disabled = true;
                    pauseButton.style.opacity = '0.5';
                    stopButton.disabled = true;
                    stopButton.style.opacity = '0.5';
                    pauseButton.innerHTML = 'Pause';
                }
            }
            
            // Start messaging job
            document.getElementById('start-button').addEventListener('click', function() {
                const recipients = document.querySelector('.recipient-input').value;
                const message = document.querySelector('.message-input').value;
                const selectedAccount = document.querySelector('.send-select').value;
                const distribution = getSelectedDistribution();
                
                totalMessages = 0;
                recipients.split(/[\n,]/).forEach(function(recipient) {
                    if (recipient.trim().length > 0) {
                        totalMessages++;
                    }
                });
                
                if (totalMessages === 0) {
                    alert('Please enter at least one recipient phone number.');
                    return;
                }
                
                if (message.trim() === '') {
                    alert('Please enter a message to send.');
                    return;
                }
                
                // Get distribution time display
                let distDisplay = "immediately";
                let updateFrequency = 100; // milliseconds
                
                switch(distribution) {
                    case 'dist-1h': 
                        distDisplay = "over 1 hour"; 
                        updateFrequency = 1000; 
                        break;
                    case 'dist-2h': 
                        distDisplay = "over 2 hours"; 
                        updateFrequency = 2000; 
                        break;
                    case 'dist-4h': 
                        distDisplay = "over 4 hours"; 
                        updateFrequency = 3000; 
                        break;
                    case 'dist-12h': 
                        distDisplay = "over 12 hours"; 
                        updateFrequency = 5000; 
                        break;
                    case 'dist-24h': 
                        distDisplay = "over 24 hours"; 
                        updateFrequency = 8000; 
                        break;
                }
                
                messagingActive = true;
                messagingPaused = false;
                sentMessages = 0;
                updateButtonStates();
                
                // For the demo, we'll simulate sending with a progress counter
                progressInterval = setInterval(function() {
                    if (!messagingPaused && sentMessages < totalMessages) {
                        sentMessages++;
                        document.querySelector('.stat-value').innerText = sentMessages.toLocaleString();
                        document.querySelector('.stat-value:nth-child(2)').innerText = Math.round((sentMessages / totalMessages) * 100) + '%';
                        
                        // Update progress in stats
                        const usedPercentage = (sentMessages / 100000 * 100).toFixed(1);
                        document.querySelector('.stat-group:nth-child(3) .stat-row:nth-child(2) .stat-value').innerText = usedPercentage + '%';
                        
                        if (sentMessages >= totalMessages) {
                            clearInterval(progressInterval);
                            messagingActive = false;
                            updateButtonStates();
                            alert(`Completed sending ${totalMessages} messages!`);
                        }
                    }
                }, updateFrequency);
                
                alert(`Starting to send ${totalMessages} messages ${distDisplay} from account: ${selectedAccount}`);
            });
            
            // Pause messaging job
            document.getElementById('pause-button').addEventListener('click', function() {
                if (messagingActive) {
                    messagingPaused = !messagingPaused;
                    
                    if (messagingPaused) {
                        alert('Message sending paused. Click "Resume" to continue.');
                    } else {
                        alert('Message sending resumed.');
                    }
                    
                    updateButtonStates();
                }
            });
            
            // Stop messaging job
            document.getElementById('stop-button').addEventListener('click', function() {
                if (messagingActive) {
                    clearInterval(progressInterval);
                    messagingActive = false;
                    messagingPaused = false;
                    alert(`Messaging stopped. ${sentMessages} out of ${totalMessages} messages were sent.`);
                    updateButtonStates();
                }
            });
            
            document.querySelectorAll('.account-item').forEach(function(item) {
                item.addEventListener('click', function() {
                    document.querySelectorAll('.account-item').forEach(function(i) {
                        i.classList.remove('active');
                    });
                    item.classList.add('active');
                });
            });
        </script>
    </body>
    </html>
    ''', logo_exists=os.path.exists("static/progress_logo.png"))

if __name__ == '__main__':
    # Check if assets folder exists and create it if not
    os.makedirs('assets', exist_ok=True)
    
    # Copy logo and background from attached_assets if needed
    if os.path.exists("attached_assets/progress_logo.png") and not os.path.exists("assets/progress_logo.png"):
        import shutil
        shutil.copy("attached_assets/progress_logo.png", "assets/progress_logo.png")
        
    if os.path.exists("attached_assets/progress_background.jpg") and not os.path.exists("assets/progress_background.jpg"):
        import shutil
        shutil.copy("attached_assets/progress_background.jpg", "assets/progress_background.jpg")
    
    # Start the Flask development server
    app.run(host='0.0.0.0', port=5000, debug=True)