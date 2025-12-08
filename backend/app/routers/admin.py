# File: backend/app/routers/admin.py
"""
Admin-only routes for sensitive operations
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import os

from .. import models
from ..core.auth import get_current_user, require_roles

router = APIRouter(prefix="/admin", tags=["admin"])


class PasswordValidation(BaseModel):
    password: str


@router.post("/validate-delete-password")
def validate_admin_delete_password(
    payload: PasswordValidation,
    user: models.User = Depends(require_roles("admin"))
):
    """
    Validate password for admin delete operations
    This prevents password from being exposed in frontend code
    """
    from ..modules.admin.service import admin_service
    is_valid = admin_service.validate_delete_password(payload.password)
    
    return {
        "valid": is_valid,
        "message": "Password validated" if is_valid else "Invalid password"
    }
