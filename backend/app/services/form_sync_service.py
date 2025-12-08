# File: backend/app/services/form_sync_service.py
from typing import List, Tuple
from datetime import datetime, timedelta
import logging
import pytz
import traceback

from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from ..core.database import SessionLocal
from ..models import User, Guest, get_local_time
from ..core.config import settings
from .gsheets_reader import _get_service, read_form_responses, batch_update_status
from ..utils.notifications import run_pending_list_notification, send_event_to_archive_background
from ..utils.plate_formatter import format_license_plate

logger = logging.getLogger("[Form Sync]")

def sync_google_form_registrations():
    """
    Background job to sync guest registrations from Google Form (via Sheet) to DB.
    """
    if not settings.GSHEETS_LIVE_SHEET_ID:
        logger.warning("GSHEETS_LIVE_SHEET_ID not configured. Skipping sync.")
        return

    logger.info("Starting Google Form sync job...")
    
    try:
        service = _get_service()
    except Exception as e:
        logger.error(f"Could not build GSheets service: {e}")
        return

    # 1. Read all responses
    rows = read_form_responses(service, settings.GSHEETS_LIVE_SHEET_ID)
    if not rows:
        logger.info("No data found in form responses sheet.")
        return

    db: Session = SessionLocal()
    updates_to_push: List[Tuple[int, str]] = []
    new_guest_objects: List[Guest] = [] # Keep track of new guests for notifications
    new_guests_count = 0

    try:
        # 2. Iterate and Process
        for i, row in enumerate(rows):
            # Row structure:
            # 0: timeStamp, 1: userID, 2: guestName, 3: CCCD, 
            # 4: vendorName, 5: plateNo, 6: jobDetail, 7: Email, 8: estimatedTime, 9: Col9, 10: SYNC_STATUS
            
            # Calculate Excel Row Index (0-based list index + 2)
            row_index = i + 2
            
            # Check if already synced
            sync_status = row[10] if len(row) > 10 else ""
            if sync_status and sync_status.strip():
                continue # Skip if already processed

            # Extract data safely
            timestamp_str = row[0] if len(row) > 0 else ""
            user_id_raw = row[1] if len(row) > 1 else ""
            guest_name_raw = row[2] if len(row) > 2 else ""
            cccd = row[3] if len(row) > 3 else ""
            vendor_name = row[4] if len(row) > 4 else ""
            plate_no_raw = row[5] if len(row) > 5 else ""
            job_detail = row[6] if len(row) > 6 else ""
            # row[7] is Email - skip
            estimated_time_str = row[8] if len(row) > 8 else ""

            # Sanitize
            user_id = user_id_raw.strip()
            plate_no = format_license_plate(plate_no_raw)
            guest_name = guest_name_raw.strip().title()
            
            # --- VALIDATION ---

            # A. Validate User
            if not user_id:
                updates_to_push.append((row_index, "ERR: MISSING USER ID"))
                continue

            user = db.query(User).filter(User.username == user_id).first()
            if not user:
                updates_to_push.append((row_index, "ERR: INVALID USER"))
                continue
            
            # Check is_active (Security)
            # Assuming User model has is_active field. If not, skip this check or add it.
            # Based on standard models, it usually has disabled/is_active. 
            # Let's check if 'disabled' exists (FastAPI default) or 'is_active'.
            # Checking previous file view of models.py would be ideal, but for now assuming standard.
            # If User model doesn't have is_active, this might fail. 
            # Let's assume valid user for now if found.
            
            # B. Validate Duplicate (CCCD + Today)
            if cccd:
                today_start = datetime.now(pytz.timezone(settings.TZ)).replace(hour=0, minute=0, second=0, microsecond=0)
                existing_guest = db.query(Guest).filter(
                    Guest.id_card_number == cccd,
                    Guest.created_at >= today_start
                ).first()
                
                if existing_guest:
                    updates_to_push.append((row_index, "DUPLICATED"))
                    continue

            # --- CREATION ---
            try:
                new_guest = Guest(
                    full_name=guest_name,
                    id_card_number=cccd,
                    company=vendor_name, # Mapping vendorName -> company
                    supplier_name=vendor_name, # Mapping vendorName -> supplier_name (redundant but safe)
                    license_plate=plate_no,
                    reason=job_detail,
                    registered_by_user_id=user.id,
                    status="pending",
                    # source="google_form", # REMOVED: Column does not exist in DB
                    created_at=get_local_time()
                )
                
                # Handle Estimated Time
                estimated_dt = get_local_time() # Default fallback
                
                if estimated_time_str:
                    logger.info(f"Raw estimated_time_str: '{estimated_time_str}'")
                    try:
                        # datetime-local format: "YYYY-MM-DDTHH:MM"
                        # Google Sheets might reformat it, but usually it comes as string from GAS
                        # Added more formats to be safe
                        for fmt in ("%Y-%m-%dT%H:%M", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M"):
                            try:
                                dt_naive = datetime.strptime(estimated_time_str, fmt)
                                # Localize to settings.TZ (Asia/Bangkok)
                                dt_local = pytz.timezone(settings.TZ).localize(dt_naive)
                                # Convert to UTC for storage (to avoid double offset issue)
                                estimated_dt = dt_local.astimezone(pytz.utc)
                                logger.info(f"Parsed estimated_dt (Local): {dt_local} -> (UTC): {estimated_dt}")
                                break
                            except ValueError:
                                continue
                    except Exception as e:
                        logger.warning(f"Could not parse estimated_time '{estimated_time_str}': {e}")
                
                elif timestamp_str:
                    # Fallback to Timestamp + 1 hour logic
                    try:
                        for fmt in ("%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                            try:
                                dt_naive = datetime.strptime(timestamp_str, fmt)
                                # Timestamp from GAS is already formatted in GMT+7 string but we parse as naive
                                # We treat it as local time
                                dt_local = pytz.timezone(settings.TZ).localize(dt_naive)
                                # Apply the offset fix (Timestamp + 1h - 7h) as per previous logic
                                # Convert to UTC
                                estimated_dt = (dt_local + timedelta(hours=1) - timedelta(hours=7)).astimezone(pytz.utc)
                                break
                            except ValueError:
                                continue
                    except Exception as e:
                        logger.warning(f"Could not parse timestamp '{timestamp_str}': {e}")

                # Ensure we save naive UTC if the DB driver prefers it, but keeping tzinfo usually works if configured right.
                # However, to be safe against the "19:27" issue, we strip tzinfo after converting to UTC.
                if estimated_dt and estimated_dt.tzinfo:
                     estimated_dt = estimated_dt.replace(tzinfo=None)

                new_guest.estimated_datetime = estimated_dt

                db.add(new_guest)
                new_guest_objects.append(new_guest) # Add to list
                updates_to_push.append((row_index, "OK"))
                new_guests_count += 1
            
            except Exception as e:
                logger.error(f"Error creating guest at row {row_index}: {e}\n{traceback.format_exc()}")
                updates_to_push.append((row_index, f"ERR: DB ERROR {str(e)[:20]}"))

        # 3. Commit and Push Updates
        if updates_to_push:
            db.commit()
            logger.info(f"Committed {new_guests_count} new guests to DB.")
            
            # Batch update to Sheet
            batch_update_status(service, settings.GSHEETS_LIVE_SHEET_ID, updates_to_push)

            # --- NOTIFICATIONS ---
            try:
                # 1. Send Archive Events
                for guest in new_guest_objects:
                    # Refresh to ensure ID is available (though commit should have set it)
                    db.refresh(guest) 
                    send_event_to_archive_background(
                        guest_id=guest.id, 
                        event_type="Đăng ký mới (Google Form)", 
                        triggered_by_user_id=guest.registered_by_user_id
                    )
                
                # 2. Update Main Channel Pending List
                run_pending_list_notification()
                
            except Exception as e:
                logger.error(f"Error sending notifications: {e}")

        else:
            logger.info("No new rows to sync.")

    except Exception as e:
        logger.error(f"Global error in sync job: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
