# File: backend/app/routers/guests.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from .. import models, schemas
from ..core.deps import get_db
from ..core.auth import get_current_user, require_roles
from ..models import get_local_time
from ..core.config import settings

router = APIRouter(prefix="/guests", tags=["guests"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=schemas.GuestRead, dependencies=[Depends(require_roles("admin", "manager", "staff"))])
def create_guest(payload: schemas.GuestCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user), bg: BackgroundTasks = BackgroundTasks()):
    """
    Tạo một bản ghi khách lẻ mới.
    """
    try:
        from ..modules.guest.service import guest_service
        return guest_service.create_guest(db, payload, user.id, bg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating guest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not create guest")

@router.post("/{guest_id}/upload-image", response_model=schemas.GuestImageRead, dependencies=[Depends(require_roles("admin", "manager", "staff"))])
async def upload_guest_image(guest_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    from ..modules.guest.service import guest_service
    try:
        content = await file.read()
        db_image = guest_service.upload_guest_image_bytes(db, guest_id, file.filename, content)
        if not db_image:
             raise HTTPException(status_code=404, detail="Guest not found")
        return db_image
    except Exception as e:
        logger.error(f"Could not upload image for guest {guest_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not upload image")


@router.post("/bulk", response_model=list[schemas.GuestRead], dependencies=[Depends(require_roles("admin", "manager", "staff"))])
def create_guests_bulk(payload: schemas.GuestBulkCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user), bg: BackgroundTasks = BackgroundTasks()):
    try:
        from ..modules.guest.service import guest_service
        return guest_service.create_guests_bulk(db, payload, user.id, bg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating bulk guests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not create guests")


@router.get("/", response_model=list[schemas.GuestReadWithUser])
def list_guests(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    q: str | None = Query(default=None, description="Tìm kiếm tương đối"),
    include_all_my_history: bool = False
):
    from ..modules.guest.service import guest_service
    results = guest_service.list_guests(db, user, q, include_all_my_history)

    # Đảm bảo trả về cả thông tin ảnh
    output = []
    for guest, registered_by_name in results:
        guest_data = schemas.GuestRead.model_validate(guest).model_dump()
        guest_data["registered_by_name"] = registered_by_name
        guest_data["images"] = [schemas.GuestImageRead.model_validate(img) for img in guest.images]
        output.append(schemas.GuestReadWithUser.model_validate(guest_data))

    return output

@router.get("/suggestions", response_model=schemas.GuestSuggestions)
def get_suggestions(db: Session = Depends(get_db)):
    from ..modules.guest.service import guest_service
    return guest_service.get_suggestions(db)

@router.put("/{guest_id}", response_model=schemas.GuestRead)
def update_guest(guest_id: int, payload: schemas.GuestUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    try:
        from ..modules.guest.service import guest_service
        guest = guest_service.update_guest(db, guest_id, payload, user)
        if not guest:
            # Handle not found in service or here.
            # Service returns None if not found, let's check manually if we prefer
            # But the service actually does query.get().
            # Let's handle generic HTTPException here if service raises
             raise HTTPException(status_code=404, detail="Guest not found")
        return guest
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not allowed")
    except Exception as e:
        logger.error(f"Error updating guest: {e}", exc_info=True)
        # Check if 404
        if "not found" in str(e).lower():
             raise HTTPException(status_code=404, detail="Guest not found")
        raise HTTPException(status_code=500, detail="Could not update guest")

# Helper removed. Logic moved to GuestService.

@router.delete("/{guest_id}")
def delete_guest(guest_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user), bg: BackgroundTasks = BackgroundTasks()):
    try:
        from ..modules.guest.service import guest_service
        success = guest_service.delete_guest(db, guest_id, user, bg)
        if not success:
            raise HTTPException(status_code=404, detail="Guest not found")
        return {"ok": True}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not allowed")
    except Exception as e:
        logger.error(f"Error deleting guest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not delete guest")

@router.delete("/images/{image_id}", dependencies=[Depends(require_roles("admin", "manager", "staff"))])
def delete_guest_image(image_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    from ..modules.guest.service import guest_service
    try:
        success = guest_service.delete_guest_image(db, image_id, user)
        if not success:
            raise HTTPException(status_code=404, detail="Image not found or permission denied")
        return {"ok": True}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not allowed")
    except Exception as e:
        logger.error(f"Error deleting image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not delete image")

@router.post("/import/xlsx", dependencies=[Depends(require_roles("admin", "manager"))])
async def import_guests(file: UploadFile = File(...), db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    from ..modules.guest.service import guest_service
    try:
        content = await file.read()
        return guest_service.import_guests(db, content, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Xử lý file thất bại: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Import failed")

@router.get("/export/xlsx", dependencies=[Depends(require_roles("admin", "manager", "staff"))])
def export_guests(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    start_date: str | None = Query(default=None, description="Ngày bắt đầu (YYYY-MM-DD)"),
    end_date: str | None = Query(default=None, description="Ngày kết thúc (YYYY-MM-DD)"),
    registrant_id: int | None = Query(default=None, description="ID người đăng ký"),
    supplier_name: str | None = Query(default=None, description="Tên nhà cung cấp"),
    status: str | None = Query(default=None, description="Trạng thái: checked_in hoặc pending")
):
    from ..modules.guest.service import guest_service
    try:
        output = guest_service.export_guests(db, user, start_date, end_date, registrant_id, supplier_name, status)
        headers = {
            'Content-Disposition': f'attachment; filename="so_theo_doi_khach_{get_local_time().strftime("%Y%m%d_%H%M")}.xlsx"'
        }
        return Response(content=output.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)
    except Exception as e:
        logger.error(f"Không thể tạo file Excel: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Không thể tạo file Excel.")

@router.post("/clear", dependencies=[Depends(require_roles("admin"))])
def clear_guests(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    from ..modules.guest.service import guest_service
    try:
        guest_service.clear_all_guests(db, user)
        return {"ok": True, "message": "Đã xóa toàn bộ dữ liệu khách và lưu trữ ảnh."}
    except Exception as e:
        logger.error(f"Lỗi khi xóa dữ liệu khách: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Xóa dữ liệu thất bại: {e}")

@router.post("/delete-old", dependencies=[Depends(require_roles("admin"))])
def delete_old_pending_guests(db: Session = Depends(get_db)):
    """
    Xóa các khách đăng ký cũ với điều kiện:
    - Trạng thái: pending (chờ vào)
    - Ngày vào dự kiến (estimated_datetime) từ ngày hôm qua hoặc cũ hơn
    
    Hành động: Đánh dấu là 'no_show' và tạo thông báo cho người đăng ký.
    """
    from ..modules.guest.service import guest_service
    try:
        processed_count = guest_service.process_no_show_guests(db)
        if processed_count == 0:
            return {"ok": True, "message": "Không có khách quá hạn cần xử lý.", "count": 0}
        
        logger.info(f"Đã xử lý {processed_count} khách no-show.")
        return {"ok": True, "message": f"Đã đánh dấu no-show {processed_count} khách.", "count": processed_count}
    
    except Exception as e:
        logger.error(f"Lỗi khi xóa dữ liệu khách cũ: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Xóa dữ liệu thất bại: {e}")

