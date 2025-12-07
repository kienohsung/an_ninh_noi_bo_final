# File: backend/app/routers/security_events.py
"""
Router cho Sự kiện An ninh (Security Events)
Sử dụng chiến lược Zero Migration - tái sử dụng bảng asset_log

Mapping:
- title -> asset_description
- occurred_at -> estimated_datetime  
- location -> destination
- involved_parties -> department
- detail + resolution -> description_reason (formatted)
- status = "security_event" (hardcode)
- quantity = 1 (hardcode)
- employee_code = "EVENT" (hardcode)
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List
import os
import shutil
from datetime import datetime
import pytz
import uuid

from .. import models
from ..deps import get_db
from ..auth import get_current_user, require_roles
from ..config import settings
from . import schemas

router = APIRouter(
    prefix="/security-events",
    tags=["Security Events"]
)

# === CONSTANTS ===
SECURITY_EVENT_STATUS = "security_event"
EVENT_EMPLOYEE_CODE = "EVENT"
EVENT_QUANTITY = 1
MAX_IMAGES = 5

# === HELPER FUNCTIONS ===

def format_description_reason(detail: str, resolution: str) -> str:
    """Format detail và resolution thành chuỗi có cấu trúc để dễ parse sau này"""
    return f"""[NỘI DUNG]
{detail or 'N/A'}

[HƯỚNG GIẢI QUYẾT]
{resolution or 'N/A'}"""


def parse_description_reason(text: str) -> tuple[str, str]:
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


def asset_log_to_security_event(asset: models.AssetLog) -> schemas.SecurityEventRead:
    """Convert AssetLog model sang SecurityEventRead schema"""
    detail, resolution = parse_description_reason(asset.description_reason)
    
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
        images=[schemas.AssetImageRead(id=img.id, image_path=img.image_path) for img in asset.images]
    )


# === ENDPOINT 1: GET /security-events (Danh sách) ===
@router.get("/", response_model=List[schemas.SecurityEventRead])
def get_security_events(
    limit: int = 5,
    current_user: models.User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách sự kiện an ninh.
    - Chỉ Admin và Manager được xem
    - Mặc định lấy 5 sự kiện mới nhất
    """
    events = db.query(models.AssetLog)\
        .options(joinedload(models.AssetLog.registered_by), joinedload(models.AssetLog.images))\
        .filter(models.AssetLog.status == SECURITY_EVENT_STATUS)\
        .order_by(desc(models.AssetLog.estimated_datetime))\
        .limit(limit)\
        .all()
    
    return [asset_log_to_security_event(event) for event in events]


# === ENDPOINT 2: POST /security-events (Tạo mới) ===
@router.post("/", response_model=schemas.SecurityEventRead)
def create_security_event(
    event_in: schemas.SecurityEventCreate,
    current_user: models.User = Depends(require_roles("admin", "manager", "guard")),
    db: Session = Depends(get_db)
):
    """
    Tạo sự kiện an ninh mới.
    - Admin, Manager, Guard có thể tạo (Staff không được)
    - Hardcode status = "security_event", quantity = 1, employee_code = "EVENT"
    """
    # Xử lý timezone
    tz = pytz.timezone(settings.TZ)
    occurred_at = event_in.occurred_at
    if occurred_at and occurred_at.tzinfo is None:
        occurred_at = tz.localize(occurred_at)
    
    # Map từ SecurityEvent sang AssetLog
    new_event = models.AssetLog(
        # Mapping fields
        asset_description=event_in.title,
        estimated_datetime=occurred_at,
        destination=event_in.location,
        department=event_in.involved_parties or '',
        description_reason=format_description_reason(event_in.detail, event_in.resolution),
        
        # Hardcoded values
        status=SECURITY_EVENT_STATUS,
        quantity=EVENT_QUANTITY,
        employee_code=EVENT_EMPLOYEE_CODE,
        
        # User info
        full_name=current_user.full_name,
        registered_by_user_id=current_user.id
    )
    
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    # Load relationships
    db.refresh(new_event)
    
    return asset_log_to_security_event(new_event)


# === ENDPOINT 3: GET /security-events/{id} (Chi tiết) ===
@router.get("/{event_id}", response_model=schemas.SecurityEventRead)
def get_security_event(
    event_id: int,
    current_user: models.User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db)
):
    """
    Xem chi tiết một sự kiện an ninh.
    - Chỉ Admin và Manager được xem
    """
    event = db.query(models.AssetLog)\
        .options(joinedload(models.AssetLog.registered_by), joinedload(models.AssetLog.images))\
        .filter(
            models.AssetLog.id == event_id,
            models.AssetLog.status == SECURITY_EVENT_STATUS
        )\
        .first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    
    return asset_log_to_security_event(event)

# === ENDPOINT 3.5: PUT /security-events/{id} (Cập nhật) ===
@router.put("/{event_id}", response_model=schemas.SecurityEventRead)
def update_security_event(
    event_id: int,
    event_in: schemas.SecurityEventUpdate,
    current_user: models.User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db)
):
    """
    Cập nhật thông tin sự kiện an ninh.
    - Chỉ Admin và Manager được sửa
    """
    event = db.query(models.AssetLog)\
        .options(joinedload(models.AssetLog.registered_by), joinedload(models.AssetLog.images))\
        .filter(
            models.AssetLog.id == event_id,
            models.AssetLog.status == SECURITY_EVENT_STATUS
        )\
        .first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    
    # Update fields if provided
    if event_in.title is not None:
        event.asset_description = event_in.title
        
    if event_in.occurred_at is not None:
        tz = pytz.timezone(settings.TZ)
        if event_in.occurred_at.tzinfo is None:
            event.estimated_datetime = tz.localize(event_in.occurred_at)
        else:
            event.estimated_datetime = event_in.occurred_at
            
    if event_in.location is not None:
        event.destination = event_in.location
        
    if event_in.involved_parties is not None:
        event.department = event_in.involved_parties
        
    # Handle detail & resolution update
    # Need to re-format description_reason if either changes
    if event_in.detail is not None or event_in.resolution is not None:
        current_detail, current_resolution = parse_description_reason(event.description_reason)
        new_detail = event_in.detail if event_in.detail is not None else current_detail
        new_resolution = event_in.resolution if event_in.resolution is not None else current_resolution
        event.description_reason = format_description_reason(new_detail, new_resolution)
    
    db.commit()
    db.refresh(event)
    
    return asset_log_to_security_event(event)


# === ENDPOINT 4: DELETE /security-events/{id} (Xóa) ===
@router.delete("/{event_id}")
def delete_security_event(
    event_id: int,
    current_user: models.User = Depends(require_roles("admin")),  # Chỉ Admin
    db: Session = Depends(get_db)
):
    """
    Xóa sự kiện an ninh.
    - CHỈ ADMIN được xóa để tránh phi tang sự kiện
    """
    event = db.query(models.AssetLog)\
        .filter(
            models.AssetLog.id == event_id,
            models.AssetLog.status == SECURITY_EVENT_STATUS
        )\
        .first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    
    # Xóa ảnh liên quan (nếu có)
    for image in event.images:
        try:
            if os.path.exists(image.image_path):
                os.remove(image.image_path)
        except:
            pass
    
    db.delete(event)
    db.commit()
    
    return {"message": "Đã xóa sự kiện thành công"}


# === ENDPOINT 5: POST /security-events/{id}/upload-image (Upload ảnh) ===
@router.post("/{event_id}/upload-image")
def upload_security_event_image(
    event_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(require_roles("admin", "manager", "guard")),
    db: Session = Depends(get_db)
):
    """
    Upload ảnh cho sự kiện an ninh.
    - Admin, Manager, Guard có thể upload
    - Tối đa 5 ảnh/sự kiện
    """
    # Verify event exists
    event = db.query(models.AssetLog)\
        .filter(
            models.AssetLog.id == event_id,
            models.AssetLog.status == SECURITY_EVENT_STATUS
        )\
        .first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    
    # Check image limit
    current_count = db.query(models.AssetImage).filter(models.AssetImage.asset_id == event_id).count()
    if current_count >= MAX_IMAGES:
        raise HTTPException(status_code=400, detail=f"Đã đạt giới hạn {MAX_IMAGES} ảnh")
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file ảnh (JPEG, PNG, GIF, WebP)")
    
    # Create upload directory
    upload_dir = os.path.join(settings.UPLOAD_DIR, "security_events", str(event_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:6]
    ext = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
    filename = f"event_{event_id}_{timestamp}_{unique_id}{ext}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lưu file: {str(e)}")
    
    # Create database record (reuse AssetImage table)
    # CRITICAL: Lưu relative path để frontend có thể build URL
    relative_path = os.path.join("security_events", str(event_id), filename).replace("\\", "/")
    new_image = models.AssetImage(
        asset_id=event_id,
        image_path=relative_path  # Changed from file_path to relative_path
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    
    return {
        "id": new_image.id,
        "image_path": new_image.image_path,
        "message": "Upload ảnh thành công"
    }


# === ENDPOINT 6: DELETE /security-events/images/{image_id} (Xóa ảnh) ===
@router.delete("/images/{image_id}")
def delete_security_event_image(
    image_id: int,
    current_user: models.User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db)
):
    """
    Xóa ảnh của sự kiện an ninh.
    - Admin và Manager có thể xóa
    """
    image = db.query(models.AssetImage)\
        .join(models.AssetLog)\
        .filter(
            models.AssetImage.id == image_id,
            models.AssetLog.status == SECURITY_EVENT_STATUS
        )\
        .first()
    
    if not image:
        raise HTTPException(status_code=404, detail="Không tìm thấy ảnh")
    
    # Delete file
    try:
        if os.path.exists(image.image_path):
            os.remove(image.image_path)
    except:
        pass
    
    db.delete(image)
    db.commit()
    
    return {"message": "Đã xóa ảnh thành công"}
