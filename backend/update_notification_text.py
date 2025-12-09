import sys
import os
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv(".env")

from app.core.config import settings
settings.DATABASE_URL = "sqlite:///backend/security_v2_3.db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Notification

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("--- Updating Notification Text ---")
try:
    # Find notifications with OLD TITLE
    old_title = "⚠️ Cảnh báo: Khách No-show"
    new_title = "⚠️ Cảnh báo: Khách đăng ký nhưng không tới"
    
    notifs = db.query(Notification).filter(Notification.title == old_title).all()
    
    print(f"Found {len(notifs)} notifications to update title.")
    
    for n in notifs:
        n.title = new_title
        # Message is likely already correct from previous run, but we can verify/force it if needed.
        # For now, just title.
        
    db.commit()
    print("Title update complete.")
    
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
