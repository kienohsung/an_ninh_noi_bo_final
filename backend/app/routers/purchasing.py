# File: backend/app/routers/purchasing.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field
import logging
import uuid
import os

from .. import models
from ..database import get_db
from ..auth import require_roles, get_current_user
from ..config import settings

# === SCHEMAS ===
class PurchasingLogCreate(BaseModel):
    creator_name: str = Field(..., min_length=1, max_length=128)
    department: str = Field(default="", max_length=128)
    using_department: str = Field(default="", max_length=128)
    category: str = Field(..., min_length=1, max_length=64)
    item_name: str = Field(..., min_length=1, max_length=255)
    supplier_name: str = Field(default="", max_length=128)
    approved_price: int = Field(default=0, ge=0)

class PurchasingLogUpdate(BaseModel):
    creator_name: Optional[str] = Field(None, max_length=128)
    department: Optional[str] = Field(None, max_length=128)
    using_department: Optional[str] = Field(None, max_length=128)
    category: Optional[str] = Field(None, max_length=64)
    item_name: Optional[str] = Field(None, max_length=255)
    supplier_name: Optional[str] = Field(None, max_length=128)
    approved_price: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None)

class PurchasingImageRead(BaseModel):
    id: int
    purchasing_id: int
    image_path: str
    image_type: str = "request"

    class Config:
        from_attributes = True

class PurchasingLogRead(BaseModel):
    id: int
    creator_name: str
    department: str
    using_department: str
    category: str
    item_name: str
    supplier_name: str
    approved_price: int
    status: str
    created_at: Optional[datetime]
    received_at: Optional[datetime]
    received_note: Optional[str]
    images: List[PurchasingImageRead] = []

    class Config:
        from_attributes = True

# === ROUTER ===
router = APIRouter(
    prefix="/purchasing",
    tags=["Purchasing"],
    dependencies=[Depends(require_roles("admin", "manager"))]
)

# Constants
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB

# === ENDPOINT: [GET] /purchasing (Danh sách) ===
@router.get("", response_model=List[PurchasingLogRead])
def get_purchasing_list(
    start_date: date = Query(None),
    end_date: date = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Lấy danh sách phiếu mua bán với filter"""
    query = (
        select(models.PurchasingLog)
        .options(joinedload(models.PurchasingLog.images))
        .order_by(models.PurchasingLog.created_at.desc())
    )
    
    if start_date:
        start_dt = datetime.combine(start_date, datetime.min.time())
        query = query.filter(models.PurchasingLog.created_at >= start_dt)
    if end_date:
        end_dt = datetime.combine(end_date, datetime.max.time())
        query = query.filter(models.PurchasingLog.created_at <= end_dt)
    
    if category:
        query = query.filter(models.PurchasingLog.category == category)
    
    if status:
        query = query.filter(models.PurchasingLog.status == status)
    
    results = db.scalars(query).unique().all()
    return results

# === ENDPOINT: [POST] /purchasing (Tạo mới) ===
@router.post("", response_model=PurchasingLogRead, status_code=201)
def create_purchasing(
    data: PurchasingLogCreate,
    db: Session = Depends(get_db)
):
    """Tạo phiếu mua bán mới. Ngày giờ tự động gán từ server."""
    db_purchasing = models.PurchasingLog(
        creator_name=data.creator_name,
        department=data.department,
        using_department=data.using_department,
        category=data.category,
        item_name=data.item_name,
        supplier_name=data.supplier_name,
        approved_price=data.approved_price,
        status=models.PURCHASING_STATUS_NEW,
        created_at=models.get_local_time()
    )
    
    db.add(db_purchasing)
    db.commit()
    db.refresh(db_purchasing)
    
    return db_purchasing

# === ENDPOINT: [PUT] /purchasing/{id} (Cập nhật) ===
@router.put("/{purchasing_id}", response_model=PurchasingLogRead)
def update_purchasing(
    purchasing_id: int,
    data: PurchasingLogUpdate,
    db: Session = Depends(get_db)
):
    """Cập nhật thông tin phiếu mua bán"""
    db_purchasing = db.get(models.PurchasingLog, purchasing_id)
    
    if not db_purchasing:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu mua bán")
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None and hasattr(db_purchasing, key):
            setattr(db_purchasing, key, value)
    
    db.commit()
    db.refresh(db_purchasing)
    return db_purchasing

# === ENDPOINT: [DELETE] /purchasing/{id} (Xóa) ===
@router.delete("/{purchasing_id}")
def delete_purchasing(
    purchasing_id: int,
    db: Session = Depends(get_db)
):
    """Xóa phiếu mua bán và các file ảnh vật lý liên quan"""
    logger = logging.getLogger(__name__)
    
    db_purchasing = db.get(
        models.PurchasingLog, 
        purchasing_id, 
        options=[joinedload(models.PurchasingLog.images)]
    )
    
    if not db_purchasing:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu mua bán")
    
    # Xóa file vật lý
    for image in db_purchasing.images:
        try:
            file_path = os.path.join(settings.UPLOAD_DIR, image.image_path)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Could not delete file {image.image_path}: {e}")
    
    # Xóa record trong DB (cascade xóa images)
    db.delete(db_purchasing)
    db.commit()
    
    return {"message": "Đã xóa phiếu mua bán thành công", "ok": True}

# === ENDPOINT: [POST] /purchasing/{id}/upload-image (Upload ảnh) ===
@router.post("/{purchasing_id}/upload-image", response_model=PurchasingImageRead)
async def upload_purchasing_image(
    purchasing_id: int,
    type: str = Query("request", enum=["request", "delivery"]),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload ảnh cho phiếu mua bán. Max 5MB, chỉ chấp nhận ảnh/pdf."""
    logger = logging.getLogger(__name__)
    
    # Check if purchasing exists
    db_purchasing = db.get(models.PurchasingLog, purchasing_id)
    if not db_purchasing:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu mua bán")
    
    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Định dạng file không hợp lệ. Chỉ chấp nhận: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )
    
    # Read file and validate size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Dung lượng file vượt quá giới hạn {MAX_FILE_SIZE_BYTES // (1024*1024)}MB"
        )
    
    try:
        # Generate unique filename (UUID)
        unique_filename = f"{uuid.uuid4()}{ext}"
        
        # Save to purchasing directory
        save_dir = os.path.join(settings.UPLOAD_DIR, "purchasing")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, unique_filename)
        
        # Write file
        with open(save_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Create database record
        db_image = models.PurchasingImage(
            purchasing_id=purchasing_id,
            image_path=f"purchasing/{unique_filename}",
            image_type=type
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        
        return db_image
    except Exception as e:
        logger.error(f"Could not upload image for purchasing {purchasing_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Không thể tải ảnh lên")

# === ENDPOINT: [DELETE] /purchasing/images/{image_id} (Xóa ảnh) ===
@router.delete("/images/{image_id}")
def delete_purchasing_image(
    image_id: int,
    db: Session = Depends(get_db)
):
    """Xóa ảnh của phiếu mua bán"""
    logger = logging.getLogger(__name__)
    
    db_image = db.get(models.PurchasingImage, image_id)
    
    if not db_image:
        raise HTTPException(status_code=404, detail="Không tìm thấy ảnh")
    
    # Xóa file vật lý
    try:
        file_path = os.path.join(settings.UPLOAD_DIR, db_image.image_path)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
    except Exception as e:
        logger.error(f"Could not delete file {db_image.image_path}: {e}")
    
    db.delete(db_image)
    db.commit()
    
    return {"ok": True}

# === ENDPOINT: [POST] /purchasing/{id}/receive (Nhận hàng) ===
class ReceiveGoodsRequest(BaseModel):
    note: str

@router.post("/{purchasing_id}/receive", response_model=PurchasingLogRead)
def receive_purchasing(
    purchasing_id: int,
    payload: ReceiveGoodsRequest,
    db: Session = Depends(get_db)
):
    """Xác nhận nhận hàng và kết thúc phiếu"""
    db_purchasing = db.get(models.PurchasingLog, purchasing_id)
    
    if not db_purchasing:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu")
    
    if db_purchasing.status in ["completed", "rejected"]:
         raise HTTPException(status_code=400, detail="Trạng thái phiếu không hợp lệ để nhận hàng")
    
    db_purchasing.status = "completed"
    db_purchasing.received_at = models.get_local_time()
    db_purchasing.received_note = payload.note
    
    db.commit()
    db.refresh(db_purchasing)
    
    return db_purchasing
