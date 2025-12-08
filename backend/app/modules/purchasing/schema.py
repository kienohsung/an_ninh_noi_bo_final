from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PurchasingLogCreate(BaseModel):
    creator_name: str = Field(..., min_length=1, max_length=128)
    department: str = Field(default="", max_length=128)
    using_department: str = Field(default="", max_length=128)
    category: str = Field(..., min_length=1, max_length=64)
    item_name: str = Field(..., min_length=1, max_length=255)
    supplier_name: str = Field(default="", max_length=128)
    approved_price: int = Field(default=0, ge=0)

class PurchasingLogUpdate(BaseModel):
    creator_name: Optional[str] = Field(None, max_length=128)
    department: Optional[str] = Field(None, max_length=128)
    using_department: Optional[str] = Field(None, max_length=128)
    category: Optional[str] = Field(None, max_length=64)
    item_name: Optional[str] = Field(None, max_length=255)
    supplier_name: Optional[str] = Field(None, max_length=128)
    approved_price: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None)

class PurchasingImageRead(BaseModel):
    id: int
    purchasing_id: int
    image_path: str
    image_type: str = "request"

    class Config:
        from_attributes = True

class PurchasingLogRead(BaseModel):
    id: int
    creator_name: str
    department: str
    using_department: str
    category: str
    item_name: str
    supplier_name: str
    approved_price: int
    status: str
    created_at: Optional[datetime]
    received_at: Optional[datetime]
    received_note: Optional[str]
    images: List[PurchasingImageRead] = []

    class Config:
        from_attributes = True
