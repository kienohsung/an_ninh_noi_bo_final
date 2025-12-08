# File: backend/app/routers/gemini.py
# MÔ TẢ: File này đã được viết lại hoàn toàn.
# Nó không còn gọi trực tiếp đến Gemini nữa mà đóng vai trò là một proxy,
# chuyển tiếp yêu cầu đến service API trích xuất CCCD độc lập.

import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from ..core.auth import get_current_user

router = APIRouter(prefix="/gemini", tags=["gemini"])
logger = logging.getLogger(__name__)

@router.post("/extract-cccd-info")
async def extract_cccd_info_proxy(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """
    Endpoint này nhận file ảnh từ frontend, sau đó chuyển tiếp (proxy) đến
    ID Card Extractor Service để xử lý và trả kết quả về.
    """
    from ..modules.cccd.service import cccd_service
    try:
        return await cccd_service.extract_cccd_info(file, user)

    except ValueError as e:
        if "Extractor service is not configured" in str(e):
             raise HTTPException(status_code=500, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
         # Extract status code if possible or default to 500. 
         # Since RuntimeError wrapper lost the status code, we default to 500 but detail is preserved.
         raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi xử lý yêu cầu quét CCCD.")
