from pydantic import BaseModel, ConfigDict
from typing import Optional, List

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
