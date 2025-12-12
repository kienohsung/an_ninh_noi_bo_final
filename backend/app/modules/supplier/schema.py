from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict

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

# ---------- NORMALIZATION ----------
class SupplierVariant(BaseModel):
    """Một biến thể tên nhà cung cấp"""
    name: str
    count: int  # Số lượng bản ghi sử dụng tên này
    tables: List[str]  # ["guests", "purchasing_log", "long_term_guests"]

class SupplierGroup(BaseModel):
    """Một nhóm các tên tương tự"""
    variants: List[SupplierVariant]
    suggested_name: str  # Tên xuất hiện nhiều nhất
    total_records: int
    similarity_score: float

class NormalizationAnalysis(BaseModel):
    """Kết quả phân tích toàn bộ"""
    groups: List[SupplierGroup]
    total_groups: int

class NormalizationRequest(BaseModel):
    """Request để thực hiện normalization"""
    mappings: Dict[str, str]  # {old_name: new_name}

class NormalizationPreview(BaseModel):
    """Preview số lượng bản ghi sẽ bị ảnh hưởng"""
    guests: int
    long_term_guests: int
    purchasing_log: int
    total: int

class NormalizationResult(BaseModel):
    """Kết quả sau khi thực hiện normalization"""
    success: bool
    updated_records: Dict[str, int]  # {table_name: count}
    errors: List[str] = []
