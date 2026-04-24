"""Run this once to get a Google refresh token for the bot."""
import os
import sys

# Run from the project root directory
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/tasks",
]

flow = InstalledAppFlow.from_client_secrets_file("google_client_secret.json", SCOPES)

try:
    creds = flow.run_local_server(
        port=8765,
        access_type="offline",
        prompt="consent",
    )
except OSError as e:
    print(f"\nLocal server failed ({e}); switching to manual mode.")
    print("A URL will appear below. Open it in your browser, approve, then paste the code here.\n")
    creds = flow.run_console()

if not creds.refresh_token:
    print("\nERROR: No refresh token returned.")
    print("Go to https://myaccount.google.com/permissions, remove the app, and run this script again.")
    sys.exit(1)

print("\n" + "="*60)
print("SUCCESS! Copy these 3 values into your .env file:")
print("="*60)
print(f"GOOGLE_CLIENT_ID={flow.client_config['client_id']}")
print(f"GOOGLE_CLIENT_SECRET={flow.client_config['client_secret']}")
print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
print("="*60)
