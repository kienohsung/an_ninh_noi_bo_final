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
