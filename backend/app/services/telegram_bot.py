import time
import logging
import requests
import threading
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ..config import settings
from ..database import SessionLocal
from ..models import User, get_local_time
from ..utils.notifications import send_telegram_message


# Cấu hình logging
logger = logging.getLogger(__name__)

import os
from collections import deque

# ... imports ...

class TelegramPollingService:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self.processed_ids = deque(maxlen=100) # Cache 100 ID gần nhất

    def start(self):
        """Khởi động bot trong một thread riêng."""
        if not settings.NOTIFY_TELEGRAM_ENABLED or not self.token:
            logger.warning("Telegram Bot chưa được cấu hình hoặc bị tắt. Bỏ qua Polling Mode.")
            return

        logger.info(f"Khởi động Telegram Polling Service... (PID: {os.getpid()})")
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_polling_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Dừng bot an toàn."""
        if self.thread and self.thread.is_alive():
            logger.info("Đang dừng Telegram Polling Service...")
            self.stop_event.set()
            self.thread.join(timeout=5)
            logger.info("Telegram Polling Service đã dừng.")

    def _run_polling_loop(self):
        """Vòng lặp chính để hỏi server Telegram."""
        logger.info("Telegram Polling Loop bắt đầu chạy.")
        while not self.stop_event.is_set():
            try:
                updates = self._get_updates()
                for update in updates:
                    update_id = update["update_id"]
                    if update_id in self.processed_ids:
                        logger.warning(f"Bỏ qua update_id {update_id} đã xử lý.")
                        self.offset = update_id + 1
                        continue

                    self._process_update(update)
                    
                    # Đánh dấu đã xử lý
                    self.processed_ids.append(update_id)
                    # Cập nhật offset
                    self.offset = update_id + 1
            except Exception as e:
                logger.error(f"Lỗi trong vòng lặp Polling: {e}")
                # Nghỉ 5 giây trước khi thử lại để tránh spam lỗi khi mất mạng
                time.sleep(5)
            
            # Nghỉ ngắn để tránh chiếm dụng CPU quá mức (dù long polling đã block rồi)
            time.sleep(0.1)

    def _get_updates(self) -> list:
        """Gọi API getUpdates của Telegram."""
        url = f"{self.base_url}/getUpdates"
        params = {
            "offset": self.offset,
            "timeout": 30  # Long polling
        }
        try:
            response = requests.get(url, params=params, timeout=35)
            response.raise_for_status()
            data = response.json()
            if data.get("ok"):
                return data.get("result", [])
            else:
                logger.error(f"Telegram API Error: {data}")
                return []
        except requests.RequestException as e:
            # Nếu timeout (do long polling) thì không sao, chỉ là hết giờ chờ
            # Nhưng nếu lỗi kết nối thật thì raise để vòng lặp xử lý
            if isinstance(e, requests.Timeout):
                return []
            raise e

    def _process_update(self, update: Dict[str, Any]):
        """Xử lý từng update nhận được."""
        message = update.get("message")
        if not message or "text" not in message:
            return

        chat_id = message["chat"]["id"]
        text = message["text"].strip()
        telegram_id = str(message["from"]["id"])
        user_name = message["from"].get("first_name", "Unknown")

        logger.info(f"Nhận tin nhắn từ {user_name} ({telegram_id}): {text}")

        # 1. Xác thực người dùng
        user = self._authenticate_user(telegram_id)
        if not user:
            self._send_reply(chat_id, "⛔ Tài khoản Telegram của bạn chưa được liên kết với hệ thống. Vui lòng liên hệ Admin.")
            return

        # 2. Xử lý lệnh
        if text.startswith("/"):
            self._handle_command(chat_id, text)
        else:
            self._send_reply(chat_id, "⚠️ Sai cú pháp. Gõ /help để xem hướng dẫn.")

    def _authenticate_user(self, telegram_id: str) -> Optional[User]:
        """Kiểm tra xem telegram_id có tồn tại trong DB không."""
        db: Session = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            return user
        except Exception as e:
            logger.error(f"Lỗi xác thực user {telegram_id}: {e}")
            return None
        finally:
            db.close()

    def _handle_command(self, chat_id: int, text: str):
        """Xử lý các lệnh bắt đầu bằng /"""
        cmd = text.split()[0].lower()
        if cmd in ["/start", "/help", "/huongdan"]:
            help_text = (
                "🤖 **HƯỚNG DẪN SỬ DỤNG**\n\n"
                "Hiện tại bot chỉ hỗ trợ nhận thông báo.\n"
                "Vui lòng sử dụng website để đăng ký khách."
            )
            self._send_reply(chat_id, help_text)
        else:
            self._send_reply(chat_id, "Lệnh không hợp lệ. Gõ /help để được hỗ trợ.")

    def _send_reply(self, chat_id: int, text: str):
        """Gửi tin nhắn phản hồi riêng cho user."""
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            logger.error(f"Lỗi gửi tin nhắn phản hồi tới {chat_id}: {e}")

# Global instance
telegram_bot_service = TelegramPollingService()
