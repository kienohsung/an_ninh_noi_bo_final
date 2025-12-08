# File: backend/app/routers/print_tracking.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..core.database import get_db
from ..core.auth import get_current_user

router = APIRouter(
    prefix="/assets",
    tags=["Assets - Print Tracking"]
)

@router.post("/{asset_id}/increment-print-count", response_model=schemas.AssetLogDisplay)
def increment_print_count(
    asset_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Increment print count for an asset.
    Called when user prints the asset form.
    """
    # Check permissions (all authenticated users can print)
    if current_user.role not in ["admin", "manager", "staff", "guard"]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    
    from ..modules.asset.service import asset_service
    db_asset = asset_service.increment_print_count(db, asset_id, current_user)
    
    if not db_asset:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài sản")
    
    return db_asset
