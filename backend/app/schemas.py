# Facade for backward compatibility and easy imports
# This file re-exports schemas from their new modular locations.

from app.modules.user.schema import (
    Token, TokenRefreshRequest, UserBase, UserCreate, UserUpdate, UserRead
)
from app.modules.guest.schema import (
    GuestImageRead, GuestBase, GuestCreate, GuestUpdate, GuestRead, 
    GuestReadWithUser, GuestSuggestions, GuestIndividualCreate, GuestBulkCreate,
    LongTermGuestBase, LongTermGuestCreate, LongTermGuestUpdate, LongTermGuestRead,
    LongTermGuestReadWithUser
)
from app.modules.asset.schema import (
    AssetImageRead, AssetLogBase, AssetLogCreate, AssetLogUpdate, AssetLogDisplay
)
from app.modules.supplier.schema import (
    SupplierBase, SupplierCreate, SupplierUpdate, 
    SupplierPlateBase, SupplierPlateCreate, SupplierPlateRead, SupplierRead,
    # Normalization schemas
    SupplierVariant, SupplierGroup, NormalizationAnalysis,
    NormalizationRequest, NormalizationPreview, NormalizationResult
)
from app.modules.report.schema import (
    MonthlyDataPoint, DailyTrendPoint, SupplierStat, StatusBreakdown, 
    VisitorStatsResponse, OverdueAssetDetail, AssetControlResponse, 
    SystemOverviewResponse, UserActivityStat, UserActivityResponse
)
