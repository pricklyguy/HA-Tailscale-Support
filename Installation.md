
Prickly Guy Remote Support Installation Guide
Prerequisites
Home Assistant installed and accessible
Access to Tailscale admin console
Text editor or notepad for copying credentials
Card Mod intalled for Dashboard card

Step 1: Prepare Home Assistant Package
Download the pg_support.yaml package file
Create file pg_support.yaml in /config/packages/ folder in Home Assistant
Copy downloaded yaml to that file
Do NOT restart yet - we'll use the commented sections as reference during setup

Step 2: Create Tailscale Account & Install
Help client create a Tailscale account at https://login.tailscale.com
Install Tailscale add-on in Home Assistant:
Go to Settings → Add-ons → Add-on Store
Search for "Tailscale"
Install and start the add-on
Check Tailscale add-on logs for the activation URL
Open the URL and log into the client's Tailscale account
Click "Add device" to authorize the Home Assistant instance

Step 3: Share Device with Support Account
In the client's Tailscale admin console, go to Machines
Click on the newly added Home Assistant device
Click Share (or the share icon)
Enter: Support@Pricklyguy.com
Click Share
Wait for Prickly Guy to accept the share before proceeding

Step 4: Configure Access Control List (ACL)
In the client's Tailscale admin console, go to Access Controls
Click Switch to JSON (if in visual editor mode)
Copy the ACL JSON from the commented section at the bottom of pg_support.yaml
Paste over the existing ACL content (please note if you have ever changed this file, you'll need to merge them)
Verify these sections exist:
tagOwners section contains: tag:client-device and tag:support-enabled
grants section contains rules for owner and pricklyguy@github
Click Save

Step 5: Get Device ID
Still in Tailscale admin console, go to Machines
Click on your Home Assistant device
Look for ID: field (example: xyMnrSTecxCNTRL)
Copy this ID - you'll need it for secrets.yaml
If you hover on the question mark, it will tell you this your tailnet id for your device

Step 6: Create OAuth Credentials
In Tailscale admin console, go to Settings → Trust Credentials
Click + Credential button
Select OAuth
Click Continue
Under Scopes, change from "Custom scopes" to "all: read and write"
Click Generate credential
IMPORTANT: Copy both the Client ID and Client secret immediately
Client ID: starts with k...
Client secret: starts with tskey-client-...
Paste both into Notepad or a document - you won't see the secret again!
Click Done

Step 7: Configure Home Assistant Secrets
Open /config/secrets.yaml in Home Assistant
Copy the secrets template from the commented section in pg_support.yaml
Update with your actual values:
 tailscale_oauth_client_id: "k1234..." # From Step 6 tailscale_oauth_client_secret: "tskey-client-k..." # From Step 6 tailscale_device_id: "xyMnrSTecxCNTRL" # From Step 5 # Update this payload with YOUR client_id and client_secrettailscale_oauth_payload: "client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET&grant_type=client_credentials"


Save the file (Ctrl+S or Cmd+S)

Step 8: Create Dashboard Card
Go to your Home Assistant dashboard
Create a new dashboard or add to existing (recommended: create "Support" dashboard)
Click Edit Dashboard → Add Card
Select Manual (or paste YAML directly)
Copy the dashboard card YAML from the commented section at bottom of pg_support.yaml
Paste into the card editor
Click Save

Step 9: Validate & Restart
Go to Developer Tools → YAML
Click Check Configuration
Wait for green checkmark ✓ (if errors, review secrets.yaml formatting)
Go to Settings → System → Restart
Click Restart Home Assistant (full restart, not just YAML reload)
Wait for Home Assistant to come back online (~2-3 minutes)

Step 10: Test the Setup
Go to your Support dashboard
Locate the "Remote Technical Support" card
Toggle "Enable Remote Support Access" to ON
Set timeout if needed (default: 2 hours)
Wait ~25 seconds for changes to propagate
Verify in Tailscale admin console:
Go to Machines → Click your HA device
Should show tag:support-enabled
Toggle the switch to OFF
Wait ~25 seconds
Verify device now shows tag:client-device (or no tags)
Notify Prickly Guy that setup is complete and working

Troubleshooting
Tags aren't changing
Go to Settings → System → Logs
Search for rest_command or tailscale
Check for error messages
Sensor shows "unavailable"
Verify OAuth credentials in secrets.yaml are correct
Check that tailscale_oauth_payload has YOUR actual client_id and client_secret (not placeholders)
Restart Home Assistant again
"Configuration invalid" error
Check secrets.yaml formatting (no extra spaces, quotes match)
Ensure all four secrets are defined
Make sure package file is in /config/packages/ folder
Still need help?
Screenshot the error from Logs
Contact Prickly Guy with screenshots

Security Notes for Clients
Only enable support access when you've requested help
Access automatically disables after the timeout period
You can manually disable anytime by toggling the switch
Your phones and tablets are never affected by this
OAuth credentials never expire - set it up once and forget it


Setup Complete! 🎉

