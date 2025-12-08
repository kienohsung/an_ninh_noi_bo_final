# File: security_mgmt_dev/backend/app/routers/reports.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from .. import models
from ..core.deps import get_db
from ..core.auth import require_roles

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(require_roles("admin", "manager"))])


@router.get("/guests_daily")
def guests_daily(db: Session = Depends(get_db), start: datetime | None = None, end: datetime | None = None):
    """Thống kê lượt khách vào theo từng ngày."""
    from ..modules.report.service import report_service
    return report_service.guests_daily(db, start, end)

@router.get("/guests_by_user")
def guests_by_user(db: Session = Depends(get_db), start: datetime | None = None, end: datetime | None = None):
    """Thống kê lượt khách theo người đăng ký."""
    from ..modules.report.service import report_service
    return report_service.guests_by_user(db, start, end)

@router.get("/guests_by_supplier")
def guests_by_supplier(db: Session = Depends(get_db), start: datetime | None = None, end: datetime | None = None):
    """Thống kê lượt khách theo nhà cung cấp."""
    from ..modules.report.service import report_service
    return report_service.guests_by_supplier(db, start, end)

@router.get("/guests_by_plate")
def guests_by_plate(db: Session = Depends(get_db), start: datetime | None = None, end: datetime | None = None, limit: int = 10):
    """Thống kê top 10 xe vào nhiều nhất."""
    from ..modules.report.service import report_service
    return report_service.guests_by_plate(db, start, end, limit)

@router.get("/assets_by_status")
def assets_by_status(
    db: Session = Depends(get_db), 
    start: datetime | None = None, 
    end: datetime | None = None
):
    """Thống kê số lượng tài sản theo trạng thái."""
    from ..modules.report.service import report_service
    return report_service.assets_by_status(db, start, end)

@router.get("/assets_daily")
def assets_daily(
    db: Session = Depends(get_db),
    start: datetime | None = None,
    end: datetime | None = None
):
    """Thống kê tài sản ra/vào theo ngày và tổng tích luỹ tài sản ra."""
    from ..modules.report.service import report_service
    return report_service.assets_daily(db, start, end)

@router.get("/visitor-security-index")
def visitor_security_index(
    db: Session = Depends(get_db),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    supplier_name: str | None = None
):
    """Phân tích chỉ số an ninh khách theo tháng."""
    try:
        from ..modules.report.service import report_service
        return report_service.visitor_security_index(db, start_date, end_date, supplier_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/asset-control")
def asset_control(
    db: Session = Depends(get_db),
    start: datetime | None = None,
    end: datetime | None = None,
    include_returned: bool = False
):
    """Kiểm soát tài sản quá hạn và tỷ lệ hoàn trả."""
    try:
        from ..modules.report.service import report_service
        return report_service.asset_control(db, start, end)
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.get("/system-overview")
def system_overview(
    db: Session = Depends(get_db),
    start: datetime | None = None,
    end: datetime | None = None
):
    """Tổng quan hệ thống với các KPIs quan trọng."""
    try:
        from ..modules.report.service import report_service
        return report_service.system_overview(db, start, end)
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-activity")
def user_activity(
    db: Session = Depends(get_db),
    start_date: datetime | None = None,
    end_date: datetime | None = None
):
    """Thống kê hoạt động của người dùng."""
    try:
        from ..modules.report.service import report_service
        return report_service.user_activity(db, start_date, end_date)
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

