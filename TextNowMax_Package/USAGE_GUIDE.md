# TextNow Max - User Guide

## Getting Started

### Account Creation
1. Navigate to the "Account Creator" tab
2. Enter the number of accounts you want to create
3. Select your desired area codes (can select multiple states)
4. Click "Start Creation"
5. The system will automatically create TextNow accounts with random names and credentials
6. Progress will be shown in real-time with a status bar

### Managing Accounts
1. Navigate to the "Dashboard" tab to see all your accounts
2. You can see account details including:
   - Phone number
   - Username
   - Creation date
   - Last activity
   - Account health
3. Use the "Delete" button to remove accounts that are no longer needed
4. Use the "Edit" button to modify account details

## Sending Messages

### Manual Messaging
1. Navigate to the "Manual Messaging" tab
2. Select the TextNow accounts to use for sending
3. Import your recipients list (CSV format)
4. Create your message template with variables like {first_name}
5. Schedule delivery time or send immediately
6. Monitor delivery status in real-time

### Campaign Manager
1. Navigate to the "Campaigns" tab
2. Click "Create New Campaign"
3. Set campaign parameters:
   - Name
   - Message template
   - Number of accounts to use
   - Recipients per account
   - Schedule
4. Click "Start Campaign" to begin
5. Monitor progress and statistics

## Media Manager

### Images
1. Navigate to the "Images" tab
2. Upload new images to use in messages
3. View all uploaded images
4. Delete images you no longer need

### Voicemails
1. Navigate to the "Voicemails" tab
2. Upload audio files or generate new ones
3. Assign voicemails to accounts
4. Delete voicemails you no longer need

## Account Health Monitoring

1. Navigate to the "Account Health" tab
2. View health metrics for all accounts
3. Accounts are color-coded by health status:
   - Green: Healthy
   - Yellow: Warning
   - Red: Critical
4. Take action on flagged accounts before they become blocked

## IP Rotation with Proxidize

1. Ensure your Proxidize device is properly connected
2. Navigate to the "Device Manager" tab
3. View current IP and connection status
4. Click "Refresh IP" to rotate to a new mobile proxy
5. Set automatic rotation schedule if desired

## Backing Up Your Data

1. The system automatically backs up the database every 24 hours
2. Manual backup:
   - Navigate to your TextNow Max folder
   - Copy the `ghost_accounts.db` file to a safe location
3. To restore from backup, replace the current database file with your backup

## Troubleshooting

### Account Creation Issues
- Check your internet connection
- Ensure Proxidize is properly configured
- Try using different area codes

### Message Sending Issues
- Check account health status
- Ensure your proxy connection is working
- Rotate to a new IP address
- Reduce sending volume temporarily

### Application Won't Start
- Make sure all Python dependencies are installed
- Check if another application is using port 5000
- Run as Administrator if on Windows

For more detailed information, refer to the WINDOWS_SETUP.md file.