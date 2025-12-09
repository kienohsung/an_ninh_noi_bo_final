from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.config import settings
from app.utils.time_utils import get_local_time
import pytz
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(128), nullable=False)
    role = Column(String(16), nullable=False, index=True)  # admin, manager, guard, staff
    department = Column(String(64), default="", nullable=True)  # Bộ phận
    telegram_id = Column(String(32), unique=True, nullable=True, index=True) # ID Telegram
    created_at = Column(DateTime, default=get_local_time)

    # Relationships using String References to avoid Circular Imports
    guests = relationship("Guest", back_populates="registered_by", foreign_keys="[Guest.registered_by_user_id]")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
