import sys
import os
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import datetime

# Setup path
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

from app.core.database import SessionLocal
from app.modules.guest.service import guest_service
from app.modules.asset.service import asset_service
from app import models, schemas
from app.core import config

# Dummy background task
class MockBackgroundTasks:
    def add_task(self, func, *args, **kwargs):
        print(f"[MockBG] Queued task: {func.__name__} with args: {args}")

def test_guest_flow(db: Session, user: models.User):
    print("\n--- Testing Guest Flow ---")
    mock_bg = MockBackgroundTasks()
    
    # 1. Create Guest
    guest_in = schemas.GuestCreate(
        full_name="Test Guest A",
        estimated_datetime=datetime.now(),
        reason="Test Visit"
    )
    guest = guest_service.create_guest(db, guest_in, user.id, mock_bg)
    print(f"✅ Created Guest: ID={guest.id}, Name={guest.full_name}")
    
    # 2. Check-in (confirm)
    guest = guest_service.confirm_check_in(db, guest.id, user, mock_bg)
    print(f"✅ Guest Checked In: Status={guest.status}, Time={guest.check_in_time}")
    
    # 3. Check-out
    guest = guest_service.confirm_check_out(db, guest.id, user, mock_bg)
    print(f"✅ Guest Checked Out: Status={guest.status}, Time={guest.check_out_time}")

    # Clean up
    db.delete(guest)
    db.commit()
    print("✅ Guest Cleaned up")

def test_asset_flow(db: Session, user: models.User):
    print("\n--- Testing Asset Flow ---")
    mock_bg = MockBackgroundTasks()

    # 1. Create Asset
    asset_in = schemas.AssetLogCreate(
        asset_description="Test Laptop",
        quantity=1,
        description_reason="Work",
        destination="Office",
        receiver_name="Test Receiver",
        department="IT",
        expected_return_date=datetime.now().date()
    )
    asset = asset_service.create_asset(db, asset_in, user, mock_bg)
    print(f"✅ Created Asset: ID={asset.id}, Desc={asset.asset_description}")

    # 2. Guard Checkout
    asset = asset_service.confirm_asset_checkout(db, asset.id, user, mock_bg)
    print(f"✅ Asset Checkout Confirmed: Status={asset.status}")

    # 3. Guard Return (Check-in back)
    asset = asset_service.confirm_asset_return(db, asset.id, user, mock_bg)
    print(f"✅ Asset Return Confirmed: Status={asset.status}")

    # Clean up
    db.delete(asset)
    db.commit()
    print("✅ Asset Cleaned up")

def main():
    db = SessionLocal()
    try:
        # Get Admin User for testing
        admin = db.query(models.User).filter(models.User.username == config.settings.ADMIN_USERNAME).first()
        if not admin:
            print("❌ Admin user not found. Run calling code to seed DB first.")
            return

        test_guest_flow(db, admin)
        test_asset_flow(db, admin)
        
        print("\n✅✅ SUCCESS: All Core Flows Verified!")
    except Exception as e:
        print(f"\n❌❌ FAILURE: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
