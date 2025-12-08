from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.config import settings
import pytz
from datetime import datetime

def get_local_time():
    """Returns the current time in the timezone specified in settings."""
    tz = pytz.timezone(settings.TZ)
    return datetime.now(tz)

class Guest(Base):
    __tablename__ = "guests"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(128), index=True, nullable=False)
    id_card_number = Column(String(32), index=True, default="")
    company = Column(String(128), index=True, default="")
    reason = Column(Text, default="")
    license_plate = Column(String(32), index=True, default="")
    supplier_name = Column(String(128), index=True, default="")
    status = Column(String(16), index=True, default="pending")
    
    estimated_datetime = Column(DateTime, nullable=True)
    
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    registered_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=get_local_time)

    registered_by = relationship("User", back_populates="guests", foreign_keys=[registered_by_user_id])
    images = relationship("GuestImage", back_populates="guest", cascade="all, delete-orphan")

class GuestImage(Base):
    __tablename__ = "guest_images"
    id = Column(Integer, primary_key=True, index=True)
    guest_id = Column(Integer, ForeignKey("guests.id"), nullable=False)
    image_path = Column(String(255), nullable=False)
    
    guest = relationship("Guest", back_populates="images")

class LongTermGuest(Base):
    __tablename__ = "long_term_guests"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(128), nullable=False)
    id_card_number = Column(String(32), default="")
    company = Column(String(128), default="")
    reason = Column(Text, default="")
    license_plate = Column(String(32), default="")
    supplier_name = Column(String(128), default="")
    
    estimated_datetime = Column(DateTime, nullable=True)
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    registered_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=get_local_time)

    registered_by = relationship("User", foreign_keys=[registered_by_user_id])
