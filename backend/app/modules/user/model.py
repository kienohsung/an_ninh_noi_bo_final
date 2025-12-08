from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.config import settings
import pytz
from datetime import datetime

def get_local_time():
    """Returns the current time in the timezone specified in settings."""
    tz = pytz.timezone(settings.TZ)
    return datetime.now(tz)

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
