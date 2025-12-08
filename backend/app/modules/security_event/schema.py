from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas import AssetImageRead

# === SECURITY EVENT SCHEMAS (Zero Migration Strategy) ===
# Mapping: SecurityEvent fields -> AssetLog columns
# title -> asset_description
# occurred_at -> estimated_datetime
# location -> destination
# involved_parties -> department
# detail + resolution -> description_reason (formatted text)
# status: hardcode "security_event"
# quantity: hardcode 1
# employee_code: hardcode "EVENT"

class SecurityEventBase(BaseModel):
    """Schema nghiệp vụ cho Sự kiện An ninh - Frontend friendly"""
    title: str                                    # Tiêu đề sự kiện (bắt buộc)
    occurred_at: datetime                         # Thời điểm xảy ra (bắt buộc)
    location: str                                 # Địa điểm (bắt buộc)
    involved_parties: Optional[str] = ""          # Các bên liên quan
    detail: Optional[str] = ""                    # Nội dung chi tiết
    resolution: Optional[str] = ""                # Hướng giải quyết

class SecurityEventCreate(SecurityEventBase):
    """Schema tạo mới sự kiện - nhận từ Frontend"""
    pass

class SecurityEventUpdate(BaseModel):
    """Schema cập nhật sự kiện"""
    title: Optional[str] = None
    occurred_at: Optional[datetime] = None
    location: Optional[str] = None
    involved_parties: Optional[str] = None
    detail: Optional[str] = None
    resolution: Optional[str] = None

class SecurityEventRead(BaseModel):
    """Schema trả về cho Frontend - đã parse từ AssetLog"""
    id: int
    title: str                                    # Parsed from asset_description
    occurred_at: Optional[datetime] = None        # Parsed from estimated_datetime
    location: str                                 # Parsed from destination
    involved_parties: str                         # Parsed from department
    detail: str                                   # Parsed from description_reason
    resolution: str                               # Parsed from description_reason
    reported_by_name: str                         # Người báo cáo
    created_at: datetime
    images: List[AssetImageRead] = []             # Tái sử dụng AssetImageRead
    model_config = ConfigDict(from_attributes=True)
