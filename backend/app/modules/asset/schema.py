from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from app.modules.user.schema import UserRead

class AssetImageRead(BaseModel):
    id: int
    image_path: str
    model_config = ConfigDict(from_attributes=True)

class AssetLogBase(BaseModel):
    destination: str
    description_reason: str
    asset_description: str
    quantity: int
    department: str
    expected_return_date: Optional[date] = None
    estimated_datetime: Optional[datetime] = None
    vietnamese_manager_name: Optional[str] = None
    korean_manager_name: Optional[str] = None

class AssetLogCreate(AssetLogBase):
    pass

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

class AssetLogDisplay(AssetLogBase):
    id: int
    status: str
    created_at: datetime
    check_out_time: Optional[datetime] = None
    check_in_back_time: Optional[datetime] = None
    
    # Print tracking
    print_count: int = 0
    
    # User info
    registered_by: UserRead
    check_out_by: Optional[UserRead] = None
    check_in_back_by: Optional[UserRead] = None
    
    # Images
    images: List[AssetImageRead] = []
    
    model_config = ConfigDict(from_attributes=True)
