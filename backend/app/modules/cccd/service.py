import logging
import requests
from fastapi import UploadFile, HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

class CCCDService:
    @staticmethod
    async def extract_cccd_info(file: UploadFile, user: dict) -> dict:
        """
        Extracts CCCD info by proxying to an external service.
        """
        if not settings.ID_CARD_EXTRACTOR_URL:
            logger.error("URL của ID Card Extractor Service chưa được cấu hình trong file .env hoặc config.py")
            raise ValueError("Extractor service is not configured.")

        if not file.content_type.startswith("image/"):
             raise ValueError(f"Tệp {file.filename} không phải là ảnh.")
        
        try:
            # Read file content
            file_content = await file.read()
            
            # Prepare multipart payload
            files_payload = {'file': (file.filename, file_content, file.content_type)}

            logger.info(f"Chuyển tiếp yêu cầu quét CCCD cho file '{file.filename}' đến service: {settings.ID_CARD_EXTRACTOR_URL}")

            # Send POST request
            response = requests.post(settings.ID_CARD_EXTRACTOR_URL, files=files_payload, timeout=30)
            
            # Raise for status
            response.raise_for_status()

            # Return JSON
            return response.json()

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Lỗi kết nối đến ID card extractor service: {e}")
            raise ConnectionError("Không thể kết nối đến dịch vụ quét CCCD. Vui lòng kiểm tra xem service đã được khởi chạy chưa.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Lỗi trong quá trình gọi đến service quét CCCD: {e}")
            error_detail = "Không rõ lỗi"
            if e.response is not None:
                try:
                    error_detail = e.response.json().get("detail", e.response.text)
                except:
                    error_detail = e.response.text
            
            raise RuntimeError(f"Dịch vụ quét CCCD báo lỗi: {error_detail}")
        except Exception as e:
            logger.error(f"Đã có lỗi không xác định xảy ra trong proxy: {e}", exc_info=True)
            raise e

cccd_service = CCCDService()
