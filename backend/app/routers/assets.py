# File: backend/app/routers/assets.py
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, UploadFile, File, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import logging
import io

from .. import models, schemas
from ..core.deps import get_db
from ..core.auth import get_current_user, require_roles
from ..models import get_local_time
from ..core.config import settings

router = APIRouter(
    prefix="/assets",
    tags=["Assets"]
)

logger = logging.getLogger(__name__)

# === ENDPOINT: [POST] /assets (Tạo mới) ===
@router.post("", response_model=schemas.AssetLogDisplay, status_code=201)
async def create_asset(
    asset_in: schemas.AssetLogCreate,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    try:
        from ..modules.asset.service import asset_service
        return asset_service.create_asset(db, asset_in, current_user, background_tasks)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    except Exception as e:
        logger.error(f"Error creating asset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not create asset")

# === ENDPOINT: [POST] /assets/{asset_id}/upload-image (Upload Asset Image) ===
@router.post("/{asset_id}/upload-image", response_model=schemas.AssetImageRead)
async def upload_asset_image(
    asset_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from ..modules.asset.service import asset_service
        content = await file.read()
        db_image = asset_service.upload_asset_image(db, asset_id, file.filename, content, current_user)
        if not db_image:
             raise HTTPException(status_code=404, detail="Không tìm thấy tài sản")
        return db_image
    except PermissionError:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập hoặc tài sản không thuộc về bạn")
    except Exception as e:
        logger.error(f"Error uploading image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Không thể tải ảnh lên")

# === ENDPOINT: [DELETE] /assets/images/{image_id} (Delete Asset Image) ===
@router.delete("/images/{image_id}")
def delete_asset_image(
    image_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from ..modules.asset.service import asset_service
        success = asset_service.delete_asset_image(db, image_id, current_user)
        if not success:
             raise HTTPException(status_code=404, detail="Không tìm thấy ảnh")
        return {"ok": True}
    except ValueError:
         raise HTTPException(status_code=500, detail="Ảnh lỗi (orphaned)")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Không có quyền xóa ảnh này")
    except Exception as e:
         logger.error(f"Error deleting image: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail="Lỗi server")

# === ENDPOINT 2: [GET] /assets (Trang Quản lý/Lịch sử) ===
@router.get("", response_model=List[schemas.AssetLogDisplay])
def get_assets(
    start_date: date = Query(None),
    end_date: date = Query(None),
    status: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    try:
        from ..modules.asset.service import asset_service
        return asset_service.get_assets(db, current_user, start_date, end_date, status, department)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    except Exception as e:
        logger.error(f"Error getting assets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi lấy danh sách tài sản")

# === ENDPOINT 3: [GET] /assets/guard-gate (Trang Bảo vệ) ===
@router.get("/guard-gate", response_model=List[schemas.AssetLogDisplay])
def get_assets_for_guard_gate(
    q: Optional[str] = Query(None),
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    try:
        from ..modules.asset.service import asset_service
        return asset_service.get_assets_for_guard_gate(db, current_user, q)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    except Exception as e:
        logger.error(f"Error getting guard gate assets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi lấy dữ liệu cổng bảo vệ")

# === ENDPOINT 4: [POST] /assets/{asset_id}/checkout (Bảo vệ Xác nhận RA) ===
@router.post("/{asset_id}/checkout", response_model=schemas.AssetLogDisplay)
async def confirm_asset_checkout(
    asset_id: int,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    try:
        from ..modules.asset.service import asset_service
        asset = asset_service.confirm_asset_checkout(db, asset_id, current_user, background_tasks)
        if not asset:
             raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi tài sản.")
        return asset
    except PermissionError:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error checking out asset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi check-out")

# === ENDPOINT 5: [POST] /assets/{asset_id}/checkin-back (Bảo vệ Xác nhận VỀ) ===
@router.post("/{asset_id}/checkin-back", response_model=schemas.AssetLogDisplay)
async def confirm_asset_return(
    asset_id: int,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    try:
        from ..modules.asset.service import asset_service
        asset = asset_service.confirm_asset_return(db, asset_id, current_user, background_tasks)
        if not asset:
             raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi tài sản.")
        return asset
    except PermissionError:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error returning asset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi check-in back")


# === Endpoints quản lý tài sản của staff ===

@router.get("/my-assets", response_model=List[schemas.AssetLogDisplay])
def get_my_assets(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from ..modules.asset.service import asset_service
        return asset_service.get_my_assets(db, current_user)
    except Exception as e:
        logger.error(f"Error getting my assets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi lấy danh sách tài sản của tôi")


@router.put("/{asset_id}", response_model=schemas.AssetLogDisplay)
def update_asset(
    asset_id: int,
    asset_update: schemas.AssetLogUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from ..modules.asset.service import asset_service
        asset = asset_service.update_asset(db, asset_id, asset_update, current_user)
        if not asset:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài sản")
        return asset
    except PermissionError:
        raise HTTPException(status_code=403, detail="Không có quyền sửa tài sản này")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating asset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi cập nhật tài sản")


@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from ..modules.asset.service import asset_service
        success = asset_service.delete_asset(db, asset_id, current_user)
        if not success:
             raise HTTPException(status_code=404, detail="Không tìm thấy tài sản")
        return {"message": "Đã xóa tài sản thành công"}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Không có quyền xóa tài sản này")
    except ValueError as e:
         raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting asset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi xóa tài sản")

# === EXPORT ENDPOINT ===
@router.get("/export/xlsx")
def export_assets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    start_date: str | None = Query(default=None, description="Ngày bắt đầu (YYYY-MM-DD)"),
    end_date: str | None = Query(default=None, description="Ngày kết thúc (YYYY-MM-DD)"),
    status: str | None = Query(default=None, description="Trạng thái: pending_out,checked_out,returned"),
    department: str | None = Query(default=None, description="Bộ phận")
):
    try:
        from ..modules.asset.service import asset_service
        output = asset_service.export_assets(db, current_user, start_date, end_date, status, department)
        headers = {
            'Content-Disposition': f'attachment; filename="so_theo_doi_tai_san_{get_local_time().strftime("%Y%m%d_%H%M")}.xlsx"'
        }
        return Response(content=output.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)
    except Exception as e:
        logger.error(f"Không thể tạo file Excel: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Không thể tạo file Excel.")
