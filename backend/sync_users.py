import sys
import os
import logging

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- FIX PATHS ---
# Force absolute paths for DB and Credentials to avoid CWD issues
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(BASE_DIR, 'security_v2_3.db')}"
os.environ["GSHEETS_CREDENTIALS_PATH"] = os.path.join(BASE_DIR, "credentials.json")

from backend.app.database import SessionLocal
from backend.app.models import User
from backend.app.services.gsheets_reader import _get_service
from backend.app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SyncUsers")

def sync_users_to_sheet():
    logger.info("Starting user sync process...")
    
    # 1. Fetch Users from DB
    db = SessionLocal()
    try:
        users = db.query(User).all()
        logger.info(f"Found {len(users)} users in database.")
    except Exception as e:
        logger.error(f"Error fetching users from DB: {e}")
        return
    finally:
        db.close()

    # 2. Prepare Data for Sheet
    # Header
    values = [["EmployeeID", "Name"]]
    # Rows
    for user in users:
        # Use username as EmployeeID, full_name as Name
        values.append([user.username, user.full_name])

    # 3. Connect to Google Sheets
    try:
        service = _get_service()
    except Exception as e:
        logger.error(f"Error connecting to Google Sheets: {e}")
        return

    sheet_id = settings.GSHEETS_LIVE_SHEET_ID
    sheet_name = "Users"

    # 4. Check if 'Users' sheet exists, if not create it
    try:
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheets = spreadsheet.get('sheets', [])
        sheet_exists = any(s['properties']['title'] == sheet_name for s in sheets)

        if not sheet_exists:
            logger.info(f"Sheet '{sheet_name}' not found. Creating it...")
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
            }
            service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()
            logger.info(f"Sheet '{sheet_name}' created successfully.")
    except Exception as e:
        logger.error(f"Error checking/creating sheet: {e}")
        return

    # 5. Write Data
    range_name = f"'{sheet_name}'!A1"
    body = {
        'values': values
    }
    
    try:
        result = service.spreadsheets().values().update(
            spreadsheetId=sheet_id, range=range_name,
            valueInputOption='RAW', body=body
        ).execute()
        logger.info(f"{result.get('updatedCells')} cells updated.")
        logger.info("User sync completed successfully!")
    except Exception as e:
        logger.error(f"Error writing to Google Sheet: {e}")

if __name__ == "__main__":
    sync_users_to_sheet()
