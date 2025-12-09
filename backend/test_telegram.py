import sys
import os

# Add the backend directory to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.notifications import send_telegram_message, can_send_main, can_send_archive, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ARCHIVE_CHAT_ID, TELEGRAM_ENABLED

def test_telegram():
    print("--- Telegram Configuration Check ---")
    print(f"ENABLED: {TELEGRAM_ENABLED}")
    print(f"TOKEN: {TELEGRAM_BOT_TOKEN[:5]}...{TELEGRAM_BOT_TOKEN[-5:] if TELEGRAM_BOT_TOKEN else 'None'}")
    print(f"MAIN CHAT_ID: {TELEGRAM_CHAT_ID}")
    print(f"ARCHIVE CHAT_ID: {TELEGRAM_ARCHIVE_CHAT_ID}")
    
    if not can_send_main():
        print("❌ Cannot send to main channel: Check configuration.")
    else:
        print("\n--- Sending Test Message to MAIN ---")
        try:
            response = send_telegram_message("🔔 Test message to MAIN Channel.", TELEGRAM_CHAT_ID)
            if response.get("ok"):
                print("✅ Message sent to MAIN successfully!")
            else:
                print(f"❌ Failed to send to MAIN: {response.get('description')}")
        except Exception as e:
            print(f"❌ Exception (MAIN): {e}")

    if not can_send_archive():
         print("❌ Cannot send to archive channel: Check configuration (TELEGRAM_ARCHIVE_CHAT_ID).")
    else:
        print("\n--- Sending Test Message to ARCHIVE ---")
        try:
            response = send_telegram_message("🔔 Test message to ARCHIVE Channel.", TELEGRAM_ARCHIVE_CHAT_ID)
            if response.get("ok"):
                print("✅ Message sent to ARCHIVE successfully!")
            else:
                print(f"❌ Failed to send to ARCHIVE: {response.get('description')}")
        except Exception as e:
             print(f"❌ Exception (ARCHIVE): {e}")

if __name__ == "__main__":
    test_telegram()
