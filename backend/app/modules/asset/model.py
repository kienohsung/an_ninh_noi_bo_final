from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.config import settings
import pytz
from datetime import datetime

def get_local_time():
    """Returns the current time in the timezone specified in settings."""
    tz = pytz.timezone(settings.TZ)
    return datetime.now(tz)

# Hằng số trạng thái
ASSET_STATUS_PENDING_OUT = "pending_out"
ASSET_STATUS_CHECKED_OUT = "checked_out"
ASSET_STATUS_RETURNED = "returned"

class AssetLog(Base):
    __tablename__ = "asset_log"
    id = Column(Integer, primary_key=True, index=True)
    
    # Thông tin người đăng ký
    registered_by_user_id = Column(Integer, ForeignKey("users.id"))
    registered_by = relationship("User", foreign_keys=[registered_by_user_id])
    full_name = Column(String(128), nullable=False)
    employee_code = Column(String(128), nullable=False)
    department = Column(String(128), default="")
    
    # Manager Approvals
    vietnamese_manager_name = Column(String(128), nullable=True)
    korean_manager_name = Column(String(255), nullable=True)
    
    # Print tracking
    print_count = Column(Integer, default=0, nullable=False)
    
    # Thông tin đăng ký
    destination = Column(String(255), index=True, default="")
    description_reason = Column(Text, default="")
    asset_description = Column(Text, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    expected_return_date = Column(Date, nullable=True)
    estimated_datetime = Column(DateTime, nullable=True)
    
    # Trạng thái và Dấu vết
    status = Column(String(16), index=True, default=ASSET_STATUS_PENDING_OUT)
    
    # Dấu vết xác nhận RA
    check_out_time = Column(DateTime, nullable=True)
    check_out_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    check_out_by = relationship("User", foreign_keys=[check_out_by_user_id])
    
    # Dấu vết xác nhận VỀ
    check_in_back_time = Column(DateTime, nullable=True)
    check_in_back_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    check_in_back_by = relationship("User", foreign_keys=[check_in_back_by_user_id])

    created_at = Column(DateTime, default=get_local_time)
    
    # Image relationship
    images = relationship("AssetImage", back_populates="asset", cascade="all, delete-orphan")

class AssetImage(Base):
    __tablename__ = "asset_images"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("asset_log.id"), nullable=False)
    image_path = Column(String(255), nullable=False)
    
    asset = relationship("AssetLog", back_populates="images")
