from backend.app.core.config import settings
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Force using backend DB
db_path = os.path.join(os.getcwd(), 'backend', 'security_v2_3.db')
settings.DATABASE_URL = f"sqlite:///{db_path}"

from backend.app.core.database import SessionLocal
from backend.app.modules.purchasing.model import PurchasingLog

def reset_item(item_id):
    db = SessionLocal()
    try:
        item = db.get(PurchasingLog, item_id)
        if item:
            print(f"Resetting Item {item.id} from {item.status} to approved")
            item.status = "approved"
            item.received_at = None
            db.commit()
            print("Done.")
        else:
            print(f"Item ID {item_id} not found")
    finally:
        db.close()

if __name__ == "__main__":
    reset_item(1)
