import sys
import os
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv(".env")

from app.core.config import settings
settings.DATABASE_URL = "sqlite:///backend/security_v2_3.db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.modules.guest.service import GuestService
from app.models import Guest

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("--- Manual Trigger Start ---")
try:
    count = GuestService.process_no_show_guests(db)
    print(f"Processed Count: {count}")
    
    pending_left = db.query(Guest).filter(Guest.status == 'pending').count()
    print(f"Pending Remaining: {pending_left}")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
