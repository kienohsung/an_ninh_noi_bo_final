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
from sqlalchemy.orm import Session
from typing import List

from .. import models
from ..core.deps import get_db
from ..core.auth import require_roles
from ..modules.security_event import schema as schemas

router = APIRouter(
    prefix="/security-events",
    tags=["Security Events"]
)


@router.get("/", response_model=List[schemas.SecurityEventRead])
def get_security_events(
    limit: int = 5,
    current_user: models.User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db)
):
    from ..modules.security_event.service import security_event_service
    return security_event_service.get_security_events(db, limit)

@router.post("/", response_model=schemas.SecurityEventRead)
def create_security_event(
    event_in: schemas.SecurityEventCreate,
    current_user: models.User = Depends(require_roles("admin", "manager", "guard")),
    db: Session = Depends(get_db)
):
    from ..modules.security_event.service import security_event_service
    return security_event_service.create_security_event(db, event_in, current_user)

@router.get("/{event_id}", response_model=schemas.SecurityEventRead)
def get_security_event(
    event_id: int,
    current_user: models.User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db)
):
    from ..modules.security_event.service import security_event_service
    event = security_event_service.get_security_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    return event

@router.put("/{event_id}", response_model=schemas.SecurityEventRead)
def update_security_event(
    event_id: int,
    event_in: schemas.SecurityEventUpdate,
    current_user: models.User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db)
):
    from ..modules.security_event.service import security_event_service
    event = security_event_service.update_security_event(db, event_id, event_in)
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    return event

@router.delete("/{event_id}")
def delete_security_event(
    event_id: int,
    current_user: models.User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    from ..modules.security_event.service import security_event_service
    if not security_event_service.delete_security_event(db, event_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    return {"message": "Đã xóa sự kiện thành công"}

@router.post("/{event_id}/upload-image")
def upload_security_event_image(
    event_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(require_roles("admin", "manager", "guard")),
    db: Session = Depends(get_db)
):
    from ..modules.security_event.service import security_event_service
    
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file ảnh (JPEG, PNG, GIF, WebP)")
        
    try:
        return security_event_service.upload_image(db, event_id, file.filename, file.file)
    except ValueError as e:
         raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.delete("/images/{image_id}")
def delete_security_event_image(
    image_id: int,
    current_user: models.User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db)
):
    from ..modules.security_event.service import security_event_service
    if not security_event_service.delete_image(db, image_id):
         raise HTTPException(status_code=404, detail="Không tìm thấy ảnh")
    return {"message": "Đã xóa ảnh thành công"}
