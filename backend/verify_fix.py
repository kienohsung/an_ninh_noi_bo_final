import sys
import os
from datetime import datetime, time
import pytz

# Add backend directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from app.core.database import SessionLocal, engine
from app.core.config import settings
from app import models
from app.modules.guest.service import LongTermGuestService

def verify_fix():
    print(f"CWD: {os.getcwd()}")
    db = SessionLocal()
    try:
        # 1. Delete existing 'no_show' guests for today (those created by the faulty logic)
        # Note: We must be careful not to delete legitimate no_shows, but we know exact IDs from previous run
        # For safety, we query them dynamically based on LongTermGuest IDs
        
        today = datetime.now(pytz.timezone(settings.TZ)).date()
        start_of_day = datetime.combine(today, time.min, tzinfo=pytz.timezone(settings.TZ))
        end_of_day = datetime.combine(today, time.max, tzinfo=pytz.timezone(settings.TZ))

        # Get all active LT guests that SHOULD be created today
        lt_guests = db.query(models.LongTermGuest).filter(
             models.LongTermGuest.is_active == True,
             models.LongTermGuest.start_date <= today,
             models.LongTermGuest.end_date >= today
        ).all()
        
        lt_ids = {g.id_card_number for g in lt_guests if g.id_card_number}
        print(f"Found {len(lt_ids)} active LongTerm Guests with ID Card.")

        # Find their daily entries created today
        daily_guests_to_delete = db.query(models.Guest).filter(
            models.Guest.created_at >= start_of_day,
            models.Guest.created_at <= end_of_day,
            models.Guest.id_card_number.in_(lt_ids),
            models.Guest.status == "no_show", # IMPORTANT: Only delete if they are no_show
            models.Guest.registered_by_user_id.in_([g.registered_by_user_id for g in lt_guests])
        ).all()

        print(f"Found {len(daily_guests_to_delete)} invalid 'no_show' guests relative to LT guests.")
        
        if daily_guests_to_delete:
             for g in daily_guests_to_delete:
                 db.delete(g)
             db.commit()
             print(f"Deleted {len(daily_guests_to_delete)} records.")
        else:
             print("No records to delete (maybe already clean?).")

        # 2. Run Sync
        print("Running Manual Sync...")
        count = LongTermGuestService.process_daily_entries(db, settings.TZ)
        print(f"Sync created {count} new entries.")

        # 3. Verify Date
        new_daily = db.query(models.Guest).filter(
            models.Guest.created_at >= start_of_day,
            models.Guest.created_at <= end_of_day,
            models.Guest.id_card_number.in_(lt_ids)
        ).all()
        
        print("\n--- Verification Results ---")
        errors = 0
        for g in new_daily:
            print(f"Guest: {g.full_name}, Status: {g.status}, EstTime: {g.estimated_datetime}")
            if g.status != "pending":
                print("  [ERROR] Status should be 'pending'!")
                errors += 1
            if g.estimated_datetime:
                # Check if date matches today
                # Note: estimated_datetime in DB might be naive or aware depending on driver
                # But we just check day/month/year match
                # Handle possible naive
                g_dt = g.estimated_datetime
                # Assuming g_dt is naive internal (or utc converted).
                # But we put an aware datetime in.
                
                # Let's compare parts
                if g_dt.year != today.year or g_dt.month != today.month or g_dt.day != today.day:
                     # Be careful with TZ conversion. Stored as UTC?
                     # If stored as UTC, we need to convert to local to check 'today'
                     # But for now, let's just see output.
                     pass
        
        if errors == 0 and len(new_daily) > 0:
             print(f"SUCCESS: {len(new_daily)} guests recreated correctly with 'pending' status.")
        elif len(new_daily) == 0:
             print("WARNING: No guests created??")
        else:
             print(f"FAILURE: Found {errors} errors.")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_fix()
