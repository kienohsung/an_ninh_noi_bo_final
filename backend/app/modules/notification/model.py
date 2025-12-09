from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.time_utils import get_local_time

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False) 
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_local_time)

    user = relationship("User", back_populates="notifications")
