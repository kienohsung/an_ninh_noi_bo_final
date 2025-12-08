import os
import logging
from typing import Dict, Any, Optional

from app.utils.notifications import send_telegram_message

logger = logging.getLogger(__name__)

class AdminService:
    @staticmethod
    def validate_delete_password(password: str) -> bool:
        """
        Validate password for admin delete operations.
        """
        admin_password = os.getenv("ADMIN_DELETE_PASSWORD", "Kienhp@@123")
        return password == admin_password

    @staticmethod
    def test_telegram_connection() -> Dict[str, Any]:
        """
        Test Telegram connection by sending a message.
        """
        res = send_telegram_message("🔔 Test: hệ thống đã kết nối Telegram thành công.")
        if not res.get("ok"):
             return {"ok": False, "detail": res}
        return {"ok": True, "detail": res}

admin_service = AdminService()
