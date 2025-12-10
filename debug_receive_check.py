import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app.core.config import settings

# Force using backend DB
db_path = os.path.join(os.getcwd(), 'backend', 'security_v2_3.db')
settings.DATABASE_URL = f"sqlite:///{db_path}"

from backend.app.core.database import SessionLocal
from backend.app.modules.purchasing.model import PurchasingLog

def check_status(item_id):
    print(f"Checking DB at: {settings.DATABASE_URL}")
    db = SessionLocal()
    try:
        item = db.get(PurchasingLog, item_id)
        if item:
            print(f"Item ID: {item.id}")
            print(f"Status: {item.status}")
            print(f"Received At: {item.received_at}")
        else:
            print(f"Item ID {item_id} not found")
    finally:
        db.close()

if __name__ == "__main__":
    check_status(1)
