# File: backend/app/routers/long_term_guests.py
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import date
from typing import List
import logging  # Thêm logging cho Cải tiến 1

from .. import models, schemas
from ..core.deps import get_db
from ..core.auth import get_current_user
from ..models import get_local_time

router = APIRouter(prefix="/long-term-guests", tags=["long-term-guests"])

@router.post("/", response_model=schemas.LongTermGuestRead)
def create_long_term_guest(
    payload: schemas.LongTermGuestCreate, 
    db: Session = Depends(get_db), 
    user: models.User = Depends(get_current_user)
):
    try:
        from ..modules.guest.service import long_term_guest_service
        return long_term_guest_service.create_long_term_guest(db, payload, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[schemas.LongTermGuestReadWithUser])
def get_long_term_guests(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    from ..modules.guest.service import long_term_guest_service
    results = long_term_guest_service.get_long_term_guests(db, user)
    
    # Manually construct response to include user info
    response_data = []
    for item in results:
        data = schemas.LongTermGuestRead.model_validate(item).model_dump()
        data['registered_by_name'] = item.registered_by.full_name if item.registered_by else 'N/A'
        response_data.append(data)
        
    return response_data

@router.put("/{guest_id}", response_model=schemas.LongTermGuestRead)
def update_long_term_guest(
    guest_id: int, 
    payload: schemas.LongTermGuestUpdate, 
    db: Session = Depends(get_db), 
    user: models.User = Depends(get_current_user)
):
    from ..modules.guest.service import long_term_guest_service
    try:
        guest = long_term_guest_service.update_long_term_guest(db, guest_id, payload, user)
        if not guest:
            raise HTTPException(status_code=404, detail="Long-term guest not found")
        return guest
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/cleanup")
def cleanup_old_long_term_guests(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    from ..modules.guest.service import long_term_guest_service
    try:
        deleted_count = long_term_guest_service.cleanup_old_long_term_guests(db, user)
        logging.info(f"User {user.username} deleted {deleted_count} expired long-term guests")
        return {"deleted_count": deleted_count, "message": "Success"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.delete("/{guest_id}", status_code=204)
def delete_long_term_guest(
    guest_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    from ..modules.guest.service import long_term_guest_service
    try:
        if not long_term_guest_service.delete_long_term_guest(db, guest_id, user):
             raise HTTPException(status_code=404, detail="Long-term guest not found")
        return Response(status_code=204)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))




