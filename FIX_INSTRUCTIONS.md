# IP ROTATION FIX INSTRUCTIONS

Follow these steps to fix IP rotation in your local environment:

## What This Fix Does

This fix changes how the TextNow Max Creator handles IP rotation with Proxidize. Instead of simulating IP changes (which was needed for Replit), this fix actually checks your real IP through the proxy after rotation.

## Installation Instructions

1. Extract the `TextNowMax_Package.zip` file to your local system
2. Find and open the file `api_routes.py` in the TextNowMax_Package folder
3. Locate the function `refresh_device_ip()` (around line 532)
4. Replace the entire function with the code from `TrueIPRotation.py` included in the zip

## Verify Your Proxy Settings

Make sure your Proxidize configuration is correct in the application:

1. Open the TextNow Max Creator
2. Go to the "Proxy" tab
3. Verify these settings:
   - HTTP Proxy: nae2.proxi.es:2148
   - Username: proxidize-4XauY
   - Password: 4mhm9
   - Rotation URL: https://api.proxidize.com/api/v1/modem-token-command/rotate-modem-ip/c0e684189bcd2697f0831fb47759e005/

## Testing the Fix

1. After replacing the code, restart the application
2. Go to the "Proxy" tab
3. Click "Rotate IP" button
4. You should see a new IP address that is your actual Proxidize IP
5. Each rotation should show a different real IP address

## Troubleshooting

If you still encounter issues:

1. Check your internet connection
2. Verify Proxidize account is active
3. Make sure Proxidize's API endpoint is accessible from your network
4. Check Proxidize logs for any rate limits or errors
5. Try increasing the wait time after rotation (change value of `wait_time` in the code)