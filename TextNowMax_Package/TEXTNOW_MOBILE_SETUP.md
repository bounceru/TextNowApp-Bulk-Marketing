# TextNow Mobile Creator Setup

This guide explains how to set up and use the TextNow Mobile Creator, which uses Android emulation to create TextNow accounts through the mobile app.

## Initial Setup

1. **Run SETUP_ANDROID_EMULATOR.bat**
   - This will download and install the Android SDK and emulator
   - It will create 3 different emulator profiles with different device fingerprints
   - This is a one-time setup process that may take 20-30 minutes

2. **Get the TextNow APK**
   - Download the TextNow APK from a legitimate source like APKPure
   - Save it as `textnow.apk` in the `apk` folder

3. **Configure Proxidize**
   - Make sure your Proxidize device is properly connected
   - Update the `proxidize_config.json` with your API key and device IP

## Using the Account Creator

### Method 1: Through the Web Interface

1. Start the Android emulator by running `START_EMULATOR.bat`
2. Wait for the emulator to fully boot (may take 2-3 minutes)
3. Run TextNow Max with `RUN_TEXTNOW_MAX.bat`
4. Go to the Account Creator tab
5. Select how many accounts to create and your preferred area codes
6. Click "Start Creation" 
7. The system will automatically create accounts using the emulator
8. You can watch progress in real-time

### Method 2: Using the Console

If you prefer to use the command line:

1. Start the Android emulator by running `START_EMULATOR.bat`
2. Wait for the emulator to fully boot
3. Run `python console_desktop_app.py`
4. Choose option 1 for "Create Accounts"
5. Follow the prompts to select number of accounts and area codes
6. The system will create accounts and show progress

## Troubleshooting

### Emulator Won't Start

- Check that you have at least 8GB of RAM available
- Make sure Java JDK is installed and in your PATH
- Try running with fewer emulator instances by editing `emulator_config.json`

### Account Creation Errors

- Make sure your Proxidize device is connected and working
- Check that the TextNow APK is placed in the correct location
- Try using different area codes
- If TextNow has updated their app, download the latest APK

### System Requirements

- Windows 10 or 11 (64-bit)
- 8GB RAM minimum (16GB recommended)
- 50GB free disk space
- Intel or AMD processor with virtualization support
- Java JDK 8 or newer

## Advanced Configuration

You can customize the emulator setup by editing `emulator_config.json`:

```json
{
  "emulator_count": 2,         // Number of parallel emulators
  "headless_mode": true,       // Run without visible UI
  "apk_path": "./apk/textnow.apk",
  "sdk_path": "./android-sdk",
  "proxy_per_emulator": true,  // Use different proxy per emulator
  "reset_after_count": 5       // Reset fingerprint after X accounts
}
```

## Understanding the Process

The system creates accounts by:

1. Starting multiple Android emulators with different device profiles
2. Connecting each emulator to a different Proxidize mobile IP
3. Installing and launching the TextNow app
4. Automating the sign-up process with random profile data
5. Selecting phone numbers based on your preferred area codes
6. Verifying the accounts are working properly
7. Saving all details to the ghost_accounts.db database
8. Rotating IPs and device fingerprints regularly

This approach maintains high success rates because it uses the official TextNow app on what appears to be real Android devices, each with unique hardware fingerprints and mobile IPs.