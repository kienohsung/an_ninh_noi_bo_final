# File: backend/app/routers/suppliers.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session
import logging

from .. import models, schemas
from ..core.deps import get_db
from ..core.auth import require_roles

router = APIRouter(prefix="/suppliers", tags=["suppliers"], dependencies=[Depends(require_roles("admin", "manager"))])
logger = logging.getLogger(__name__)

@router.post("/", response_model=schemas.SupplierRead)
def create_supplier(payload: schemas.SupplierCreate, db: Session = Depends(get_db)):
    try:
        from ..modules.supplier.service import supplier_service
        return supplier_service.create_supplier(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=list[schemas.SupplierRead])
def list_suppliers(db: Session = Depends(get_db)):
    from ..modules.supplier.service import supplier_service
    return supplier_service.list_suppliers(db)

@router.put("/{supplier_id}", response_model=schemas.SupplierRead)
def update_supplier(supplier_id: int, payload: schemas.SupplierUpdate, db: Session = Depends(get_db)):
    from ..modules.supplier.service import supplier_service
    s = supplier_service.update_supplier(db, supplier_id, payload)
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return s

@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    from ..modules.supplier.service import supplier_service
    if not supplier_service.delete_supplier(db, supplier_id):
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"ok": True}

@router.post("/{supplier_id}/plates", response_model=schemas.SupplierPlateRead)
def add_plate(supplier_id: int, payload: schemas.SupplierPlateCreate, db: Session = Depends(get_db)):
    from ..modules.supplier.service import supplier_service
    p = supplier_service.add_plate(db, supplier_id, payload)
    if not p:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return p

@router.get("/{supplier_id}/plates", response_model=list[schemas.SupplierPlateRead])
def list_plates(supplier_id: int, db: Session = Depends(get_db)):
    from ..modules.supplier.service import supplier_service
    return supplier_service.list_plates(db, supplier_id)

@router.delete("/{supplier_id}/plates/{plate_id}")
def delete_plate(supplier_id: int, plate_id: int, db: Session = Depends(get_db)):
    from ..modules.supplier.service import supplier_service
    if not supplier_service.delete_plate(db, supplier_id, plate_id):
        raise HTTPException(status_code=404, detail="Plate not found")
    return {"ok": True}

@router.get("/export/xlsx", dependencies=[Depends(require_roles("admin", "manager"))])
def export_suppliers(db: Session = Depends(get_db)):
    from ..modules.supplier.service import supplier_service
    try:
        bio = supplier_service.export_suppliers(db)
        headers = {"Content-Disposition": "attachment; filename=suppliers_export.xlsx"}
        return Response(bio.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Export failed")

@router.post("/import/xlsx", dependencies=[Depends(require_roles("admin"))])
async def import_suppliers(db: Session = Depends(get_db), file: UploadFile = File(...)):
    from ..modules.supplier.service import supplier_service
    try:
        content = await file.read()
        supplier_service.import_suppliers(db, content)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Import failed")

@router.post("/clear", dependencies=[Depends(require_roles("admin"))])
def clear_suppliers(db: Session = Depends(get_db)):
    from ..modules.supplier.service import supplier_service
    try:
        supplier_service.clear_suppliers(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear suppliers: {e}")
    return {"ok": True}

# ---------- STATS ENDPOINT ----------
@router.get("/stats/activity")
def get_supplier_activity_stats(
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """Lấy thống kê hoạt động nhà cung cấp (top suppliers theo số lượng khách)"""
    from sqlalchemy import func
    from datetime import datetime
    
    try:
        # Build query
        query = db.query(
            models.Guest.supplier_name,
            func.count(models.Guest.id).label('count')
        ).filter(
            models.Guest.supplier_name != "",
            models.Guest.supplier_name.isnot(None)
        )
        
        # Apply date filters
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(models.Guest.created_at >= start_dt)
            except:
                pass
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(models.Guest.created_at <= end_dt)
            except:
                pass
        
        # Group and order
        results = query.group_by(models.Guest.supplier_name)\
                      .order_by(func.count(models.Guest.id).desc())\
                      .limit(10)\
                      .all()
        
        # Format response
        labels = [r[0] for r in results]
        series = [r[1] for r in results]
        
        return {
            "labels": labels,
            "series": series,
            "total_suppliers": len(results)
        }
        
    except Exception as e:
        logger.error(f"Stats query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get stats")

@router.get("/stats/no-show")
def get_supplier_noshow_stats(
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """Lấy thống kê nhà cung cấp có khách no-show (khách đăng ký nhưng không tới)"""
    from sqlalchemy import func
    from datetime import datetime
    
    try:
        # Build query for no-show guests
        query = db.query(
            models.Guest.supplier_name,
            func.count(models.Guest.id).label('no_show_count')
        ).filter(
            models.Guest.supplier_name != "",
            models.Guest.supplier_name.isnot(None),
            models.Guest.status == "no_show"
        )
        
        # Apply date filters
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(models.Guest.created_at >= start_dt)
            except:
                pass
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(models.Guest.created_at <= end_dt)
            except:
                pass
        
        # Group and order
        results = query.group_by(models.Guest.supplier_name)\
                      .order_by(func.count(models.Guest.id).desc())\
                      .limit(10)\
                      .all()
        
        # Format response
        data = [
            {
                "supplier_name": r[0],
                "no_show_count": r[1]
            }
            for r in results
        ]
        
        return {
            "data": data,
            "total": len(data)
        }
        
    except Exception as e:
        logger.error(f"No-show stats query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get no-show stats")

@router.get("/stats/no-show/{supplier_name}/details")
def get_supplier_noshow_details(
    supplier_name: str,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """Lấy chi tiết top 5 khách no-show của một nhà cung cấp cụ thể"""
    from sqlalchemy import func
    from datetime import datetime
    from urllib.parse import unquote
    
    try:
        # Decode URL-encoded supplier name
        supplier_name = unquote(supplier_name)
        
        # Subquery to count no-show occurrences per guest (by full_name)
        no_show_count_subq = db.query(
            models.Guest.full_name,
            func.count(models.Guest.id).label('total_no_shows')
        ).filter(
            models.Guest.status == "no_show"
        ).group_by(
            models.Guest.full_name
        ).subquery()
        
        # Build query with join to get user info and no-show count
        query = db.query(
            models.Guest.full_name,
            models.User.full_name.label('employee_name'),
            models.Guest.created_at,
            models.Guest.estimated_datetime,
            func.coalesce(no_show_count_subq.c.total_no_shows, 0).label('no_show_count')
        ).outerjoin(
            models.User, 
            models.Guest.registered_by_user_id == models.User.id
        ).outerjoin(
            no_show_count_subq,
            models.Guest.full_name == no_show_count_subq.c.full_name
        ).filter(
            models.Guest.supplier_name == supplier_name,
            models.Guest.status == "no_show"
        )
        
        # Apply date filters
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(models.Guest.created_at >= start_dt)
            except:
                pass
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(models.Guest.created_at <= end_dt)
            except:
                pass
        
        # Order by created_at and limit to top 5
        results = query.order_by(models.Guest.created_at.desc()).limit(5).all()
        
        # Format response
        data = [
            {
                "guest_name": r[0],
                "registered_by": r[1] or "N/A",
                "registered_at": r[2].isoformat() if r[2] else None,
                "visit_date": r[3].isoformat() if r[3] else None,
                "no_show_count": r[4]
            }
            for r in results
        ]
        
        return {
            "supplier_name": supplier_name,
            "guests": data,
            "total": len(data)
        }
        
    except Exception as e:
        logger.error(f"No-show details query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get no-show details")

# ---------- NORMALIZATION ENDPOINTS ----------
@router.get("/normalization/analyze", dependencies=[Depends(require_roles("admin"))])
def analyze_supplier_normalization(db: Session = Depends(get_db)):
    """Phân tích và nhóm các tên nhà cung cấp tương tự"""
    logger.info("🔍 [NORMALIZATION] Analyze endpoint called")
    from ..modules.supplier.normalization_service import supplier_normalization_service
    try:
        result = supplier_normalization_service.analyze_supplier_names(db)
        logger.info(f"✅ [NORMALIZATION] Analysis complete. Found {result.total_groups} groups")
        return result
    except Exception as e:
        logger.error(f"❌ [NORMALIZATION] Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/normalization/preview", dependencies=[Depends(require_roles("admin"))])
def preview_supplier_normalization(
    payload: schemas.NormalizationRequest,
    db: Session = Depends(get_db)
):
    """Xem trước số lượng bản ghi sẽ bị ảnh hưởng"""
    logger.info(f"🔍 [NORMALIZATION] Preview endpoint called with {len(payload.mappings)} mappings")
    from ..modules.supplier.normalization_service import supplier_normalization_service
    try:
        result = supplier_normalization_service.preview_normalization(db, payload.mappings)
        logger.info(f"✅ [NORMALIZATION] Preview complete. Total records: {result.total}")
        return result
    except Exception as e:
        logger.error(f"❌ [NORMALIZATION] Preview failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")

@router.post("/normalization/execute", dependencies=[Depends(require_roles("admin"))])
def execute_supplier_normalization(
    payload: schemas.NormalizationRequest,
    db: Session = Depends(get_db)
):
    """Thực hiện chuẩn hóa tên nhà cung cấp"""
    logger.info(f"🔍 [NORMALIZATION] Execute endpoint called with {len(payload.mappings)} mappings")
    from ..modules.supplier.normalization_service import supplier_normalization_service
    try:
        result = supplier_normalization_service.execute_normalization(db, payload.mappings)
        if not result.success:
            logger.error(f"❌ [NORMALIZATION] Execution failed: {result.errors}")
            raise HTTPException(status_code=500, detail=result.errors)
        logger.info(f"✅ [NORMALIZATION] Execution successful. Updated: {result.updated_records}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [NORMALIZATION] Execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
