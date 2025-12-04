# File: security_mgmt_dev/backend/app/routers/reports.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, time, timedelta
import logging

from .. import models
from ..deps import get_db
from ..auth import require_roles

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(require_roles("admin", "manager"))])
logger = logging.getLogger(__name__)

def apply_time_filters(query, model, start: datetime | None, end: datetime | None):
    """
    Áp dụng bộ lọc thời gian cho một câu truy vấn SQLAlchemy.
    Sử dụng cột 'check_in_time' để lọc.
    """
    time_column = model.check_in_time
    if start:
        query = query.filter(time_column >= start)
    if end:
        # Frontend đã gửi mốc thời gian chính xác (23:59:59),
        # nên chỉ cần so sánh nhỏ hơn hoặc bằng.
        query = query.filter(time_column <= end)
    return query

@router.get("/guests_daily")
def guests_daily(db: Session = Depends(get_db), start: datetime | None = None, end: datetime | None = None):
    """Thống kê lượt khách vào theo từng ngày."""
    try:
        # Bỏ điều kiện lọc theo biển số, đếm tất cả khách đã check-in
        query = db.query(func.date(models.Guest.check_in_time), func.count(models.Guest.id))\
                  .filter(models.Guest.status == "checked_in")
        
        query = apply_time_filters(query, models.Guest, start, end)
        data = query.group_by(func.date(models.Guest.check_in_time)).order_by(func.date(models.Guest.check_in_time)).all()
        return {"labels": [str(d or "") for d, _ in data], "series": [c for _, c in data]}
    except Exception as e:
        logger.error(f"Error in guests_daily: {e}", exc_info=True)
        return {"labels": [], "series": []}

@router.get("/guests_by_user")
def guests_by_user(db: Session = Depends(get_db), start: datetime | None = None, end: datetime | None = None):
    """Thống kê lượt khách theo người đăng ký."""
    try:
        # Bỏ điều kiện lọc theo biển số, đếm tất cả khách đã check-in
        query = db.query(models.User.full_name, func.count(models.Guest.id))\
                  .join(models.User, models.Guest.registered_by_user_id == models.User.id)\
                  .filter(models.Guest.status == "checked_in")

        query = apply_time_filters(query, models.Guest, start, end)
        data = query.group_by(models.User.full_name).all()
        return {"labels": [str(d or "") for d, _ in data], "series": [c for _, c in data]}
    except Exception as e:
        logger.error(f"Error in guests_by_user: {e}", exc_info=True)
        return {"labels": [], "series": []}

@router.get("/guests_by_supplier")
def guests_by_supplier(db: Session = Depends(get_db), start: datetime | None = None, end: datetime | None = None):
    """Thống kê lượt khách theo nhà cung cấp."""
    try:
        # Bỏ điều kiện lọc theo biển số, đếm tất cả khách đã check-in
        query = db.query(models.Guest.supplier_name, func.count(models.Guest.id))\
                  .filter(models.Guest.status == "checked_in", models.Guest.supplier_name != "")
        
        query = apply_time_filters(query, models.Guest, start, end)
        data = query.group_by(models.Guest.supplier_name).all()
        return {"labels": [str(d or "") for d, _ in data], "series": [c for _, c in data]}
    except Exception as e:
        logger.error(f"Error in guests_by_supplier: {e}", exc_info=True)
        return {"labels": [], "series": []}

@router.get("/guests_by_plate")
def guests_by_plate(db: Session = Depends(get_db), start: datetime | None = None, end: datetime | None = None, limit: int = 10):
    """Thống kê top 10 xe vào nhiều nhất (vẫn giữ nguyên logic yêu cầu biển số)."""
    try:
        query = db.query(models.Guest.license_plate, func.count(models.Guest.id))\
                  .filter(models.Guest.status == "checked_in", models.Guest.license_plate != "", models.Guest.license_plate != None)
        
        query = apply_time_filters(query, models.Guest, start, end)
        
        data = query.group_by(models.Guest.license_plate)\
                   .order_by(desc(func.count(models.Guest.id)))\
                   .limit(limit)\
                   .all()
        
        if not data:
            return {"labels": [], "series": []}
            
        return {"labels": [str(d or "") for d, _ in data], "series": [c for _, c in data]}
    except Exception as e:
        logger.error(f"Error in guests_by_plate: {e}", exc_info=True)
        return {"labels": [], "series": []}


# === CẢI TIẾN 5: Endpoint thống kê tài sản theo trạng thái ===
@router.get("/assets_by_status")
def assets_by_status(
    db: Session = Depends(get_db), 
    start: datetime | None = None, 
    end: datetime | None = None
):
    """
    Thống kê số lượng tài sản theo trạng thái.
    
    Returns:
        {
            "labels": ["Chờ ra cổng", "Đã ra cổng", "Đã vào lại"],
            "series": [10, 5, 3]
        }
    """
    try:
        # Build query
        query = db.query(
            models.AssetLog.status,
            func.count(models.AssetLog.id).label('count')
        )
        
        # Apply date filters if provided (filter by created_at)
        if start:
            query = query.filter(models.AssetLog.created_at >= start)
        
        if end:
            query = query.filter(models.AssetLog.created_at <= end)
        
        # Group by status
        results = query.group_by(models.AssetLog.status).all()
        
        # Map status to Vietnamese labels
        status_labels = {
            'pending_out': 'Chờ ra cổng',
            'checked_out': 'Đã ra cổng',
            'returned': 'Đã vào lại'
        }
        
        labels = []
        series = []
        
        for status, count in results:
            label = status_labels.get(status, status)
            labels.append(label)
            series.append(count)
        
        return {
            "labels": labels,
            "series": series
        }
    except Exception as e:
        logger.error(f"Error in assets_by_status: {e}", exc_info=True)
        return {"labels": [], "series": []}
# === KẾT THÚC CẢI TIẾN 5 ===

# === MODULE REPORT v1.15.0: Visitor Security Index ===
@router.get("/visitor-security-index")
def visitor_security_index(
    db: Session = Depends(get_db),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    supplier_name: str | None = None
):
    """
    Phân tích chỉ số an ninh khách theo tháng.
    Returns: VisitorStatsResponse
    """
    try:
        import pytz
        from ..config import settings
        from .. import schemas
        
        # Lấy timezone Việt Nam
        tz = pytz.timezone(settings.TZ)
        now = datetime.now(tz)
        
        # Tháng hiện tại
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Tháng trước
        last_month_end = current_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Query tổng khách tháng hiện tại
        query_current = db.query(func.count(models.Guest.id)).filter(
            models.Guest.created_at >= current_month_start
        )
        if supplier_name:
            query_current = query_current.filter(models.Guest.supplier_name == supplier_name)
        total_current = query_current.scalar() or 0
        
        # Query tổng khách tháng trước
        query_last = db.query(func.count(models.Guest.id)).filter(
            models.Guest.created_at >= last_month_start,
            models.Guest.created_at < current_month_start
        )
        if supplier_name:
            query_last = query_last.filter(models.Guest.supplier_name == supplier_name)
        total_last = query_last.scalar() or 0
        
        # Tính growth percentage
        growth_pct = ((total_current - total_last) / total_last * 100) if total_last > 0 else 0.0
        
        # Monthly data (12 tháng gần nhất)
        monthly_data = []
        for i in range(11, -1, -1):
            month_date = now - timedelta(days=30*i)
            month_str = month_date.strftime("%Y-%m")
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i == 0:
                month_end = now
            else:
                next_month = month_start + timedelta(days=32)
                month_end = next_month.replace(day=1) - timedelta(seconds=1)
            
            count_query = db.query(func.count(models.Guest.id)).filter(
                models.Guest.created_at >= month_start,
                models.Guest.created_at <= month_end
            )    
            if supplier_name:
                count_query = count_query.filter(models.Guest.supplier_name == supplier_name)
            count = count_query.scalar() or 0
            monthly_data.append(schemas.MonthlyDataPoint(month=month_str, count=count))
        
        # Daily trend (30 ngày gần nhất)
        daily_trend = []
        for i in range(29, -1, -1):
            day = now - timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            count_query = db.query(func.count(models.Guest.id)).filter(
                models.Guest.created_at >= day_start,
                models.Guest.created_at <= day_end
            )
            if supplier_name:
                count_query = count_query.filter(models.Guest.supplier_name == supplier_name)
            count = count_query.scalar() or 0
            daily_trend.append(schemas.DailyTrendPoint(date=day_str, count=count))
        
        # Top 5 suppliers
        top_suppliers_query = db.query(
            models.Guest.supplier_name,
            func.count(models.Guest.id).label('count')
        ).filter(
            models.Guest.supplier_name != '',
            models.Guest.supplier_name != None
        ).group_by(models.Guest.supplier_name).order_by(desc(func.count(models.Guest.id))).limit(5)
        
        top_suppliers = [
            schemas.SupplierStat(supplier_name=name, count=count)
            for name, count in top_suppliers_query.all()
        ]
        
        # Status breakdown
        status_counts = db.query(
            models.Guest.status,
            func.count(models.Guest.id)
        ).filter(
            models.Guest.created_at >= current_month_start
        ).group_by(models.Guest.status).all()
        
        status_dict = {status: count for status, count in status_counts}
        status_breakdown = schemas.StatusBreakdown(
            pending=status_dict.get('pending', 0),
            checked_in=status_dict.get('checked_in', 0),
            checked_out=status_dict.get('checked_out', 0)
        )
        
        return schemas.VisitorStatsResponse(
            total_guests_current_month=total_current,
            total_guests_last_month=total_last,
            growth_percentage=round(growth_pct, 2),
            monthly_data=monthly_data,
            daily_trend=daily_trend,
            top_suppliers=top_suppliers,
            status_breakdown=status_breakdown
        )
    except Exception as e:
        logger.error(f"Error in visitor_security_index: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# === MODULE REPORT v1.15.0: Asset Control ===
@router.get("/asset-control")
def asset_control(
    db: Session = Depends(get_db),
    include_returned: bool = False
):
    """
    Kiểm soát tài sản quá hạn và tỷ lệ hoàn trả.
    Returns: AssetControlResponse
    """
    try:
        import pytz
        from ..config import settings
        from .. import schemas
        
        # Lấy ngày hiện tại theo timezone Việt Nam
        tz = pytz.timezone(settings.TZ)
        today = datetime.now(tz).date()
        
        # Đếm tài sản đang ra ngoài
        total_out = db.query(func.count(models.AssetLog.id)).filter(
            models.AssetLog.status.in_(['pending_out', 'checked_out'])
        ).scalar() or 0
        
        # Đếm tài sản đã hoàn trả
        total_returned = db.query(func.count(models.AssetLog.id)).filter(
            models.AssetLog.status == 'returned'
        ).scalar() or 0
        
        # Tính tỷ lệ hoàn trả
        total_all = total_out + total_returned
        return_rate = (total_returned / total_all * 100) if total_all > 0 else 0.0
        
        # Tìm tài sản quá hạn
        # CRITICAL FIX: Add NULL check for expected_return_date
        overdue_query = db.query(models.AssetLog).join(
            models.User, models.AssetLog.registered_by_user_id == models.User.id
        ).filter(
            models.AssetLog.expected_return_date != None,
            models.AssetLog.expected_return_date < today,
            models.AssetLog.status != 'returned'
        ).order_by(models.AssetLog.expected_return_date.asc())
        
        overdue_assets = []
        high_risk_count = 0
        
        for asset in overdue_query.all():
            try:
                days_overdue = (today - asset.expected_return_date).days
                
                # Xác định mức độ rủi ro
                if days_overdue > 7:
                    risk_level = "HIGH"
                    high_risk_count += 1
                elif days_overdue >= 3:
                    risk_level = "MEDIUM"
                else:
                    risk_level = "LOW"
                
                overdue_assets.append(schemas.OverdueAssetDetail(
                    id=asset.id,
                    asset_description=asset.asset_description or "N/A",
                    employee_name=asset.registered_by.full_name if asset.registered_by else "Unknown",
                    employee_code=asset.registered_by.username if asset.registered_by else "N/A",
                    expected_return_date=asset.expected_return_date,
                    days_overdue=days_overdue,
                    risk_level=risk_level
                ))
            except Exception as e:
                logger.error(f"Error processing asset {asset.id}: {e}")
                continue
        
        return schemas.AssetControlResponse(
            total_assets_out=total_out,
            total_assets_returned=total_returned,
            return_rate_percentage=round(return_rate, 2),
            overdue_assets=overdue_assets,
            overdue_count=len(overdue_assets),
            high_risk_count=high_risk_count
        )
    except Exception as e:
        logger.error(f"Error in asset_control: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# === MODULE REPORT v1.15.0: System Overview ===
@router.get("/system-overview")
def system_overview(db: Session = Depends(get_db)):
    """
    Tổng quan hệ thống với các KPIs quan trọng.
    Returns: SystemOverviewResponse
    """
    try:
        import pytz
        from ..config import settings
        from .. import schemas
        
        # Lấy timezone
        tz = pytz.timezone(settings.TZ)
        now = datetime.now(tz)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Tổng users
        total_users = db.query(func.count(models.User.id)).scalar() or 0
        
        # Tổng guests
        total_guests = db.query(func.count(models.Guest.id)).scalar() or 0
        
        # Tổng assets
        total_assets = db.query(func.count(models.AssetLog.id)).scalar() or 0
        
        # Khách active hôm nay (status = checked_in)
        active_guests_today = db.query(func.count(models.Guest.id)).filter(
            models.Guest.check_in_time >= today_start,
            models.Guest.status == 'checked_in'
        ).scalar() or 0
        
        # Assets active hôm nay (status != returned)
        active_assets_today = db.query(func.count(models.AssetLog.id)).filter(
            models.AssetLog.created_at >= today_start,
            models.AssetLog.status != 'returned'
        ).scalar() or 0
        
        # Avg checkin time (phút) - placeholder logic
        avg_checkin_time = None  # Cần logic tính toán nếu có dữ liệu
        
        return schemas.SystemOverviewResponse(
            total_users=total_users,
            total_guests_all_time=total_guests,
            total_assets_all_time=total_assets,
            active_guests_today=active_guests_today,
            active_assets_today=active_assets_today,
            avg_checkin_time_minutes=avg_checkin_time
        )
    except Exception as e:
        logger.error(f"Error in system_overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# === MODULE REPORT v1.15.0: User Activity ===
@router.get("/user-activity")
def user_activity(
    db: Session = Depends(get_db),
    start_date: datetime | None = None,
    end_date: datetime | None = None
):
    """
    Thống kê hoạt động của người dùng.
    Returns: UserActivityResponse
    """
    try:
        from .. import schemas
        
        # Query all users
        users = db.query(models.User).all()
        
        user_stats = []
        for user in users:
            # Đếm guests đã đăng ký
            guests_query = db.query(func.count(models.Guest.id)).filter(
                models.Guest.registered_by_user_id == user.id
            )
            if start_date:
                guests_query = guests_query.filter(models.Guest.created_at >= start_date)
            if end_date:
                guests_query = guests_query.filter(models.Guest.created_at <= end_date)
            guests_count = guests_query.scalar() or 0
            
            # Đếm assets đã đăng ký
            assets_query = db.query(func.count(models.AssetLog.id)).filter(
                models.AssetLog.registered_by_user_id == user.id
            )
            if start_date:
                assets_query = assets_query.filter(models.AssetLog.created_at >= start_date)
            if end_date:
                assets_query = assets_query.filter(models.AssetLog.created_at <= end_date)
            assets_count = assets_query.scalar() or 0
            
            # Tính performance score (simple formula)
            performance_score = (guests_count * 1.0) + (assets_count * 1.5)
            
            user_stats.append(schemas.UserActivityStat(
                user_id=user.id,
                full_name=user.full_name,
                department=user.role,  # Placeholder - có thể thay bằng field department
                guests_registered=guests_count,
                assets_registered=assets_count,
                performance_score=round(performance_score, 2)
            ))
        
        # Sắp xếp theo performance score giảm dần
        user_stats.sort(key=lambda x: x.performance_score, reverse=True)
        
        return schemas.UserActivityResponse(users=user_stats)
    except Exception as e:
        logger.error(f"Error in user_activity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

