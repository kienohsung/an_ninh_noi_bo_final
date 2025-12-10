import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app.core.database import SessionLocal
from backend.app.modules.purchasing.model import PurchasingImage, PurchasingLog
from sqlalchemy import select

def check_images():
    db = SessionLocal()
    try:
        stmt = select(PurchasingImage)
        images = db.scalars(stmt).all()
        print(f"Total images found: {len(images)}")
        for img in images:
            print(f"ID: {img.id}, Path: {img.image_path}, Type: {img.image_type}, Purchasing ID: {img.purchasing_id}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_images()
