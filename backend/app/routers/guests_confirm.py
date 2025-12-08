# File: backend/app/routers/guests_confirm.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from .. import models, schemas
from ..core.deps import get_db
from ..core.auth import require_roles, get_current_user

router = APIRouter(prefix="/guests", tags=["guests-confirm"])
logger = logging.getLogger(__name__)

@router.post("/{guest_id}/confirm-in", dependencies=[Depends(require_roles("admin","manager","guard","staff"))])
def confirm_in(guest_id: int, bg: BackgroundTasks, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    from ..modules.guest.service import guest_service
    guest = guest_service.confirm_check_in(db, guest_id, user, bg)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return schemas.GuestRead.model_validate(guest)

@router.post("/{guest_id}/confirm-out", dependencies=[Depends(require_roles("admin","manager","guard","staff"))])
def confirm_out(guest_id: int, bg: BackgroundTasks, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """
    Xác nhận khách đã rời khỏi cổng (Check-out).
    Chuyển trạng thái từ 'checked_in' sang 'checked_out'.
    """
    from ..modules.guest.service import guest_service
    guest = guest_service.confirm_check_out(db, guest_id, user, bg)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return schemas.GuestRead.model_validate(guest)
