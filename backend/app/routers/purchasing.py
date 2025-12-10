# File: backend/app/routers/purchasing.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import logging

from .. import models
from ..core.deps import get_db
from ..core.auth import get_current_user, require_roles
from ..models import get_local_time
from ..modules.purchasing import schema as schemas

router = APIRouter(
    prefix="/purchasing",
    tags=["Purchasing"]
)

logger = logging.getLogger(__name__)

# === ENDPOINTS ===

@router.get("", response_model=List[schemas.PurchasingLogRead])
def get_purchasing_list(
    start_date: date = Query(None),
    end_date: date = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        from ..modules.purchasing.service import purchasing_service
        return purchasing_service.get_purchasing_list(db, start_date, end_date, category, status)
    except Exception as e:
        logger.error(f"Error getting purchasing list: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving purchasing list")

@router.post("", response_model=schemas.PurchasingLogRead)
def create_purchasing(
    payload: schemas.PurchasingLogCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        from ..modules.purchasing.service import purchasing_service
        return purchasing_service.create_purchasing(db, payload)
    except Exception as e:
        logger.error(f"Error creating purchasing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not create purchasing request")

@router.put("/{purchasing_id}", response_model=schemas.PurchasingLogRead)
def update_purchasing(
    purchasing_id: int,
    payload: schemas.PurchasingLogUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        from ..modules.purchasing.service import purchasing_service
        p = purchasing_service.update_purchasing(db, purchasing_id, payload)
        if not p:
            raise HTTPException(status_code=404, detail="Purchasing request not found")
        return p
    except Exception as e:
        logger.error(f"Error updating purchasing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not update purchasing request")

@router.delete("/{purchasing_id}")
def delete_purchasing(
    purchasing_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Assuming auth required
):
    try:
        from ..modules.purchasing.service import purchasing_service
        if not purchasing_service.delete_purchasing(db, purchasing_id):
            raise HTTPException(status_code=404, detail="Purchasing request not found")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error deleting purchasing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not delete purchasing request")

@router.post("/{purchasing_id}/images", response_model=schemas.PurchasingImageRead)
async def upload_purchasing_image(
    purchasing_id: int,
    type: str = Query(..., regex="^(request|quote|invoice|other|delivery)$"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        from ..modules.purchasing.service import purchasing_service
        content = await file.read()
        image = purchasing_service.upload_purchasing_image(db, purchasing_id, type, file.filename, content)
        if not image:
            raise HTTPException(status_code=404, detail="Purchasing request not found")
        return image
    except Exception as e:
        logger.error(f"Error uploading image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not upload image")

@router.delete("/images/{image_id}")
def delete_purchasing_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        from ..modules.purchasing.service import purchasing_service
        if not purchasing_service.delete_purchasing_image(db, image_id):
            raise HTTPException(status_code=404, detail="Image not found")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error deleting image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not delete image")

@router.post("/{purchasing_id}/receive", response_model=schemas.PurchasingLogRead)
def receive_purchasing(
    purchasing_id: int,
    note: str = Body("", embed=True),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        from ..modules.purchasing.service import purchasing_service
        p = purchasing_service.receive_purchasing(db, purchasing_id, note)
        if not p:
            raise HTTPException(status_code=404, detail="Purchasing request not found")
        return p
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error receiving purchasing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not receive purchasing")

@router.get("/export/xlsx", dependencies=[Depends(require_roles("admin", "manager", "staff"))])
def export_purchasing_logs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    start_date: str | None = Query(default=None, description="Ngày bắt đầu (YYYY-MM-DD)"),
    end_date: str | None = Query(default=None, description="Ngày kết thúc (YYYY-MM-DD)"),
    department: str | None = Query(default=None, description="Bộ phận đề xuất"),
    status: str | None = Query(default=None, description="Trạng thái")
):
    try:
        from ..modules.purchasing.service import purchasing_service
        output = purchasing_service.export_purchasing_logs(db, start_date, end_date, department, status)
        
        filename = f"bao_cao_mua_sam_{get_local_time().strftime('%Y%m%d_%H%M')}.xlsx"
        headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
        return Response(content=output.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

    except Exception as e:
        logger.error(f"Cannot export purchasing logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Cannot export Excel file.")
