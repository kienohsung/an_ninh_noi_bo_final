from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date

class GuestImageRead(BaseModel):
    id: int
    image_path: str
    model_config = ConfigDict(from_attributes=True)

class GuestBase(BaseModel):
    full_name: str
    id_card_number: Optional[str] = ""
    company: Optional[str] = ""
    reason: Optional[str] = ""
    license_plate: Optional[str] = ""
    supplier_name: Optional[str] = ""
    estimated_datetime: Optional[datetime] = None

class GuestCreate(GuestBase):
    pass

class GuestUpdate(BaseModel):
    full_name: Optional[str] = None
    id_card_number: Optional[str] = None
    company: Optional[str] = None
    reason: Optional[str] = None
    license_plate: Optional[str] = None
    supplier_name: Optional[str] = None
    status: Optional[str] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    estimated_datetime: Optional[datetime] = None

class GuestRead(GuestBase):
    id: int
    status: str
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    registered_by_user_id: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class GuestReadWithUser(GuestRead):
    registered_by_name: Optional[str] = None
    images: List[GuestImageRead] = []

class GuestSuggestions(BaseModel):
    companies: List[str]
    license_plates: List[str]
    supplier_names: List[str]

class GuestIndividualCreate(BaseModel):
    full_name: str
    id_card_number: Optional[str] = ""

class GuestBulkCreate(BaseModel):
    guests: List[GuestIndividualCreate]
    company: Optional[str] = ""
    reason: Optional[str] = ""
    license_plate: Optional[str] = ""
    supplier_name: Optional[str] = ""
    estimated_datetime: Optional[datetime] = None

# ---------- LONG TERM GUESTS ----------
class LongTermGuestBase(BaseModel):
    full_name: str
    id_card_number: Optional[str] = ""
    company: Optional[str] = ""
    reason: Optional[str] = ""
    license_plate: Optional[str] = ""
    supplier_name: Optional[str] = ""
    start_date: date
    end_date: date
    estimated_datetime: Optional[datetime] = None

class LongTermGuestCreate(LongTermGuestBase):
    pass

class LongTermGuestUpdate(BaseModel):
    full_name: Optional[str] = None
    id_card_number: Optional[str] = None
    company: Optional[str] = None
    reason: Optional[str] = None
    license_plate: Optional[str] = None
    supplier_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    estimated_datetime: Optional[datetime] = None

class LongTermGuestRead(LongTermGuestBase):
    id: int
    is_active: bool
    registered_by_user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class LongTermGuestReadWithUser(LongTermGuestRead):
    registered_by_name: Optional[str] = None
