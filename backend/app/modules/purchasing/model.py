from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.config import settings
import pytz
from datetime import datetime

def get_local_time():
    """Returns the current time in the timezone specified in settings."""
    tz = pytz.timezone(settings.TZ)
    return datetime.now(tz)

# Hằng số trạng thái Mua bán
PURCHASING_STATUS_NEW = "new"
PURCHASING_STATUS_PENDING = "pending"
PURCHASING_STATUS_APPROVED = "approved"
PURCHASING_STATUS_REJECTED = "rejected"

class PurchasingLog(Base):
    __tablename__ = "purchasing_logs"
    id = Column(Integer, primary_key=True, index=True)
    
    # Thông tin người lập phiếu (Nhập tự do, không FK)
    creator_name = Column(String(128), nullable=False)
    department = Column(String(128), default="")
    using_department = Column(String(128), default="")  # V2: Bộ phận sử dụng
    
    # Thông tin hàng hóa
    category = Column(String(64), index=True, nullable=False)  # PC, Laptop, Linh kiện, Mực in, Khác
    item_name = Column(String(255), nullable=False)
    supplier_name = Column(String(128), default="")
    approved_price = Column(Integer, default=0)  # Lưu VNĐ dạng số nguyên
    
    # Trạng thái
    # Thông tin nhận hàng (V3)
    received_at = Column(DateTime, nullable=True)
    received_note = Column(Text, default="")
    
    status = Column(String(32), index=True, default=PURCHASING_STATUS_NEW)
    
    # Timestamps
    created_at = Column(DateTime, default=get_local_time, index=True)
    
    # Image relationship
    images = relationship("PurchasingImage", back_populates="purchasing", cascade="all, delete-orphan")

class PurchasingImage(Base):
    __tablename__ = "purchasing_images"
    
    id = Column(Integer, primary_key=True, index=True)
    purchasing_id = Column(Integer, ForeignKey("purchasing_logs.id"), nullable=False)
    image_path = Column(String(255), nullable=False)
    image_type = Column(String(32), default="request") # request, delivery
    
    purchasing = relationship("PurchasingLog", back_populates="images")
