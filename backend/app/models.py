# Facade for backward compatibility and easy imports
# This file re-exports models from their new modular locations.
# It does NOT import Base itself.
# This file re-exports models from their new modular locations.

from app.modules.user.model import User, get_local_time
from app.modules.guest.model import Guest, GuestImage, LongTermGuest
from app.modules.asset.model import (
    AssetLog, AssetImage, 
    ASSET_STATUS_PENDING_OUT, ASSET_STATUS_CHECKED_OUT, ASSET_STATUS_RETURNED
)
from app.modules.supplier.model import Supplier, SupplierPlate
from app.modules.purchasing.model import (
    PurchasingLog, PurchasingImage,
    PURCHASING_STATUS_NEW, PURCHASING_STATUS_PENDING, 
    PURCHASING_STATUS_APPROVED, PURCHASING_STATUS_REJECTED
)

# Re-export handy things if needed, but preferably use modules directly.