# File: backend/app/schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime, date

# ---------- NORMALIZATION SCHEMAS ----------
# Đặt trực tiếp ở đây để tránh circular import
class SupplierVariant(BaseModel):
    """Một biến thể tên nhà cung cấp"""
    name: str
    count: int
    tables: List[str]

class SupplierGroup(BaseModel):
    """Một nhóm các tên tương tự"""
    variants: List['SupplierVariant']
    suggested_name: str
    total_records: int
    similarity_score: float

class NormalizationAnalysis(BaseModel):
    """Kết quả phân tích toàn bộ"""
    groups: List[SupplierGroup]
    total_groups: int

class NormalizationRequest(BaseModel):
    """Request để thực hiện normalization"""
    mappings: Dict[str, str]

class NormalizationPreview(BaseModel):
    """Preview số lượng bản ghi sẽ bị ảnh hưởng"""
    guests: int
    long_term_guests: int
    purchasing_log: int
    total: int

class NormalizationResult(BaseModel):
    """Kết quả sau khi thực hiện normalization"""
    success: bool
    updated_records: Dict[str, int]
    errors: List[str] = []

# ---------- AUTH ----------
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserBase(BaseModel):
    username: str
    full_name: str
    role: str

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None

class UserRead(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ---------- GUESTS & IMAGES ----------
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
    # --- NÂNG CẤP: Thay estimated_time bằng estimated_datetime ---
    # (Đã xóa trường estimated_time cũ)
    estimated_datetime: Optional[datetime] = None
    # --- KẾT THÚC NÂNG CẤP ---

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
    # --- NÂNG CẤP: Thay estimated_time bằng estimated_datetime ---
    # (Đã xóa trường estimated_time cũ)
    estimated_datetime: Optional[datetime] = None
    # --- KẾT THÚC NÂNG CẤP ---

class GuestRead(GuestBase):
    id: int
    status: str
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    registered_by_user_id: Optional[int] = None
    created_at: datetime
    # estimated_datetime được kế thừa từ GuestBase
    model_config = ConfigDict(from_attributes=True)

class GuestReadWithUser(GuestRead):
    registered_by_name: Optional[str] = None
    images: List[GuestImageRead] = []

# === CHECKLIST 1.4: Tạo Pydantic schemas cho AssetLog ===
class AssetImageRead(BaseModel):
    id: int
    image_path: str
    model_config = ConfigDict(from_attributes=True)

class AssetLogBase(BaseModel):
    destination: str
    description_reason: str  # Required field - no default value
    asset_description: str  # Asset/item name
    quantity: int
    department: str
    expected_return_date: Optional[date] = None
    estimated_datetime: Optional[datetime] = None  # CẢI TIẾN 3
    vietnamese_manager_name: Optional[str] = None
    korean_manager_name: Optional[str] = None

class AssetLogCreate(AssetLogBase):
    pass

# === CẢI TIẾN 2: Schema cho update asset ===
class AssetLogUpdate(BaseModel):
    destination: Optional[str] = None
    description_reason: Optional[str] = None
    asset_description: Optional[str] = None
    quantity: Optional[int] = None
    department: Optional[str] = None
    expected_return_date: Optional[date] = None
    estimated_datetime: Optional[datetime] = None
    vietnamese_manager_name: Optional[str] = None
    korean_manager_name: Optional[str] = None
# === KẾT THÚC CẢI TIẾN 2 ===

class AssetLogDisplay(AssetLogBase):
    id: int
    # department: str # (Đã kế thừa từ AssetLogBase)
    status: str
    created_at: datetime
    check_out_time: Optional[datetime] = None
    check_in_back_time: Optional[datetime] = None
    
    # Thông tin lồng ghép từ user
    registered_by: UserRead
    check_out_by: Optional[UserRead] = None
    check_in_back_by: Optional[UserRead] = None
    
    # Images
    images: List[AssetImageRead] = []
    
    model_config = ConfigDict(from_attributes=True)
# === KẾT THÚC CHECKLIST 1.4 ===

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
    # --- NÂNG CẤP: Thay estimated_time bằng estimated_datetime ---
    # (Đã xóa trường estimated_time cũ)
    estimated_datetime: Optional[datetime] = None
    # --- KẾT THÚC NÂNG CẤP ---

class TokenRefreshRequest(BaseModel):
    refresh_token: str

# ---------- SUPPLIERS ----------
class SupplierBase(BaseModel):
    name: str

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    name: Optional[str] = None

class SupplierPlateBase(BaseModel):
    plate: str

class SupplierPlateCreate(SupplierPlateBase):
    pass

class SupplierPlateRead(SupplierPlateBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class SupplierRead(SupplierBase):
    id: int
    plates: List[SupplierPlateRead] = []
    model_config = ConfigDict(from_attributes=True)

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
    # --- NÂNG CẤP: Thay estimated_time bằng estimated_datetime ---
    # (Đã xóa trường estimated_time cũ)
    estimated_datetime: Optional[datetime] = None
    # --- KẾT THÚC NÂNG CẤP ---

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
    # --- NÂNG CẤP: Thay estimated_time bằng estimated_datetime ---
    # (Đã xóa trường estimated_time cũ)
    estimated_datetime: Optional[datetime] = None
    # --- KẾT THÚC NÂNG CẤP ---

class LongTermGuestRead(LongTermGuestBase):
    id: int
    is_active: bool
    registered_by_user_id: int
    created_at: datetime
    # estimated_datetime được kế thừa từ LongTermGuestBase
    model_config = ConfigDict(from_attributes=True)

# SỬA LỖI: Thêm schema LongTermGuestReadWithUser
class LongTermGuestReadWithUser(LongTermGuestRead):
    registered_by_name: Optional[str] = None

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
# === KẾT THÚC SECURITY EVENT SCHEMAS ===
