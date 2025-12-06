# File: backend/app/routers/print_tracking.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user

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
    
    # Get asset
    db_asset = db.get(models.AssetLog, asset_id)
    
    if not db_asset:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài sản")
    
    # Increment print count
    db_asset.print_count += 1
    db.commit()
    db.refresh(db_asset)
    
    return db_asset
