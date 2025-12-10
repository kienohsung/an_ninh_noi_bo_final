import sys
import os
from datetime import datetime, time

# Add backend directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from app.core.database import SessionLocal, engine
from app.core.config import settings
from app import models
import pytz
from sqlalchemy import select

def check_long_term_guests():
    print(f"CWD: {os.getcwd()}")
    print("--- Checking Long Term Guests ---")
    
    db = SessionLocal()
    try:
        guests = db.query(models.LongTermGuest).all()
        print(f"Total LongTermGuests: {len(guests)}")
        
        today = datetime.now(pytz.timezone(settings.TZ)).date()
        print(f"Today (Server TZ): {today}")
        
        active_candidates = []
        for g in guests:
            print(f"ID: {g.id}, Name: {g.full_name}, IDCard: '{g.id_card_number}', EstTime: {g.estimated_datetime}")
            
            is_valid_date = g.start_date <= today <= g.end_date
            if g.is_active and is_valid_date:
                active_candidates.append(g)
            else:
                print(f"  -> SKIPPED (Active: {g.is_active}, InDate: {is_valid_date})")

        print(f"\nActive Candidates for Today: {len(active_candidates)}")
        
        # Simulate ID checking logic
        start_of_day = datetime.combine(today, time.min, tzinfo=pytz.timezone(settings.TZ))
        end_of_day = datetime.combine(today, time.max, tzinfo=pytz.timezone(settings.TZ))

        id_cards_today = db.scalars(
            select(models.Guest.id_card_number).where(
                models.Guest.created_at >= start_of_day,
                models.Guest.created_at <= end_of_day,
                models.Guest.id_card_number != ""
            )
        ).all()
        id_set = set(id_cards_today)
        print(f"Existing Guest IDs today (Count: {len(id_set)}): {id_set}")
        
        # Get actual Guest objects to check status
        existing_guests = db.query(models.Guest).filter(
            models.Guest.created_at >= start_of_day,
            models.Guest.created_at <= end_of_day,
            models.Guest.id_card_number.in_(id_set)
        ).all()
        
        guest_map = {g.id_card_number: g for g in existing_guests}

        for g in active_candidates:
            if not g.id_card_number:
                print(f"  [!] Guest {g.full_name} (ID: {g.id}) has NO ID CARD NUMBER. Skipped by logic?")
            elif g.id_card_number in guest_map:
                 daily = guest_map[g.id_card_number]
                 print(f"  [EXISTS] Guest {g.full_name} (LT_ID: {g.id}) -> Daily Guest ID: {daily.id} | Status: {daily.status} | RegBy: {daily.registered_by_user_id} | Created: {daily.created_at}")
            else:
                print(f"  [MISSING] Guest {g.full_name} (ID: {g.id}) SHOULD BE CREATED but is NOT in map (Logic Mismatch?).")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_long_term_guests()
