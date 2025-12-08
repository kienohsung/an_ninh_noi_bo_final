# File: backend/app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from .. import models, schemas
from ..core.deps import get_db
from ..core.auth import require_roles

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=schemas.UserRead, dependencies=[Depends(require_roles("admin"))])
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        from ..modules.user.service import user_service
        return user_service.create_user(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=list[schemas.UserRead], dependencies=[Depends(require_roles("admin", "manager"))])
def list_users(db: Session = Depends(get_db), q: str | None = Query(default=None, description="search")):
    from ..modules.user.service import user_service
    return user_service.list_users(db, q)

@router.put("/{user_id}", response_model=schemas.UserRead, dependencies=[Depends(require_roles("admin"))])
def update_user(user_id: int, payload: schemas.UserUpdate, db: Session = Depends(get_db)):
    try:
        from ..modules.user.service import user_service
        user = user_service.update_user(db, user_id, payload)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}", dependencies=[Depends(require_roles("admin"))])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    try:
        from ..modules.user.service import user_service
        if not user_service.delete_user(db, user_id):
            raise HTTPException(status_code=404, detail="User not found")
        return {"ok": True}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/export/xlsx", dependencies=[Depends(require_roles("admin"))])
def export_users(db: Session = Depends(get_db)):
    try:
        from ..modules.user.service import user_service
        output = user_service.export_users(db)
        
        headers = {
            'Content-Disposition': f'attachment; filename="users_export_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        }
        return Response(content=output.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

    except Exception as e:
        logger.error(f"Could not generate users Excel file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not generate Excel file.")

@router.post("/clear", dependencies=[Depends(require_roles("admin"))])
def clear_users(db: Session = Depends(get_db)):
    try:
        from ..modules.user.service import user_service
        num_deleted = user_service.clear_users(db)
        return {"ok": True, "num_deleted": num_deleted}
    except Exception as e:
        logger.error(f"Error clearing users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not clear users.")

@router.post("/import/xlsx", dependencies=[Depends(require_roles("admin"))])
async def import_users(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        from ..modules.user.service import user_service
        content = await file.read()
        imported_count = user_service.import_users(db, content)
        return {"ok": True, "imported_count": imported_count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error importing users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to import file: {e}")
