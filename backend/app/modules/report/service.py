from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta, date as date_type
from typing import List, Optional, Dict, Any
import logging
import pytz

from app import models, schemas
from app.core import config

logger = logging.getLogger(__name__)

# Constants
SECURITY_EVENT_STATUS = "security_event"

class ReportService:
    @staticmethod
    def apply_time_filters(query, model, start: datetime | None, end: datetime | None):
        """
        Áp dụng bộ lọc thời gian cho một câu truy vấn SQLAlchemy.
        Sử dụng cột 'check_in_time' cho Guest model.
        """
        time_column = model.check_in_time
        if start:
            query = query.filter(time_column >= start)
        if end:
            query = query.filter(time_column <= end)
        return query

    def guests_daily(self, db: Session, start: datetime | None = None, end: datetime | None = None) -> Dict[str, List]:
        try:
            query = db.query(func.date(models.Guest.check_in_time), func.count(models.Guest.id))\
                      .filter(models.Guest.status == "checked_in")
            
            query = self.apply_time_filters(query, models.Guest, start, end)
            data = query.group_by(func.date(models.Guest.check_in_time)).order_by(func.date(models.Guest.check_in_time)).all()
            return {"labels": [str(d or "") for d, _ in data], "series": [c for _, c in data]}
        except Exception as e:
            logger.error(f"Error in guests_daily: {e}", exc_info=True)
            return {"labels": [], "series": []}

    def guests_by_user(self, db: Session, start: datetime | None = None, end: datetime | None = None) -> Dict[str, List]:
        try:
            query = db.query(models.User.full_name, func.count(models.Guest.id))\
                      .join(models.User, models.Guest.registered_by_user_id == models.User.id)\
                      .filter(models.Guest.status == "checked_in")

            query = self.apply_time_filters(query, models.Guest, start, end)
            data = query.group_by(models.User.full_name).all()
            return {"labels": [str(d or "") for d, _ in data], "series": [c for _, c in data]}
        except Exception as e:
            logger.error(f"Error in guests_by_user: {e}", exc_info=True)
            return {"labels": [], "series": []}

    def guests_by_supplier(self, db: Session, start: datetime | None = None, end: datetime | None = None) -> Dict[str, List]:
        try:
            query = db.query(models.Guest.supplier_name, func.count(models.Guest.id))\
                      .filter(models.Guest.status == "checked_in", models.Guest.supplier_name != "")
            
            query = self.apply_time_filters(query, models.Guest, start, end)
            data = query.group_by(models.Guest.supplier_name).all()
            return {"labels": [str(d or "") for d, _ in data], "series": [c for _, c in data]}
        except Exception as e:
            logger.error(f"Error in guests_by_supplier: {e}", exc_info=True)
            return {"labels": [], "series": []}

    def guests_by_plate(self, db: Session, start: datetime | None = None, end: datetime | None = None, limit: int = 10) -> Dict[str, List]:
        try:
            query = db.query(models.Guest.license_plate, func.count(models.Guest.id))\
                      .filter(models.Guest.status == "checked_in", models.Guest.license_plate != "", models.Guest.license_plate != None)
            
            query = self.apply_time_filters(query, models.Guest, start, end)
            
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

    def assets_by_status(self, db: Session, start: datetime | None = None, end: datetime | None = None) -> Dict[str, List]:
        try:
            query = db.query(
                models.AssetLog.status,
                func.count(models.AssetLog.id).label('count')
            ).filter(
                models.AssetLog.status != SECURITY_EVENT_STATUS
            )
            
            if start:
                query = query.filter(models.AssetLog.created_at >= start)
            
            if end:
                query = query.filter(models.AssetLog.created_at <= end)
            
            results = query.group_by(models.AssetLog.status).all()
            
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

    def assets_daily(self, db: Session, start: datetime | None = None, end: datetime | None = None) -> Dict[str, List]:
        try:
            if start and end:
                start_date = start.date() if hasattr(start, 'date') else start
                end_date = end.date() if hasattr(end, 'date') else end
            else:
                earliest = db.query(func.min(models.AssetLog.created_at)).scalar()
                latest = db.query(func.max(models.AssetLog.created_at)).scalar()
                if not earliest or not latest:
                    return {
                        "labels": [],
                        "out_series": [],
                        "in_series": [],
                        "cumulative_series": []
                    }
                start_date = earliest.date()
                end_date = latest.date()
            
            query_out = db.query(
                func.date(models.AssetLog.created_at).label('date'),
                func.count(models.AssetLog.id).label('count')
            ).filter(
                models.AssetLog.status.in_(['pending_out', 'checked_out'])
            )
            
            if start:
                query_out = query_out.filter(models.AssetLog.created_at >= start)
            if end:
                query_out = query_out.filter(models.AssetLog.created_at <= end)
            
            out_data = query_out.group_by(func.date(models.AssetLog.created_at)).all()
            out_dict = {str(date): count for date, count in out_data}
            
            query_in = db.query(
                func.date(models.AssetLog.check_in_back_time).label('date'),
                func.count(models.AssetLog.id).label('count')
            ).filter(
                models.AssetLog.status == 'returned',
                models.AssetLog.check_in_back_time != None
            )
            
            if start:
                query_in = query_in.filter(models.AssetLog.check_in_back_time >= start)
            if end:
                query_in = query_in.filter(models.AssetLog.check_in_back_time <= end)
            
            in_data = query_in.group_by(func.date(models.AssetLog.check_in_back_time)).all()
            in_dict = {str(date): count for date, count in in_data}
            
            labels = []
            out_series = []
            in_series = []
            
            current_date = start_date
            while current_date <= end_date:
                date_str = str(current_date)
                labels.append(date_str)
                out_series.append(out_dict.get(date_str, 0))
                in_series.append(in_dict.get(date_str, 0))
                current_date += timedelta(days=1)
            
            cumulative_series = []
            cumulative = 0
            for out_count in out_series:
                cumulative += out_count
                cumulative_series.append(cumulative)
            
            return {
                "labels": labels,
                "out_series": out_series,
                "in_series": in_series,
                "cumulative_series": cumulative_series
            }
        except Exception as e:
            logger.error(f"Error in assets_daily: {e}", exc_info=True)
            return {
                "labels": [],
                "out_series": [],
                "in_series": [],
                "cumulative_series": []
            }

    def visitor_security_index(self, db: Session, start_date: datetime | None = None, end_date: datetime | None = None, supplier_name: str | None = None) -> schemas.VisitorStatsResponse:
        try:
            tz = pytz.timezone(config.settings.TZ)
            now = datetime.now(tz)
            
            current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            last_month_end = current_month_start - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            query_current = db.query(func.count(models.Guest.id)).filter(
                models.Guest.created_at >= current_month_start
            )
            if supplier_name:
                query_current = query_current.filter(models.Guest.supplier_name == supplier_name)
            total_current = query_current.scalar() or 0
            
            query_last = db.query(func.count(models.Guest.id)).filter(
                models.Guest.created_at >= last_month_start,
                models.Guest.created_at < current_month_start
            )
            if supplier_name:
                query_last = query_last.filter(models.Guest.supplier_name == supplier_name)
            total_last = query_last.scalar() or 0
            
            growth_pct = ((total_current - total_last) / total_last * 100) if total_last > 0 else 0.0
            
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
            raise e

    def asset_control(self, db: Session, start: datetime | None = None, end: datetime | None = None) -> schemas.AssetControlResponse:
        try:
            tz = pytz.timezone(config.settings.TZ)
            today = datetime.now(tz).date()
            
            base_query = db.query(models.AssetLog).filter(
                models.AssetLog.status != SECURITY_EVENT_STATUS
            )
            if start:
                base_query = base_query.filter(models.AssetLog.created_at >= start)
            if end:
                base_query = base_query.filter(models.AssetLog.created_at <= end)
            
            total_out = base_query.filter(
                models.AssetLog.status.in_(['pending_out', 'checked_out']),
                models.AssetLog.estimated_datetime != None 
            ).count() or 0
            
            total_returned = base_query.filter(
                models.AssetLog.status == 'returned'
            ).count() or 0
            
            total_all = total_out + total_returned
            return_rate = (total_returned / total_all * 100) if total_all > 0 else 0.0
            
            overdue_query = base_query.join(
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
            raise e

    def system_overview(self, db: Session, start: datetime | None = None, end: datetime | None = None) -> schemas.SystemOverviewResponse:
        try:
            tz = pytz.timezone(config.settings.TZ)
            now = datetime.now(tz)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            total_users = db.query(func.count(models.User.id)).scalar() or 0
            
            guest_query = db.query(func.count(models.Guest.id))
            if start:
                guest_query = guest_query.filter(models.Guest.created_at >= start)
            if end:
                guest_query = guest_query.filter(models.Guest.created_at <= end)
            total_guests = guest_query.scalar() or 0
            
            asset_query = db.query(func.count(models.AssetLog.id)).filter(
                models.AssetLog.status != SECURITY_EVENT_STATUS
            )
            if start:
                asset_query = asset_query.filter(models.AssetLog.created_at >= start)
            if end:
                asset_query = asset_query.filter(models.AssetLog.created_at <= end)
            total_assets = asset_query.scalar() or 0
            
            active_guests_today = db.query(func.count(models.Guest.id)).filter(
                models.Guest.check_in_time >= today_start,
                models.Guest.status == 'checked_in'
            ).scalar() or 0
            
            active_assets_today = db.query(func.count(models.AssetLog.id)).filter(
                models.AssetLog.created_at >= today_start,
                models.AssetLog.status != 'returned',
                models.AssetLog.status != SECURITY_EVENT_STATUS
            ).scalar() or 0
            
            return schemas.SystemOverviewResponse(
                total_users=total_users,
                total_guests_all_time=total_guests,
                total_assets_all_time=total_assets,
                active_guests_today=active_guests_today,
                active_assets_today=active_assets_today,
                avg_checkin_time_minutes=None
            )
        except Exception as e:
            logger.error(f"Error in system_overview: {e}", exc_info=True)
            raise e

    def user_activity(self, db: Session, start_date: datetime | None = None, end_date: datetime | None = None) -> schemas.UserActivityResponse:
        try:
            users = db.query(models.User).all()
            
            user_stats = []
            for user in users:
                guests_query = db.query(func.count(models.Guest.id)).filter(
                    models.Guest.registered_by_user_id == user.id
                )
                if start_date:
                    guests_query = guests_query.filter(models.Guest.created_at >= start_date)
                if end_date:
                    guests_query = guests_query.filter(models.Guest.created_at <= end_date)
                guests_count = guests_query.scalar() or 0
                
                assets_query = db.query(func.count(models.AssetLog.id)).filter(
                    models.AssetLog.registered_by_user_id == user.id,
                    models.AssetLog.status != SECURITY_EVENT_STATUS
                )
                if start_date:
                    assets_query = assets_query.filter(models.AssetLog.created_at >= start_date)
                if end_date:
                    assets_query = assets_query.filter(models.AssetLog.created_at <= end_date)
                assets_count = assets_query.scalar() or 0
                
                performance_score = (guests_count * 1.0) + (assets_count * 1.5)
                
                user_stats.append(schemas.UserActivityStat(
                    user_id=user.id,
                    full_name=user.full_name,
                    department=user.role, 
                    guests_registered=guests_count,
                    assets_registered=assets_count,
                    performance_score=round(performance_score, 2)
                ))
            
            user_stats.sort(key=lambda x: x.performance_score, reverse=True)
            
            return schemas.UserActivityResponse(users=user_stats)
        except Exception as e:
            logger.error(f"Error in user_activity: {e}", exc_info=True)
            raise e

report_service = ReportService()
