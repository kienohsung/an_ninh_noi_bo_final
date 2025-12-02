import requests
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from app.config import settings
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in settings.")
        exit(1)
        
    url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    print(f"Checking webhook status for bot...")
    resp = requests.get(url)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.json()}")
    
except Exception as e:
    print(f"Error: {e}")
