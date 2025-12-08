from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from datetime import datetime
import pytz
import os
import shutil
import uuid
import logging
from typing import List, Tuple

from app import models
from app.core import config
from app.modules.security_event import schema as schemas

logger = logging.getLogger(__name__)

# Constants
SECURITY_EVENT_STATUS = "security_event"
EVENT_EMPLOYEE_CODE = "EVENT"
EVENT_QUANTITY = 1
MAX_IMAGES = 5

class SecurityEventService:
    @staticmethod
    def format_description_reason(detail: str, resolution: str) -> str:
        """Format detail và resolution thành chuỗi có cấu trúc để dễ parse sau này"""
        return f"[NỘI DUNG]\n{detail or 'N/A'}\n\n[HƯỚNG GIẢI QUYẾT]\n{resolution or 'N/A'}"

    @staticmethod
    def parse_description_reason(text: str) -> Tuple[str, str]:
        """Parse description_reason thành detail và resolution"""
        if not text:
            return 'N/A', 'N/A'
        
        try:
            parts = text.split('[HƯỚNG GIẢI QUYẾT]')
            detail = parts[0].replace('[NỘI DUNG]', '').strip()
            resolution = parts[1].strip() if len(parts) > 1 else 'N/A'
            return detail, resolution
        except:
            return text, 'N/A'

    def asset_log_to_security_event(self, asset: models.AssetLog) -> schemas.SecurityEventRead:
        """Convert AssetLog model sang SecurityEventRead schema"""
        detail, resolution = self.parse_description_reason(asset.description_reason)
        # Handle images - assuming conversion to dict or object compatible with schema
        # Since we use from_attributes=True, list of objects works if they match schema
        return schemas.SecurityEventRead(
            id=asset.id,
            title=asset.asset_description or '',
            occurred_at=asset.estimated_datetime,
            location=asset.destination or '',
            involved_parties=asset.department or '',
            detail=detail,
            resolution=resolution,
            reported_by_name=asset.registered_by.full_name if asset.registered_by else 'Unknown',
            created_at=asset.created_at,
            images=asset.images
        )

    def get_security_events(self, db: Session, limit: int = 5) -> List[schemas.SecurityEventRead]:
        events = db.query(models.AssetLog)\
            .options(joinedload(models.AssetLog.registered_by), joinedload(models.AssetLog.images))\
            .filter(models.AssetLog.status == SECURITY_EVENT_STATUS)\
            .order_by(desc(models.AssetLog.estimated_datetime))\
            .limit(limit)\
            .all()
        
        return [self.asset_log_to_security_event(event) for event in events]

    def create_security_event(self, db: Session, event_in: schemas.SecurityEventCreate, current_user: models.User) -> schemas.SecurityEventRead:
        # Xử lý timezone
        tz = pytz.timezone(config.settings.TZ)
        occurred_at = event_in.occurred_at
        if occurred_at and occurred_at.tzinfo is None:
            occurred_at = tz.localize(occurred_at)
        
        new_event = models.AssetLog(
            asset_description=event_in.title,
            estimated_datetime=occurred_at,
            destination=event_in.location,
            department=event_in.involved_parties or '',
            description_reason=self.format_description_reason(event_in.detail, event_in.resolution),
            status=SECURITY_EVENT_STATUS,
            quantity=EVENT_QUANTITY,
            employee_code=EVENT_EMPLOYEE_CODE,
            full_name=current_user.full_name,
            registered_by_user_id=current_user.id
        )
        
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        db.refresh(new_event, attribute_names=['registered_by', 'images'])
        
        return self.asset_log_to_security_event(new_event)

    def get_security_event(self, db: Session, event_id: int) -> schemas.SecurityEventRead:
        event = db.query(models.AssetLog)\
            .options(joinedload(models.AssetLog.registered_by), joinedload(models.AssetLog.images))\
            .filter(
                models.AssetLog.id == event_id,
                models.AssetLog.status == SECURITY_EVENT_STATUS
            )\
            .first()
        
        if not event:
            return None
        
        return self.asset_log_to_security_event(event)

    def update_security_event(self, db: Session, event_id: int, event_in: schemas.SecurityEventUpdate) -> schemas.SecurityEventRead:
        event = db.query(models.AssetLog)\
            .options(joinedload(models.AssetLog.registered_by), joinedload(models.AssetLog.images))\
            .filter(
                models.AssetLog.id == event_id,
                models.AssetLog.status == SECURITY_EVENT_STATUS
            )\
            .first()
        
        if not event:
            return None
        
        if event_in.title is not None:
            event.asset_description = event_in.title
            
        if event_in.occurred_at is not None:
            tz = pytz.timezone(config.settings.TZ)
            if event_in.occurred_at.tzinfo is None:
                event.estimated_datetime = tz.localize(event_in.occurred_at)
            else:
                event.estimated_datetime = event_in.occurred_at
                
        if event_in.location is not None:
            event.destination = event_in.location
            
        if event_in.involved_parties is not None:
            event.department = event_in.involved_parties
            
        if event_in.detail is not None or event_in.resolution is not None:
            current_detail, current_resolution = self.parse_description_reason(event.description_reason)
            new_detail = event_in.detail if event_in.detail is not None else current_detail
            new_resolution = event_in.resolution if event_in.resolution is not None else current_resolution
            event.description_reason = self.format_description_reason(new_detail, new_resolution)
        
        db.commit()
        db.refresh(event)
        
        return self.asset_log_to_security_event(event)

    def delete_security_event(self, db: Session, event_id: int) -> bool:
        event = db.query(models.AssetLog)\
            .filter(
                models.AssetLog.id == event_id,
                models.AssetLog.status == SECURITY_EVENT_STATUS
            )\
            .first()
        
        if not event:
            return False
        
        for image in event.images:
            try:
                if os.path.exists(image.image_path):
                    os.remove(image.image_path)
            except:
                pass
        
        db.delete(event)
        db.commit()
        return True

    def upload_image(self, db: Session, event_id: int, file_filename: str, file_file) -> dict:
        event = db.query(models.AssetLog)\
            .filter(
                models.AssetLog.id == event_id,
                models.AssetLog.status == SECURITY_EVENT_STATUS
            )\
            .first()
        
        if not event:
            raise ValueError("Event not found")
        
        current_count = db.query(models.AssetImage).filter(models.AssetImage.asset_id == event_id).count()
        if current_count >= MAX_IMAGES:
            raise ValueError(f"Limit reached: {MAX_IMAGES} images")
        
        upload_dir = os.path.join(config.settings.UPLOAD_DIR, "security_events", str(event_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        ext = os.path.splitext(file_filename)[1] if file_filename else '.jpg'
        filename = f"event_{event_id}_{timestamp}_{unique_id}{ext}"
        file_path = os.path.join(upload_dir, filename)
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file_file, buffer)
        except Exception as e:
            raise RuntimeError(f"Error saving file: {str(e)}")
        
        relative_path = os.path.join("security_events", str(event_id), filename).replace("\\", "/")
        new_image = models.AssetImage(
            asset_id=event_id,
            image_path=relative_path
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)
        
        return {
            "id": new_image.id,
            "image_path": new_image.image_path,
            "message": "Upload thành công"
        }

    def delete_image(self, db: Session, image_id: int) -> bool:
        image = db.query(models.AssetImage)\
            .join(models.AssetLog)\
            .filter(
                models.AssetImage.id == image_id,
                models.AssetLog.status == SECURITY_EVENT_STATUS
            )\
            .first()
        
        if not image:
            return False
        
        try:
            full_path = os.path.join(config.settings.UPLOAD_DIR, image.image_path) 
            if os.path.exists(full_path):
                os.remove(full_path)
            # Try removing from legacy path or just rely on image_path being relative to UPLOAD_DIR
        except:
            pass
        
        db.delete(image)
        db.commit()
        return True

security_event_service = SecurityEventService()
