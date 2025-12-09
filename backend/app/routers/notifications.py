from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..core.deps import get_db
from ..core.auth import get_current_user
from .. import models
from ..modules.notification import schema as schemas
from ..modules.notification.model import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/unread", response_model=List[schemas.NotificationRead])
def get_unread_notifications(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """
    Get all unread notifications for the current user.
    """
    notifications = db.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.is_read == False
    ).order_by(Notification.created_at.desc()).all()
    return notifications

@router.post("/{notification_id}/read", response_model=schemas.NotificationRead)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """
    Mark a notification as read.
    """
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user.id
    ).first()
    
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif
