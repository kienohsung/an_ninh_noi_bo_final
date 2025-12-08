# File: backend/app/routers/gcp.py
from fastapi import APIRouter, Depends, HTTPException

from ..core.auth import get_current_user

router = APIRouter(prefix="/gcp", tags=["gcp"])

@router.post("/generate-upload-url", response_model=dict)
def generate_upload_url(
    filename: str,
    content_type: str,
    user: dict = Depends(get_current_user)
):
    """
    Tạo một Signed URL để cho phép frontend tải file trực tiếp lên Google Cloud Storage.
    """
    from ..modules.storage.service import storage_service
    try:
        return storage_service.generate_upload_url(filename, content_type)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
         raise HTTPException(status_code=500, detail=str(e))

