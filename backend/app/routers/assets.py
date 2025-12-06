# File: backend/app/routers/assets.py
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, or_
from typing import List, Optional
from datetime import datetime, date
import logging
import uuid
import os

from .. import models, schemas
from ..database import get_db
from ..utils.notifications import send_telegram_message, send_asset_event_to_archive_background  # CẢI TIẾN 4
from ..auth import get_current_user
from ..config import settings

router = APIRouter(
    prefix="/assets",
    tags=["Assets"]
)

# === ENDPOINT 1: [POST] /assets (Tạo mới) ===
@router.post("", response_model=schemas.AssetLogDisplay, status_code=201)
async def create_asset(
    asset_in: schemas.AssetLogCreate,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Endpoint cho Staff (hoặc cao hơn) đăng ký một tài sản mang ra NG ngoài.
    """
    # Kiểm tra role thủ công
    if current_user.role not in ["admin", "manager", "staff"]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    
    # === TÍNH NĂNG MỚI: Cho phép tài sản KHÔNG hoàn lại (estimated_datetime có thể null) ===
    # Không còn validate bắt buộc estimated_datetime
    # === KẾT THÚC ===
    
    # Tạo bản ghi CSDL - explicitly map all fields to avoid schema mismatch
    db_asset = models.AssetLog(
        registered_by_user_id=current_user.id,
        full_name=current_user.full_name,
        employee_code=current_user.username,
        department=asset_in.department,
        destination=asset_in.destination,
        description_reason=asset_in.description_reason,
        asset_description=asset_in.asset_description,  # FIX: Use correct field
        quantity=asset_in.quantity,
        expected_return_date=asset_in.expected_return_date,
        estimated_datetime=asset_in.estimated_datetime,  # Có thể null cho tài sản không hoàn lại
        vietnamese_manager_name=asset_in.vietnamese_manager_name,  # FIX: Add manager names
        korean_manager_name=asset_in.korean_manager_name,  # FIX: Add manager names
        status=models.ASSET_STATUS_PENDING_OUT,
        created_at=models.get_local_time()
    )
    
    # === ĐỒNG BỘ DỮ LIỆU: Auto-sync expected_return_date từ estimated_datetime ===
    # Đảm bảo Reports không thiếu dữ liệu (Reports query dựa trên expected_return_date)
    # Frontend chỉ gửi estimated_datetime, backend tự động extract ngày
    if asset_in.estimated_datetime and not asset_in.expected_return_date:
        db_asset.expected_return_date = asset_in.estimated_datetime.date()
    # === KẾT THÚC ĐỒNG BỘ ===
    
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)

    # Gửi thông báo Telegram
    try:
        msg = f"""
[ASSET PENDING] - CÓ HÀNG CHỜ RA
- Người ĐK: {current_user.full_name}
- Bộ phận: {db_asset.department}
- Nơi đến: {db_asset.destination}
- Số lượng: {db_asset.quantity}
- Mô tả: {db_asset.description_reason}
- Dự kiến về: {db_asset.expected_return_date.strftime('%d/%m/%Y') if db_asset.expected_return_date else 'Không về'}
        """
        background_tasks.add_task(send_telegram_message, msg, "GUARD")
    except Exception as e:
        print(f"Telegram notification failed for new asset: {e}")
    
    # === CẢI TIẾN 4: Gửi thông báo đến kênh lưu trữ ===
    background_tasks.add_task(
        send_asset_event_to_archive_background,
        db_asset.id,
        "Đăng ký tài sản mới",
        current_user.id
    )
    # === KẾT THÚC CẢI TIẾN 4 ===
    
    # Tải lại relationship để response
    db.refresh(db_asset, attribute_names=['registered_by'])
    return db_asset

# === ENDPOINT: [POST] /assets/{asset_id}/upload-image (Upload Asset Image) ===
@router.post("/{asset_id}/upload-image", response_model=schemas.AssetImageRead)
async def upload_asset_image(
    asset_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an image for an asset.
    """
    logger = logging.getLogger(__name__)
    
    # Check permissions
    if current_user.role not in ["admin", "manager", "staff"]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    
    # Check if asset exists
    db_asset = db.get(models.AssetLog, asset_id)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài sản")
    
    # Check if user owns this asset (for staff role)
    if current_user.role == "staff" and db_asset.registered_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Không có quyền tải ảnh cho tài sản này")
    
    try:
        # Generate unique filename
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        
        # Save to assets directory
        save_path = os.path.join(settings.UPLOAD_DIR, "assets", unique_filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Write file
        with open(save_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Create database record
        db_image = models.AssetImage(
            asset_id=asset_id,
            image_path=f"assets/{unique_filename}"
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        
        return db_image
    except Exception as e:
        logger.error(f"Could not upload image for asset {asset_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Không thể tải ảnh lên")

# === HELPER FUNCTION: Archive Image ===
def _archive_asset_image(image_path: str):
    """Archive an asset image file."""
    logger = logging.getLogger(__name__)
    try:
        archive_dir = os.path.join(settings.UPLOAD_DIR, "archived_assets")
        os.makedirs(archive_dir, exist_ok=True)
        
        source_path = os.path.join(settings.UPLOAD_DIR, image_path)
        if os.path.exists(source_path):
            file_name = os.path.basename(image_path)
            dest_path = os.path.join(archive_dir, file_name)
            # Handle duplicate filenames
            if os.path.exists(dest_path):
                dest_path = os.path.join(archive_dir, f"{uuid.uuid4()}_{file_name}")
            os.rename(source_path, dest_path)
            logger.info(f"Archived asset image from {source_path} to {dest_path}")
    except Exception as e:
        logger.error(f"Could not archive asset image file {image_path}: {e}")

# === ENDPOINT: [DELETE] /assets/images/{image_id} (Delete Asset Image) ===
@router.delete("/images/{image_id}")
def delete_asset_image(
    image_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an asset image.
    """
    logger = logging.getLogger(__name__)
    
    # Check permissions
    if current_user.role not in ["admin", "manager", "staff"]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    
    # Get image with asset relationship
    db_image = db.query(models.AssetImage).options(joinedload(models.AssetImage.asset)).get(image_id)
    
    if not db_image:
        raise HTTPException(status_code=404, detail="Không tìm thấy ảnh")
    
    asset = db_image.asset
    if not asset:
        raise HTTPException(status_code=500, detail="Ảnh không có tài sản liên kết")
    
    # Check if user owns this asset (for staff role)
    is_admin_or_manager = current_user.role in ("admin", "manager")
    is_owner = asset.registered_by_user_id == current_user.id
    
    if not (is_admin_or_manager or is_owner):
        raise HTTPException(status_code=403, detail="Không có quyền xóa ảnh này")
    
    # Archive the image file
    _archive_asset_image(db_image.image_path)
    
    # Delete database record
    db.delete(db_image)
    db.commit()
    
    return {"ok": True}

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
    """
    Endpoint cho trang Quản lý/Lịch sử tài sản (cho Manager/Admin/Staff).
    Hỗ trợ lọc theo ngày, trạng thái, bộ phận.
    """
    # Kiểm tra role thủ công
    if current_user.role not in ["admin", "manager", "staff"]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")

    query = (
        select(models.AssetLog)
        .options(joinedload(models.AssetLog.registered_by))
        .options(joinedload(models.AssetLog.check_out_by))
        .options(joinedload(models.AssetLog.check_in_back_by))
        .options(joinedload(models.AssetLog.images))
        .order_by(models.AssetLog.created_at.desc())
    )

    if start_date:
        start_dt = datetime.combine(start_date, datetime.min.time())
        query = query.filter(models.AssetLog.created_at >= start_dt)
    if end_date:
        end_dt = datetime.combine(end_date, datetime.max.time())
        query = query.filter(models.AssetLog.created_at <= end_dt)
    
    if status:
        query = query.filter(models.AssetLog.status == status)
    
    if department:
        query = query.filter(models.AssetLog.department.ilike(f"%{department}%"))

    # Logic phân quyền: Staff chỉ thấy của mình
    if current_user.role == 'staff':
        query = query.filter(models.AssetLog.registered_by_user_id == current_user.id)

    results = db.scalars(query).unique().all()
    return results

# === ENDPOINT 3: [GET] /assets/guard-gate (Trang Bảo vệ) ===
@router.get("/guard-gate", response_model=List[schemas.AssetLogDisplay])
def get_assets_for_guard_gate(
    q: Optional[str] = Query(None),
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Endpoint cho trang Cổng Bảo Vệ.
    Chỉ lấy 2 trạng thái: PENDING_OUT và CHECKED_OUT.
    """
    # Kiểm tra role thủ công
    if current_user.role not in ["admin", "guard"]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    
    query = (
        select(models.AssetLog)
        .options(joinedload(models.AssetLog.registered_by))
        .options(joinedload(models.AssetLog.images))
        .filter(
            or_(
                models.AssetLog.status == models.ASSET_STATUS_PENDING_OUT,
                models.AssetLog.status == models.ASSET_STATUS_CHECKED_OUT
            )
        )
        .order_by(models.AssetLog.created_at.asc())
    )
    
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                models.AssetLog.destination.ilike(search_term),
                models.AssetLog.description_reason.ilike(search_term),
                models.AssetLog.registered_by.has(models.User.full_name.ilike(search_term))
            )
        )

    results = db.scalars(query).unique().all()
    return results

# === ENDPOINT 4: [POST] /assets/{asset_id}/checkout (Bảo vệ Xác nhận RA) ===
@router.post("/{asset_id}/checkout", response_model=schemas.AssetLogDisplay)
async def confirm_asset_checkout(
    asset_id: int,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Bảo vệ xác nhận tài sản đi RA.
    - Nếu tài sản CÓ hoàn lại: Chuyển 'pending_out' -> 'checked_out'
    - Nếu tài sản KHÔNG hoàn lại: Chuyển 'pending_out' -> 'returned' (lưu trữ ngay)
    """
    # Kiểm tra role thủ công
    if current_user.role not in ["admin", "guard"]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    
    db_asset = db.get(models.AssetLog, asset_id, options=[joinedload(models.AssetLog.registered_by)])
    
    if not db_asset:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi tài sản.")
    
    if db_asset.status != models.ASSET_STATUS_PENDING_OUT:
        raise HTTPException(status_code=400, detail=f"Tài sản đang ở trạng thái '{db_asset.status}', không thể xác nhận RA.")

    # === LOGIC MỚI: Kiểm tra tài sản có hoàn lại không ===
    is_returnable = db_asset.estimated_datetime is not None
    
    if is_returnable:
        # Tài sản CÓ hoàn lại: Chuyển sang checked_out (chờ về)
        db_asset.status = models.ASSET_STATUS_CHECKED_OUT
        db_asset.check_out_time = models.get_local_time()
        db_asset.check_out_by_user_id = current_user.id
        status_msg = "HÀNG ĐÃ RA"
    else:
        # Tài sản KHÔNG hoàn lại: Chuyển thẳng sang returned (lưu trữ luôn)
        db_asset.status = models.ASSET_STATUS_RETURNED
        db_asset.check_out_time = models.get_local_time()
        db_asset.check_out_by_user_id = current_user.id
        # Ghi cả thời gian về (cùng lúc) vì tài sản không quay lại
        db_asset.check_in_back_time = models.get_local_time()
        db_asset.check_in_back_by_user_id = current_user.id
        status_msg = "HÀNG ĐÃ RA (KHÔNG VỀ)"
    
    db.commit()

    # Gửi thông báo Telegram
    try:
        msg = f"""
[ASSET CHECK-OUT] - {status_msg}
- Bảo vệ: {current_user.full_name}
- Người ĐK: {db_asset.registered_by.full_name}
- Bộ phận: {db_asset.department}
- Nơi đến: {db_asset.destination}
- Mô tả: {db_asset.description_reason}
        """
        background_tasks.add_task(send_telegram_message, msg, "MANAGER")
    except Exception as e:
        print(f"Telegram notification failed for asset checkout: {e}")
    
    # === CẢI TIẾN 4: Gửi thông báo đến kênh lưu trữ ===
    background_tasks.add_task(
        send_asset_event_to_archive_background,
        db_asset.id,
        "Xác nhận ra cổng" if is_returnable else "Xác nhận ra cổng (không về)",
        current_user.id
    )
    # === KẾT THÚC CẢI TIẾN 4 ===
    
    db.refresh(db_asset, attribute_names=['registered_by', 'check_out_by'])
    return db_asset

# === ENDPOINT 5: [POST] /assets/{asset_id}/checkin-back (Bảo vệ Xác nhận VỀ) ===
@router.post("/{asset_id}/checkin-back", response_model=schemas.AssetLogDisplay)
async def confirm_asset_return(
    asset_id: int,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Bảo vệ xác nhận tài sản quay VỀ.
    Chuyển trạng thái từ 'checked_out' -> 'returned'.
    """
    # Kiểm tra role thủ công
    if current_user.role not in ["admin", "guard"]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    
    db_asset = db.get(models.AssetLog, asset_id, options=[joinedload(models.AssetLog.registered_by)])
    
    if not db_asset:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi tài sản.")
        
    if db_asset.status != models.ASSET_STATUS_CHECKED_OUT:
        raise HTTPException(status_code=400, detail=f"Tài sản đang ở trạng thái '{db_asset.status}', không thể xác nhận VỀ.")

    # Cập nhật trạng thái
    db_asset.status = models.ASSET_STATUS_RETURNED
    db_asset.check_in_back_time = models.get_local_time()
    db_asset.check_in_back_by_user_id = current_user.id
    db.commit()

    # Gửi thông báo Telegram
    try:
        msg = f"""
[ASSET RETURNED] - HÀNG ĐÃ VỀ
- Bảo vệ: {current_user.full_name}
- Người ĐK: {db_asset.registered_by.full_name}
- Bộ phận: {db_asset.department}
- Nơi đến: {db_asset.destination}
- Mô tả: {db_asset.description_reason}
        """
        background_tasks.add_task(send_telegram_message, msg, "MANAGER")
    except Exception as e:
        print(f"Telegram notification failed for asset return: {e}")
    
    # === CẢI TIẾN 4: Gửi thông báo đến kênh lưu trữ ===
    background_tasks.add_task(
        send_asset_event_to_archive_background,
        db_asset.id,
        "Xác nhận vào cổng",
        current_user.id
    )
    # === KẾT THÚC CẢI TIẾN 4 ===
    
    db.refresh(db_asset, attribute_names=['registered_by', 'check_in_back_by'])
    return db_asset


# === CẢI TIẾN 2: Endpoints quản lý tài sản của staff ===

@router.get("/my-assets", response_model=List[schemas.AssetLogDisplay])
def get_my_assets(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách tài sản đã đăng ký bởi user hiện tại.
    Dành cho staff xem tài sản của mình.
    """
    # Query assets của user
    query = (
        select(models.AssetLog)
        .options(joinedload(models.AssetLog.registered_by))
        .options(joinedload(models.AssetLog.check_out_by))
        .options(joinedload(models.AssetLog.check_in_back_by))
        .options(joinedload(models.AssetLog.images))
        .filter(models.AssetLog.registered_by_user_id == current_user.id)
        .order_by(models.AssetLog.created_at.desc())
    )
    
    results = db.scalars(query).unique().all()
    return results


@router.put("/{asset_id}", response_model=schemas.AssetLogDisplay)
def update_asset(
    asset_id: int,
    asset_update: schemas.AssetLogUpdate,  # Cần schema update
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update asset - chỉ cho phép user sở hữu hoặc admin/manager.
    Chỉ có thể sửa khi status = pending_out.
    """
    db_asset = db.get(models.AssetLog, asset_id)
    
    if not db_asset:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài sản")
    
    # Check permission
    if current_user.role not in ['admin', 'manager']:
        if db_asset.registered_by_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Không có quyền sửa tài sản này")
    
    # Chỉ cho phép sửa khi còn pending, trừ khi là admin
    if current_user.role != 'admin' and db_asset.status != models.ASSET_STATUS_PENDING_OUT:
        raise HTTPException(
            status_code=400, 
            detail="Chỉ có thể sửa tài sản đang ở trạng thái chờ ra cổng"
        )
    
    # Update fields
    update_data = asset_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(db_asset, key):
            setattr(db_asset, key, value)
    
    db.commit()
    db.refresh(db_asset)
    return db_asset


@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete asset - chỉ cho phép user sở hữu hoặc admin/manager.
    Chỉ có thể xóa khi status = pending_out.
    """
    db_asset = db.get(models.AssetLog, asset_id)
    
    if not db_asset:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài sản")
    
    # Check permission
    if current_user.role not in ['admin', 'manager']:
        if db_asset.registered_by_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Không có quyền xóa tài sản này")
    
    # Only allow delete if status is pending_out, unless admin
    if current_user.role != 'admin' and db_asset.status != models.ASSET_STATUS_PENDING_OUT:
        raise HTTPException(
            status_code=400, 
            detail="Chỉ có thể xóa tài sản đang ở trạng thái chờ ra cổng"
        )
    
    # Delete associated images first
    for image in db_asset.images:
        _archive_asset_image(image.image_path)
        db.delete(image)
    
    db.delete(db_asset)
    db.commit()
    
    return {"message": "Đã xóa tài sản thành công"}

# === KẾT THÚC CẢI TIẾN 2 ===

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
    """Export assets to Excel with custom formatting"""
    import pandas as pd
    import io
    import pytz
    from fastapi import Response
    from ..config import settings
    from ..models import get_local_time
    
    try:
        query = db.query(
            models.AssetLog,
            models.User.full_name.label("registered_by_name"),
            models.User.username.label("registered_by_username")
        ).join(
            models.User, models.AssetLog.registered_by_user_id == models.User.id
        ).options(joinedload(models.AssetLog.check_out_by)).options(joinedload(models.AssetLog.check_in_back_by))

        # Role-based filtering
        if current_user.role == "staff":
            query = query.filter(models.AssetLog.registered_by_user_id == current_user.id)
        
        # Date range filtering
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(models.AssetLog.created_at >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(models.AssetLog.created_at <= end_dt)
            except ValueError:
                pass

        # Status filtering
        if status:
            query = query.filter(models.AssetLog.status == status)

        # Department filtering
        if department:
            query = query.filter(models.AssetLog.department.ilike(f"%{department}%"))

        results = query.order_by(models.AssetLog.created_at.desc()).all()

        # Status labels
        status_labels = {
            'pending_out': 'Chờ ra',
            'checked_out': 'Đã ra (chờ về)',
            'returned': 'Đã hoàn trả'
        }
        
        data_to_export = []
        for idx, (asset, registered_by_name, registered_by_username) in enumerate(results, start=1):
            check_out_str = ""
            if asset.check_out_time:
                check_out_str = asset.check_out_time.astimezone(pytz.timezone(settings.TZ)).strftime("%d/%m/%Y %H:%M")
            
            check_in_back_str = ""
            if asset.check_in_back_time:
                check_in_back_str = asset.check_in_back_time.astimezone(pytz.timezone(settings.TZ)).strftime("%d/%m/%Y %H:%M")
            
            created_str = ""
            if asset.created_at:
                created_str = asset.created_at.astimezone(pytz.timezone(settings.TZ)).strftime("%d/%m/%Y %H:%M")
            
            estimated_str = ""
            if asset.estimated_datetime:
                try:
                    if asset.estimated_datetime.tzinfo is None:
                        estimated_str = pytz.utc.localize(asset.estimated_datetime).astimezone(pytz.timezone(settings.TZ)).strftime("%d/%m/%Y")
                    else:
                        estimated_str = asset.estimated_datetime.astimezone(pytz.timezone(settings.TZ)).strftime("%d/%m/%Y")
                except Exception:
                    try:
                        estimated_str = asset.estimated_datetime.strftime("%d/%m/%Y")
                    except Exception:
                        estimated_str = str(asset.estimated_datetime)
            
            data_to_export.append({
                "STT": idx,
                "Người ĐK": registered_by_name,
                "Bộ phận": asset.department or "",
                "Nơi đến": asset.destination or "",
                "Mô tả": asset.description_reason or "",
                "SL": asset.quantity,
                "Ngày ĐK": created_str,
                "Dự kiến về": estimated_str,
                "Giờ ra": check_out_str,
                "BV XN ra": asset.check_out_by.full_name if asset.check_out_by else "",
                "Giờ về": check_in_back_str,
                "BV XN về": asset.check_in_back_by.full_name if asset.check_in_back_by else "",
                "Trạng thái": status_labels.get(asset.status, asset.status)
            })

        df = pd.DataFrame(data_to_export)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Assets', startrow=1, header=True)
            
            workbook = writer.book
            worksheet = writer.sheets['Assets']
            
            # PAGE SETUP: A3 Landscape
            worksheet.set_paper(8)
            worksheet.set_landscape()
            
            # Title format
            title_format = workbook.add_format({
                'font_name': 'Courier New',
                'font_size': 15,
                'bold': True,
                'align': 'center',
                'valign': 'vcenter'
            })
            
            # Header format
            header_format = workbook.add_format({
                'font_name': 'Courier New',
                'font_size': 11,
                'bold': True,
                'align': 'left',
                'valign': 'vcenter'
            })
            
            # Data format
            data_format = workbook.add_format({
                'font_name': 'Courier New',
                'font_size': 11,
                'align': 'left',
                'valign': 'vcenter'
            })
            
            # Write title row
            num_columns = len(df.columns)
            worksheet.merge_range(0, 0, 0, num_columns - 1, 'SỔ THEO DÕI TÀI SẢN RA/VÀO', title_format)
            
            # Apply header format
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(1, col_num, value, header_format)
            
            # Apply data format
            for row_num in range(len(df)):
                for col_num in range(len(df.columns)):
                    worksheet.write(row_num + 2, col_num, df.iloc[row_num, col_num], data_format)
            
            # Auto-adjust column widths
            for col_num, column in enumerate(df.columns):
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                worksheet.set_column(col_num, col_num, column_width + 2)

        output.seek(0)

        headers = {
            'Content-Disposition': f'attachment; filename="so_theo_doi_tai_san_{get_local_time().strftime("%Y%m%d_%H%M")}.xlsx"'
        }
        return Response(content=output.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Không thể tạo file Excel: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Không thể tạo file Excel.")