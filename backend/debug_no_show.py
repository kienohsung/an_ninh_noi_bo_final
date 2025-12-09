from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import sys
import os
from datetime import datetime

# Setup path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv(".env")

from app.core.config import settings
settings.DATABASE_URL = "sqlite:///backend/security_v2_3.db"
print(f"DB URL: {settings.DATABASE_URL}")

from app.models import Guest, User, Notification
import pytz

# DB Setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print(f"--- Debug Info ---")
print(f"Timezone: {settings.TZ}")
tz = pytz.timezone(settings.TZ)
now_aware = datetime.now(tz)
print(f"Current Server Time (Aware): {now_aware}")
today_start_aware = now_aware.replace(hour=0, minute=0, second=0, microsecond=0)
print(f"Today Start (Aware): {today_start_aware}")

print(f"\n--- Overdue Pending Guests Check ---")
# Query in Python to handle naive/aware safely as we did in main logic
pending_guests = db.query(Guest).filter(Guest.status == 'pending').all()
overdue_count = 0
for g in pending_guests:
    g_time = g.estimated_datetime
    if not g_time: continue
    
    if g_time.tzinfo is None:
        g_time = tz.localize(g_time)
        
    if g_time < today_start_aware:
        overdue_count += 1
        r_user = db.query(User).get(g.registered_by_user_id)
        r_str = f"{r_user.username} (ID: {r_user.id})" if r_user else "Unknown"
        print(f"[OVERDUE] ID: {g.id} | Name: {g.full_name} | Est: {g.estimated_datetime} | By: {r_str}")

print(f"Total Overdue Found: {overdue_count}")

print(f"\n--- Notifications for ADMIN (ID: 1) ---")
admin_notes = db.query(Notification).filter(Notification.user_id == 1).order_by(Notification.created_at.desc()).limit(5).all()
for n in admin_notes:
     print(f"ID: {n.id} | Title: {n.title} | Read: {n.is_read} | Time: {n.created_at}")

print(f"\n--- Notifications (Last 10) ---")
notifs = db.query(Notification).order_by(Notification.created_at.desc()).limit(10).all()
for n in notifs:
    u = db.query(User).get(n.user_id)
    u_name = u.username if u else "Unknown"
    print(f"ID: {n.id} | To: {u_name} (ID: {n.user_id}) | Title: {n.title} | Read: {n.is_read} | Time: {n.created_at}")

db.close()
