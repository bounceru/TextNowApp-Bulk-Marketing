# TextNow Max - Windows Setup Guide

## Installation Steps

### Step 1: Download the Files
1. Download `TextNowMax.zip` from this project
2. Extract the ZIP file to a location on your computer (e.g., `C:\TextNowMax`)

### Step 2: Install Required Software
1. **Install Python 3.10 or newer:**
   - Download from [Python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation

2. **Install Chrome browser (if not already installed)**
   - Download from [Google Chrome](https://www.google.com/chrome/)

### Step 3: Install Dependencies
1. Open Command Prompt as Administrator
2. Navigate to your TextNow Max folder:
   ```
   cd C:\TextNowMax
   ```
3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

### Step 4: Configure Proxidize (if available)
1. Ensure your Proxidize PGS device is powered on and connected to your network
2. Edit `proxidize_config.json` with your Proxidize API credentials:
   ```json
   {
     "api_key": "YOUR_PROXIDIZE_API_KEY",
     "port": 5656,
     "device_ip": "192.168.1.XX"  // Your Proxidize device IP
   }
   ```

### Step 5: Run the Application
1. From the Command Prompt in your TextNow Max folder, run:
   ```
   python fixed_clickable_original.py
   ```
2. Access the application in your browser at:
   ```
   http://localhost:5000
   ```

## Troubleshooting

### Browser Automation Issues
- Make sure Chrome browser is installed and up to date
- If you see errors about Chrome driver, try reinstalling the Playwright dependencies:
  ```
  python -m playwright install
  ```

### Proxidize Connection Issues
- Ensure your Proxidize device is powered on and connected
- Verify the IP address in `proxidize_config.json` matches your device
- Check that the API key is entered correctly

### Application Won't Start
- Make sure all required packages are installed
- Try running as Administrator
- Check if port 5000 is already in use by another application

## Running the Console Version
For a command-line version of the application, run:
```
python console_desktop_app.py
```

## Creating TextNow Accounts
1. Go to the Account Creator tab
2. Set the desired number of accounts to create
3. Select your preferred area codes
4. Click "Start Creation"
5. The system will automatically create accounts with randomized details

## Additional Information
- All data is stored in `ghost_accounts.db` SQLite database
- Backup this file regularly to preserve your account data
- For more advanced customization, modify the relevant Python files