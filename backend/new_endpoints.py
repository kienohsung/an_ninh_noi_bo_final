
# === NEW REPORT ENDPOINTS FOR ANALYTICS ===

@router.get("/visitor-security-index", response_model=schemas.VisitorStatsResponse)
def visitor_security_index(
    db: Session = Depends(get_db),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    supplier_name: str | None = None
):
    """Visitor security index with monthly trends and statistics."""
    try:
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta
        import pytz
        from ..config import settings
        
        tz = pytz.timezone(settings.TZ)
        now = datetime.now(tz)
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = current_month_start - relativedelta(months=1)
        last_month_end = current_month_start - timedelta(seconds=1)
        
        # Current month count
        query_current = db.query(func.count(models.Guest.id)).filter(
            models.Guest.created_at >= current_month_start
        )
        if supplier_name:
            query_current = query_current.filter(models.Guest.supplier_name == supplier_name)
        total_current_month = query_current.scalar() or 0
        
        # Last month count
        query_last = db.query(func.count(models.Guest.id)).filter(
            models.Guest.created_at >= last_month_start,
            models.Guest.created_at <= last_month_end
        )
        if supplier_name:
            query_last = query_last.filter(models.Guest.supplier_name == supplier_name)
        total_last_month = query_last.scalar() or 0
        
        # Growth percentage
        if total_last_month > 0:
            growth_percentage = ((total_current_month - total_last_month) / total_last_month) * 100
        else:
            growth_percentage = 100.0 if total_current_month > 0 else 0.0
        
        # Monthly data (12 months)
        twelve_months_ago = current_month_start - relativedelta(months=11)
        query_monthly = db.query(
            func.strftime('%Y-%m', models.Guest.created_at).label('month'),
            func.count(models.Guest.id).label('total'),
            func.sum(func.case((models.Guest.status == 'pending', 1), else_=0)).label('pending'),
            func.sum(func.case((models.Guest.status == 'checked_in', 1), else_=0)).label('checked_in'),
            func.sum(func.case((models.Guest.status == 'checked_out', 1), else_=0)).label('checked_out')
        ).filter(models.Guest.created_at >= twelve_months_ago)
        
        if supplier_name:
            query_monthly = query_monthly.filter(models.Guest.supplier_name == supplier_name)
        
        monthly_results = query_monthly.group_by('month').order_by('month').all()
        monthly_data = [
            schemas.MonthlyGuestData(
                month=row.month,
                total=row.total,
                pending=row.pending or 0,
                checked_in=row.checked_in or 0,
                checked_out=row.checked_out or 0
            )
            for row in monthly_results
        ]
        
        # Daily trend (30 days)
        thirty_days_ago = now - timedelta(days=30)
        query_daily = db.query(
            func.date(models.Guest.created_at).label('date'),
            func.count(models.Guest.id).label('count')
        ).filter(models.Guest.created_at >= thirty_days_ago)
        
        if supplier_name:
            query_daily = query_daily.filter(models.Guest.supplier_name == supplier_name)
        
        daily_results = query_daily.group_by('date').order_by('date').all()
        daily_trend = [
            schemas.DailyGuestTrend(date=str(row.date), count=row.count)
            for row in daily_results
        ]
        
        # Top suppliers
        query_suppliers = db.query(
            models.Guest.supplier_name,
            func.count(models.Guest.id).label('count')
        ).filter(
            models.Guest.supplier_name != "",
            models.Guest.supplier_name != None
        )
        
        if start_date:
            query_suppliers = query_suppliers.filter(models.Guest.created_at >= start_date)
        if end_date:
            query_suppliers = query_suppliers.filter(models.Guest.created_at <= end_date)
        
        supplier_results = query_suppliers.group_by(models.Guest.supplier_name).order_by(
            desc(func.count(models.Guest.id))
        ).limit(5).all()
        
        top_suppliers = [
            schemas.SupplierStats(supplier_name=row.supplier_name, guest_count=row.count)
            for row in supplier_results
        ]
        
        # Status breakdown
        query_status = db.query(
            func.sum(func.case((models.Guest.status == 'pending', 1), else_=0)).label('pending'),
            func.sum(func.case((models.Guest.status == 'checked_in', 1), else_=0)).label('checked_in'),
            func.sum(func.case((models.Guest.status == 'checked_out', 1), else_=0)).label('checked_out')
        ).filter(models.Guest.created_at >= current_month_start)
        
        if supplier_name:
            query_status = query_status.filter(models.Guest.supplier_name == supplier_name)
        
        status_row = query_status.first()
        status_breakdown = schemas.StatusBreakdown(
            pending=status_row.pending or 0,
            checked_in=status_row.checked_in or 0,
            checked_out=status_row.checked_out or 0
        )
        
        return schemas.VisitorStatsResponse(
            total_guests_current_month=total_current_month,
            total_guests_last_month=total_last_month,
            growth_percentage=round(growth_percentage, 2),
            monthly_data=monthly_data,
            daily_trend=daily_trend,
            top_suppliers=top_suppliers,
            status_breakdown=status_breakdown
        )
    except Exception as e:
        logger.error(f"Error in visitor_security_index: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/asset-control", response_model=schemas.AssetControlResponse)
def asset_control(db: Session = Depends(get_db), include_returned: bool = False):
    """Asset control with overdue detection and risk levels."""
    try:
        import pytz
        from ..config import settings
        
        tz = pytz.timezone(settings.TZ)
        today = datetime.now(tz).date()
        
        total_assets_out = db.query(func.count(models.AssetLog.id)).filter(
            models.AssetLog.status.in_(['pending_out', 'checked_out'])
        ).scalar() or 0
        
        total_assets_returned = db.query(func.count(models.AssetLog.id)).filter(
            models.AssetLog.status == 'returned'
        ).scalar() or 0
        
        total_assets = total_assets_out + total_assets_returned
        return_rate_percentage = (total_assets_returned / total_assets * 100) if total_assets > 0 else 0.0
        
        # Overdue assets
        overdue_query = db.query(models.AssetLog, models.User.full_name.label('user_full_name')).join(
            models.User, models.AssetLog.registered_by_user_id == models.User.id
        ).filter(
            models.AssetLog.expected_return_date < today,
            models.AssetLog.status != 'returned'
        ).order_by(models.AssetLog.expected_return_date.asc())
        
        overdue_results = overdue_query.all()
        overdue_assets = []
        high_risk_count = 0
        
        for asset, user_name in overdue_results:
            days_overdue = (today - asset.expected_return_date).days
            
            if days_overdue > 7:
                risk_level = "high"
                high_risk_count += 1
            elif days_overdue > 3:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            overdue_assets.append(schemas.OverdueAssetDetail(
                id=asset.id,
                asset_description=asset.asset_description,
                full_name=user_name,
                employee_code=asset.employee_code,
                department=asset.department,
                expected_return_date=asset.expected_return_date,
                days_overdue=days_overdue,
                risk_level=risk_level,
                destination=asset.destination,
                created_at=asset.created_at
            ))
        
        return schemas.AssetControlResponse(
            total_assets_out=total_assets_out,
            total_assets_returned=total_assets_returned,
            return_rate_percentage=round(return_rate_percentage, 2),
            overdue_assets=overdue_assets,
            overdue_count=len(overdue_assets),
            high_risk_count=high_risk_count
        )
    except Exception as e:
        logger.error(f"Error in asset_control: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-overview", response_model=schemas.SystemOverviewResponse)
def system_overview(db: Session = Depends(get_db)):
    """System overview with aggregate KPIs."""
    try:
        import pytz
        from ..config import settings
        
        tz = pytz.timezone(settings.TZ)
        today_start = datetime.combine(datetime.now(tz).date(), datetime.min.time(), tzinfo=tz)
        
        total_users = db.query(func.count(models.User.id)).scalar() or 0
        total_guests_all_time = db.query(func.count(models.Guest.id)).scalar() or 0
        total_assets_all_time = db.query(func.count(models.AssetLog.id)).scalar() or 0
        active_guests_today = db.query(func.count(models.Guest.id)).filter(
            models.Guest.created_at >= today_start
        ).scalar() or 0
        active_assets_today = db.query(func.count(models.AssetLog.id)).filter(
            models.AssetLog.status.in_(['pending_out', 'checked_out'])
        ).scalar() or 0
        
        # Average processing time in minutes
        avg_query = db.query(
            func.avg((func.julianday(models.Guest.check_in_time) - func.julianday(models.Guest.created_at)) * 24 * 60)
        ).filter(models.Guest.check_in_time != None).scalar()
        
        avg_processing_time = round(avg_query, 2) if avg_query else None
        
        return schemas.SystemOverviewResponse(
            total_users=total_users,
            total_guests_all_time=total_guests_all_time,
            total_assets_all_time=total_assets_all_time,
            active_guests_today=active_guests_today,
            active_assets_today=active_assets_today,
            avg_processing_time_minutes=avg_processing_time
        )
    except Exception as e:
        logger.error(f"Error in system_overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-activity", response_model=schemas.UserActivityResponse)
def user_activity(
    db: Session = Depends(get_db),
    start_date: datetime | None = None,
    end_date: datetime | None = None
):
    """User activity statistics with performance scores."""
    try:
        users = db.query(models.User).all()
        user_stats = []
        
        for user in users:
            # Count guests registered by this user
            guests_query = db.query(func.count(models.Guest.id)).filter(
                models.Guest.registered_by_user_id == user.id
            )
            if start_date:
                guests_query = guests_query.filter(models.Guest.created_at >= start_date)
            if end_date:
                guests_query = guests_query.filter(models.Guest.created_at <= end_date)
            guests_count = guests_query.scalar() or 0
            
            # Count assets registered by this user
            assets_query = db.query(func.count(models.AssetLog.id)).filter(
                models.AssetLog.registered_by_user_id == user.id
            )
            if start_date:
                assets_query = assets_query.filter(models.AssetLog.created_at >= start_date)
            if end_date:
                assets_query = assets_query.filter(models.AssetLog.created_at <= end_date)
            assets_count = assets_query.scalar() or 0
            
            performance_score = guests_count + assets_count
            
            user_stats.append(schemas.UserActivityStats(
                user_id=user.id,
                full_name=user.full_name,
                department=user.department or "",
                guests_registered=guests_count,
                assets_registered=assets_count,
                performance_score=float(performance_score)
            ))
        
        # Sort by performance score descending
        user_stats.sort(key=lambda x: x.performance_score, reverse=True)
        
        # Format date range string
        if start_date and end_date:
            date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        elif start_date:
            date_range = f"From {start_date.strftime('%Y-%m-%d')}"
        elif end_date:
            date_range = f"Until {end_date.strftime('%Y-%m-%d')}"
        else:
            date_range = "All time"
        
        return schemas.UserActivityResponse(
            users=user_stats,
            date_range=date_range
        )
    except Exception as e:
        logger.error(f"Error in user_activity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
