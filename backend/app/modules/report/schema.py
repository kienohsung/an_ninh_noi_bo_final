from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date

# Visitor Security Index Schemas
class MonthlyDataPoint(BaseModel):
    month: str  # Format: "2025-01"
    count: int

class DailyTrendPoint(BaseModel):
    date: str  # Format: "2025-01-15"
    count: int

class SupplierStat(BaseModel):
    supplier_name: str
    count: int

class StatusBreakdown(BaseModel):
    pending: int
    checked_in: int
    checked_out: int

class VisitorStatsResponse(BaseModel):
    total_guests_current_month: int
    total_guests_last_month: int
    growth_percentage: float
    monthly_data: List[MonthlyDataPoint]
    daily_trend: List[DailyTrendPoint]
    top_suppliers: List[SupplierStat]
    status_breakdown: StatusBreakdown

# Asset Control Schemas
class OverdueAssetDetail(BaseModel):
    id: int
    asset_description: str
    employee_name: str
    employee_code: str
    expected_return_date: date
    days_overdue: int
    risk_level: str  # "HIGH", "MEDIUM", "LOW"
    model_config = ConfigDict(from_attributes=True)

class AssetControlResponse(BaseModel):
    total_assets_out: int
    total_assets_returned: int
    return_rate_percentage: float
    overdue_assets: List[OverdueAssetDetail]
    overdue_count: int
    high_risk_count: int  # quá hạn > 7 ngày

# System Overview Schemas
class SystemOverviewResponse(BaseModel):
    total_users: int
    total_guests_all_time: int
    total_assets_all_time: int
    active_guests_today: int
    active_assets_today: int
    avg_checkin_time_minutes: Optional[float] = None

# User Activity Schemas
class UserActivityStat(BaseModel):
    user_id: int
    full_name: str
    department: Optional[str] = None
    guests_registered: int
    assets_registered: int
    performance_score: float

class UserActivityResponse(BaseModel):
    users: List[UserActivityStat]
