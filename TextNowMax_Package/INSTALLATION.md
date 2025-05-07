# TextNow Max Installation Guide

## System Requirements
- Windows 10 or 11 (64-bit)
- Python 3.9+ installed
- Android emulator or physical device with USB debugging enabled (for account creation)

## Prerequisites 
1. Install Android SDK and add it to your PATH
2. Install Android Debug Bridge (ADB)
3. Set up a Proxidize PGS account for IP rotation
4. Have a standard TextNow APK file named "textnow.apk" (not XAPK)

## Installation Steps

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Proxidize
Edit the `proxidize_config.json` file with your Proxidize credentials:
```json
{
    "http_proxy": "your-proxy-server:port",
    "socks_proxy": "your-socks-proxy:port",
    "proxy_username": "your-username",
    "proxy_password": "your-password",
    "rotation_url": "https://api.proxidize.com/api/v1/modem-token-command/rotate-modem-ip/your-token/"
}
```

### 3. Set Up Android Emulator
Place the TextNow APK file in the root directory.

For physical devices, connect via USB and ensure debugging is enabled.

### 4. Initialize Database
Run:
```bash
python init_database.py
```

### 5. Launch the Application
```bash
python fixed_clickable_original.py
```

## Application Modes

The application operates in two primary modes:

1. **Account Creation Mode**: Uses Android emulator/device to create TextNow accounts
   - Requires ADB and an Android environment

2. **Proxy Mode**: Uses Proxidize for IP rotation during messaging campaigns
   - Requires a valid Proxidize configuration

## Troubleshooting

### Android Device Not Detected
- Ensure ADB is properly installed and in PATH
- Check USB debugging is enabled on device
- Run `adb devices` to verify connection

### Proxy Connection Issues
- Verify your Proxidize credentials
- Check network connectivity to the proxy server
- Test the rotation URL in a browser

### IP Rotation Not Working
- Verify the rotation URL format
- Check for any firewall restrictions
- Try manual rotation through the Proxidize interface

## Notes for Developers

- The IP rotation function in `api_routes.py` has been modified to handle environments where proxy connections might be blocked
- The system sends real rotation commands to Proxidize but may display simulated IPs in restricted environments
- In a production environment with proper proxy access, the system will automatically use and display real IPs