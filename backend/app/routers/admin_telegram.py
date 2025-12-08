# File: backend/app/routers/admin_telegram.py
from fastapi import APIRouter, Depends, HTTPException
from ..core.auth import require_roles

router = APIRouter(prefix="/admin/telegram", tags=["admin-telegram"])

@router.get("/test", dependencies=[Depends(require_roles("admin"))])
def test_message():
    from ..modules.admin.service import admin_service
    return admin_service.test_telegram_connection()

