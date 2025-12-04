# File: security_mgmt_dev/backend/app/routers/reports.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, time
import logging

from .. import models
from ..deps import get_db
from ..auth import require_roles

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(require_roles("admin", "manager"))])
logger = logging.getLogger(__name__)

def apply_time_filters(query, model, start: datetime | None, end: datetime | None):
    """
    √Åp d·ª•ng b·ªô l·ªçc th·ªùi gian cho m·ªôt c√¢u truy v·∫•n SQLAlchemy.
    S·ª≠ d·ª•ng c·ªôt 'check_in_time' ƒë·ªÉ l·ªçc.
    """
    time_column = model.check_in_time
    if start:
        query = query.filter(time_column >= start)
    if end:
        # Frontend ƒë√£ g·ª≠i m·ªëc th·ªùi gian ch√≠nh x√°c (23:59:59),
        # n√™n ch·ªâ c·∫ßn so s√°nh nh·ªè h∆°n ho·∫∑c b·∫±ng.
        query = query.filter(time_column <= end)
    return query

@router.get("/guests_daily")
def guests_daily(db: Session = Depends(get_db), start: datetime | None = None, end: datetime | None = None):
    """Th·ªëng k√™ l∆∞·ª£t kh√°ch v√†o theo t·ª´ng ng√†y."""
    try:
        # B·ªè ƒëi·ªÅu ki·ªán l·ªçc theo bi·ªÉn s·ªë, ƒë·∫øm t·∫•t c·∫£ kh√°ch ƒë√£ check-in
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
    """Th·ªëng k√™ l∆∞·ª£t kh√°ch theo ng∆∞·ªùi ƒëƒÉng k√Ω."""
    try:
        # B·ªè ƒëi·ªÅu ki·ªán l·ªçc theo bi·ªÉn s·ªë, ƒë·∫øm t·∫•t c·∫£ kh√°ch ƒë√£ check-in
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
    """Th·ªëng k√™ l∆∞·ª£t kh√°ch theo nh√† cung c·∫•p."""
    try:
        # B·ªè ƒëi·ªÅu ki·ªán l·ªçc theo bi·ªÉn s·ªë, ƒë·∫øm t·∫•t c·∫£ kh√°ch ƒë√£ check-in
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
    """Th·ªëng k√™ top 10 xe v√†o nhi·ªÅu nh·∫•t (v·∫´n gi·ªØ nguy√™n logic y√™u c·∫ßu bi·ªÉn s·ªë)."""
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


# === C·∫¢I TI·∫æN 5: Endpoint th·ªëng k√™ t√†i s·∫£n theo tr·∫°ng th√°i ===
@router.get("/assets_by_status")
def assets_by_status(
    db: Session = Depends(get_db), 
    start: datetime | None = None, 
    end: datetime | None = None
):
    """
    Th·ªëng k√™ s·ªë l∆∞·ª£ng t√†i s·∫£n theo tr·∫°ng th√°i.
    
    Returns:
        {
            "labels": ["Ch·ªù ra c·ªïng", "ƒê√£ ra c·ªïng", "ƒê√£ v√†o l·∫°i"],
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
            'pending_out': 'Ch·ªù ra c·ªïng',
            'checked_out': 'ƒê√£ ra c·ªïng',
            'returned': 'ƒê√£ v√†o l·∫°i'
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
# === K·∫æT TH√öC C·∫¢I TI·∫æN 5 ===


# ==========================================
# === NEW REPORT ENDPOINTS FOR ANALYTICS ===
# ==========================================

@router.get("/visitor-security-index")
def visitor_security_index(
    db: Session = Depends(get_db),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    supplier_name: str | None = None
):
    """
    Ch·ªâ s·ªë An ninh Kh√°ch - Visitor Security Index
    
    Returns:
        VisitorStatsResponse v·ªõi d·ªØ li·ªáu:
        - T·ªïng kh√°ch th√°ng hi·ªán t·∫°i vs th√°ng tr∆∞·ªõc
        - TƒÉng tr∆∞·ªüng %
        - D·ªØ li·ªáu theo th√°ng (12 th√°ng g·∫ßn nh·∫•t)
        - Xu h∆∞·ªõng theo ng√†y (30 ng√†y g·∫ßn nh·∫•t)
        - Top 5 nh√† cung c·∫•p
        - Ph√¢n b·ªë theo tr·∫°ng th√°i
    """
    try:
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta
        import pytz
        from ..config import settings
        from .. import schemas
        
        # L·∫•y timezone
        tz = pytz.timezone(settings.TZ)
        now = datetime.now(tz)
        
        # T√≠nh th√°ng hi·ªán t·∫°i v√† th√°ng tr∆∞·ªõc
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = current_month_start - relativedelta(months=1)
        last_month_end = current_month_start - timedelta(seconds=1)
        
        # 1. T·ªïng kh√°ch th√°ng hi·ªán t·∫°i
        query_current = db.query(func.count(models.Guest.id)).filter(
            models.Guest.created_at >= current_month_start
        )
        if supplier_name:
            query_current = query_current.filter(models.Guest.supplier_name == supplier_name)
        total_current_month = query_current.scalar() or 0
        
        # 2. T·ªïng kh√°ch th√°ng tr∆∞·ªõc
        query_last = db.query(func.count(models.Guest.id)).filter(
            models.Guest.created_at >= last_month_start,
            models.Guest.created_at <= last_month_end
        )
        if supplier_name:
            query_last = query_last.filter(models.Guest.supplier_name == supplier_name)
        total_last_month = query_last.scalar() or 0
        
        # 3. T√≠nh tƒÉng tr∆∞·ªüng %
        if total_last_month > 0:
            growth_percentage = ((total_current_month - total_last_month) / total_last_month) * 100
        else:
            growth_percentage = 100.0 if total_current_month > 0 else 0.0
        
        # 4. D·ªØ li·ªáu theo th√°ng (12 th√°ng g·∫ßn nh·∫•t)
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
        
        # 5. Xu h∆∞·ªõng theo ng√†y (30 ng√†y g·∫ßn nh·∫•t)
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
        
        # 6. Top 5 nh√† cung c·∫•p
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
        
        supplier_results = query_suppliers.group_by(models.Guest.supplier_name)\
                                         .order_by(desc(func.count(models.Guest.id)))\
                                         .limit(5).all()
        
        top_suppliers = [
            schemas.SupplierStats(supplier_name=row.supplier_name, guest_count=row.count)
            for row in supplier_results
        ]
        
        # 7. Ph√¢n b·ªë theo tr·∫°ng th√°i (th√°ng hi·ªán t·∫°i)
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

@ r o u t e r . g e t ( " / a s s e t - c o n t r o l " )  
 d e f   a s s e t _ c o n t r o l (  
         d b :   S e s s i o n   =   D e p e n d s ( g e t _ d b ) ,  
         i n c l u d e _ r e t u r n e d :   b o o l   =   F a l s e  
 ) :  
         " " "  
         K i · ª ím   s o √ ° t   T √ † i   s · ∫ £ n   -   A s s e t   C o n t r o l  
          
         R e t u r n s :  
                 A s s e t C o n t r o l R e s p o n s e   v · ª : i   d · ª Ø   l i · ª ! u :  
                 -   T · ª " n g   t √ † i   s · ∫ £ n   ƒ  a n g   r a   n g o √ † i  
                 -   T · ª " n g   t √ † i   s · ∫ £ n   ƒ  √ £   h o √ † n   t r · ∫ £  
                 -   T · ª ∑   l · ª !   h o √ † n   t r · ∫ £   %  
                 -   D a n h   s √ ° c h   t √ † i   s · ∫ £ n   q u √ °   h · ∫ ° n   ( Q U A N   T R · ª RN G )  
                 -   S · ª    l ∆ ∞ · ª £ n g   t √ † i   s · ∫ £ n   q u √ °   h · ∫ ° n  
                 -   S · ª    l ∆ ∞ · ª £ n g   r · ª ß i   r o   c a o   ( >   7   n g √ † y )  
         " " "  
         t r y :  
                 i m p o r t   p y t z  
                 f r o m   . . c o n f i g   i m p o r t   s e t t i n g s  
                 f r o m   . .   i m p o r t   s c h e m a s  
                  
                 #   L · ∫ • y   n g √ † y   h i · ª ! n   t · ∫ ° i   t h e o   t i m e z o n e   V i · ª ! t   N a m   ( C R I T I C A L )  
                 t z   =   p y t z . t i m e z o n e ( s e t t i n g s . T Z )  
                 t o d a y   =   d a t e t i m e . n o w ( t z ) . d a t e ( )  
                  
                 #   1 .   T · ª " n g   t √ † i   s · ∫ £ n   ƒ  a n g   r a   n g o √ † i   ( c h ∆ ∞ a   h o √ † n   t r · ∫ £ )  
                 t o t a l _ a s s e t s _ o u t   =   d b . q u e r y ( f u n c . c o u n t ( m o d e l s . A s s e t L o g . i d ) ) . f i l t e r (  
                         m o d e l s . A s s e t L o g . s t a t u s . i n _ ( [ ' p e n d i n g _ o u t ' ,   ' c h e c k e d _ o u t ' ] )  
                 ) . s c a l a r ( )   o r   0  
                  
                 #   2 .   T · ª " n g   t √ † i   s · ∫ £ n   ƒ  √ £   h o √ † n   t r · ∫ £  
                 t o t a l _ a s s e t s _ r e t u r n e d   =   d b . q u e r y ( f u n c . c o u n t ( m o d e l s . A s s e t L o g . i d ) ) . f i l t e r (  
                         m o d e l s . A s s e t L o g . s t a t u s   = =   ' r e t u r n e d '  
                 ) . s c a l a r ( )   o r   0  
                  
                 #   3 .   T √ ≠ n h   t · ª ∑   l · ª !   h o √ † n   t r · ∫ £  
                 t o t a l _ a s s e t s   =   t o t a l _ a s s e t s _ o u t   +   t o t a l _ a s s e t s _ r e t u r n e d  
                 i f   t o t a l _ a s s e t s   >   0 :  
                         r e t u r n _ r a t e _ p e r c e n t a g e   =   ( t o t a l _ a s s e t s _ r e t u r n e d   /   t o t a l _ a s s e t s )   *   1 0 0  
                 e l s e :  
                         r e t u r n _ r a t e _ p e r c e n t a g e   =   0 . 0  
                  
                 #   4 .   T √ RM   T √ ¨ I   S · ∫ ¢ N   Q U √ Å   H · ∫ † N   ( C R I T I C A L   F E A T U R E )  
                 #   L o g i c :   e x p e c t e d _ r e t u r n _ d a t e   <   t o d a y   A N D   s t a t u s   ! =   ' r e t u r n e d '  
                 o v e r d u e _ q u e r y   =   d b . q u e r y (  
                         m o d e l s . A s s e t L o g ,  
                         m o d e l s . U s e r . f u l l _ n a m e . l a b e l ( ' u s e r _ f u l l _ n a m e ' )  
                 ) . j o i n (  
                         m o d e l s . U s e r ,  
                         m o d e l s . A s s e t L o g . r e g i s t e r e d _ b y _ u s e r _ i d   = =   m o d e l s . U s e r . i d  
                 ) . f i l t e r (  
                         m o d e l s . A s s e t L o g . e x p e c t e d _ r e t u r n _ d a t e   <   t o d a y ,  
                         m o d e l s . A s s e t L o g . s t a t u s   ! =   ' r e t u r n e d '  
                 ) . o r d e r _ b y (  
                         m o d e l s . A s s e t L o g . e x p e c t e d _ r e t u r n _ d a t e . a s c ( )     #   Q u √ °   h · ∫ ° n   l √ ¢ u   n h · ∫ • t   l √ ™ n   ƒ  · ∫ ß u  
                 )  
                  
                 o v e r d u e _ r e s u l t s   =   o v e r d u e _ q u e r y . a l l ( )  
                  
                 o v e r d u e _ a s s e t s   =   [ ]  
                 h i g h _ r i s k _ c o u n t   =   0  
                  
                 f o r   a s s e t ,   u s e r _ n a m e   i n   o v e r d u e _ r e s u l t s :  
                         #   T √ ≠ n h   s · ª    n g √ † y   q u √ °   h · ∫ ° n  
                         d a y s _ o v e r d u e   =   ( t o d a y   -   a s s e t . e x p e c t e d _ r e t u r n _ d a t e ) . d a y s  
                          
                         #   X √ ° c   ƒ  · ª 9 n h   m · ª © c   ƒ  · ª "!  r · ª ß i   r o  
                         i f   d a y s _ o v e r d u e   >   7 :  
                                 r i s k _ l e v e l   =   " h i g h "  
                                 h i g h _ r i s k _ c o u n t   + =   1  
                         e l i f   d a y s _ o v e r d u e   >   3 :  
                                 r i s k _ l e v e l   =   " m e d i u m "  
                         e l s e :  
                                 r i s k _ l e v e l   =   " l o w "  
                          
                         o v e r d u e _ a s s e t s . a p p e n d ( s c h e m a s . O v e r d u e A s s e t D e t a i l (  
                                 i d = a s s e t . i d ,  
                                 a s s e t _ d e s c r i p t i o n = a s s e t . a s s e t _ d e s c r i p t i o n ,  
                                 f u l l _ n a m e = u s e r _ n a m e ,  
                                 e m p l o y e e _ c o d e = a s s e t . e m p l o y e e _ c o d e ,  
                                 d e p a r t m e n t = a s s e t . d e p a r t m e n t ,  
                                 e x p e c t e d _ r e t u r n _ d a t e = a s s e t . e x p e c t e d _ r e t u r n _ d a t e ,  
                                 d a y s _ o v e r d u e = d a y s _ o v e r d u e ,  
                                 r i s k _ l e v e l = r i s k _ l e v e l ,  
                                 d e s t i n a t i o n = a s s e t . d e s t i n a t i o n ,  
                                 c r e a t e d _ a t = a s s e t . c r e a t e d _ a t  
                         ) )  
                  
                 r e t u r n   s c h e m a s . A s s e t C o n t r o l R e s p o n s e (  
                         t o t a l _ a s s e t s _ o u t = t o t a l _ a s s e t s _ o u t ,  
                         t o t a l _ a s s e t s _ r e t u r n e d = t o t a l _ a s s e t s _ r e t u r n e d ,  
                         r e t u r n _ r a t e _ p e r c e n t a g e = r o u n d ( r e t u r n _ r a t e _ p e r c e n t a g e ,   2 ) ,  
                         o v e r d u e _ a s s e t s = o v e r d u e _ a s s e t s ,  
                         o v e r d u e _ c o u n t = l e n ( o v e r d u e _ a s s e t s ) ,  
                         h i g h _ r i s k _ c o u n t = h i g h _ r i s k _ c o u n t  
                 )  
                  
         e x c e p t   E x c e p t i o n   a s   e :  
                 l o g g e r . e r r o r ( f " E r r o r   i n   a s s e t _ c o n t r o l :   { e } " ,   e x c _ i n f o = T r u e )  
                 r a i s e   H T T P E x c e p t i o n ( s t a t u s _ c o d e = 5 0 0 ,   d e t a i l = s t r ( e ) )  
  
  
 @ r o u t e r . g e t ( " / s y s t e m - o v e r v i e w " )  
 d e f   s y s t e m _ o v e r v i e w ( d b :   S e s s i o n   =   D e p e n d s ( g e t _ d b ) ) :  
         " " "  
         T · ª " n g   q u a n   H · ª !   t h · ª  n g   -   S y s t e m   O v e r v i e w  
          
         R e t u r n s :  
                 S y s t e m O v e r v i e w R e s p o n s e   v · ª : i   c √ ° c   K P I s   t · ª " n g   h · ª £ p  
         " " "  
         t r y :  
                 i m p o r t   p y t z  
                 f r o m   . . c o n f i g   i m p o r t   s e t t i n g s  
                 f r o m   . .   i m p o r t   s c h e m a s  
                  
                 t z   =   p y t z . t i m e z o n e ( s e t t i n g s . T Z )  
                 t o d a y _ s t a r t   =   d a t e t i m e . c o m b i n e ( d a t e t i m e . n o w ( t z ) . d a t e ( ) ,   d a t e t i m e . m i n . t i m e ( ) ,   t z i n f o = t z )  
                  
                 #   1 .   T · ª " n g   n g ∆ ∞ · ª ù i   d √ π n g  
                 t o t a l _ u s e r s   =   d b . q u e r y ( f u n c . c o u n t ( m o d e l s . U s e r . i d ) ) . s c a l a r ( )   o r   0  
                  
                 #   2 .   T · ª " n g   k h √ ° c h   ( a l l   t i m e )  
                 t o t a l _ g u e s t s _ a l l _ t i m e   =   d b . q u e r y ( f u n c . c o u n t ( m o d e l s . G u e s t . i d ) ) . s c a l a r ( )   o r   0  
                  
                 #   3 .   T · ª " n g   t √ † i   s · ∫ £ n   ( a l l   t i m e )  
                 t o t a l _ a s s e t s _ a l l _ t i m e   =   d b . q u e r y ( f u n c . c o u n t ( m o d e l s . A s s e t L o g . i d ) ) . s c a l a r ( )   o r   0  
                  
                 #   4 .   K h √ ° c h   h o · ∫ ° t   ƒ  · ª "!n g   h √ ¥ m   n a y  
                 a c t i v e _ g u e s t s _ t o d a y   =   d b . q u e r y ( f u n c . c o u n t ( m o d e l s . G u e s t . i d ) ) . f i l t e r (  
                         m o d e l s . G u e s t . c r e a t e d _ a t   > =   t o d a y _ s t a r t  
                 ) . s c a l a r ( )   o r   0  
                  
                 #   5 .   T √ † i   s · ∫ £ n   ƒ  a n g   r a   n g o √ † i   h √ ¥ m   n a y  
                 a c t i v e _ a s s e t s _ t o d a y   =   d b . q u e r y ( f u n c . c o u n t ( m o d e l s . A s s e t L o g . i d ) ) . f i l t e r (  
                         m o d e l s . A s s e t L o g . s t a t u s . i n _ ( [ ' p e n d i n g _ o u t ' ,   ' c h e c k e d _ o u t ' ] )  
                 ) . s c a l a r ( )   o r   0  
                  
                 #   6 .   T h · ª ù i   g i a n   x · ª ≠   l √ Ω   t r u n g   b √ ¨ n h   ( p h √ ∫ t )   -   t · ª ´   c r e a t e d _ a t   ƒ  · ∫ ø n   c h e c k _ i n _ t i m e  
                 a v g _ q u e r y   =   d b . q u e r y (  
                         f u n c . a v g (  
                                 ( f u n c . j u l i a n d a y ( m o d e l s . G u e s t . c h e c k _ i n _ t i m e )   -   f u n c . j u l i a n d a y ( m o d e l s . G u e s t . c r e a t e d _ a t ) )   *   2 4   *   6 0  
                         )  
                 ) . f i l t e r (  
                         m o d e l s . G u e s t . c h e c k _ i n _ t i m e   ! =   N o n e  
                 ) . s c a l a r ( )  
                  
                 a v g _ p r o c e s s i n g _ t i m e   =   r o u n d ( a v g _ q u e r y ,   2 )   i f   a v g _ q u e r y   e l s e   N o n e  
                  
                 r e t u r n   s c h e m a s . S y s t e m O v e r v i e w R e s p o n s e (  
                         t o t a l _ u s e r s = t o t a l _ u s e r s ,  
                         t o t a l _ g u e s t s _ a l l _ t i m e = t o t a l _ g u e s t s _ a l l _ t i m e ,  
                         t o t a l _ a s s e t s _ a l l _ t i m e = t o t a l _ a s s e t s _ a l l _ t i m e ,  
                         a c t i v e _ g u e s t s _ t o d a y = a c t i v e _ g u e s t s _ t o d a y ,  
                         a c t i v e _ a s s e t s _ t o d a y = a c t i v e _ a s s e t s _ t o d a y ,  
                         a v g _ p r o c e s s i n g _ t i m e _ m i n u t e s = a v g _ p r o c e s s i n g _ t i m e  
                 )  
                  
         e x c e p t   E x c e p t i o n   a s   e :  
                 l o g g e r . e r r o r ( f " E r r o r   i n   s y s t e m _ o v e r v i e w :   { e } " ,   e x c _ i n f o = T r u e )  
                 r a i s e   H T T P E x c e p t i o n ( s t a t u s _ c o d e = 5 0 0 ,   d e t a i l = s t r ( e ) )  
  
  
 @ r o u t e r . g e t ( " / u s e r - a c t i v i t y " )  
 d e f   u s e r _ a c t i v i t y (  
         d b :   S e s s i o n   =   D e p e n d s ( g e t _ d b ) ,  
         s t a r t _ d a t e :   d a t e t i m e   |   N o n e   =   N o n e ,  
         e n d _ d a t e :   d a t e t i m e   |   N o n e   =   N o n e  
 ) :  
         " " "  
         H o · ∫ ° t   ƒ  · ª "!n g   N g ∆ ∞ · ª ù i   d √ π n g   -   U s e r   A c t i v i t y  
          
         R e t u r n s :  
                 U s e r A c t i v i t y R e s p o n s e   v · ª : i   t h · ª  n g   k √ ™   h o · ∫ ° t   ƒ  · ª "!n g   t · ª ´ n g   u s e r  
         " " "  
         t r y :  
                 i m p o r t   p y t z  
                 f r o m   . . c o n f i g   i m p o r t   s e t t i n g s  
                 f r o m   . .   i m p o r t   s c h e m a s  
                  
                 #   Q u e r y   t · ∫ • t   c · ∫ £   u s e r s  
                 u s e r s   =   d b . q u e r y ( m o d e l s . U s e r ) . a l l ( )  
                  
                 u s e r _ s t a t s   =   [ ]  
                  
                 f o r   u s e r   i n   u s e r s :  
                         #   ƒ ê · ∫ ø m   k h √ ° c h   ƒ  √ £   ƒ  ƒ ín g   k √ Ω  
                         g u e s t s _ q u e r y   =   d b . q u e r y ( f u n c . c o u n t ( m o d e l s . G u e s t . i d ) ) . f i l t e r (  
                                 m o d e l s . G u e s t . r e g i s t e r e d _ b y _ u s e r _ i d   = =   u s e r . i d  
                         )  
                         i f   s t a r t _ d a t e :  
                                 g u e s t s _ q u e r y   =   g u e s t s _ q u e r y . f i l t e r ( m o d e l s . G u e s t . c r e a t e d _ a t   > =   s t a r t _ d a t e )  
                         i f   e n d _ d a t e :  
                                 g u e s t s _ q u e r y   =   g u e s t s _ q u e r y . f i l t e r ( m o d e l s . G u e s t . c r e a t e d _ a t   < =   e n d _ d a t e )  
                          
                         g u e s t s _ c o u n t   =   g u e s t s _ q u e r y . s c a l a r ( )   o r   0  
                          
                         #   ƒ ê · ∫ ø m   t √ † i   s · ∫ £ n   ƒ  √ £   ƒ  ƒ ín g   k √ Ω  
                         a s s e t s _ q u e r y   =   d b . q u e r y ( f u n c . c o u n t ( m o d e l s . A s s e t L o g . i d ) ) . f i l t e r (  
                                 m o d e l s . A s s e t L o g . r e g i s t e r e d _ b y _ u s e r _ i d   = =   u s e r . i d  
                         )  
                         i f   s t a r t _ d a t e :  
                                 a s s e t s _ q u e r y   =   a s s e t s _ q u e r y . f i l t e r ( m o d e l s . A s s e t L o g . c r e a t e d _ a t   > =   s t a r t _ d a t e )  
                         i f   e n d _ d a t e :  
                                 a s s e t s _ q u e r y   =   a s s e t s _ q u e r y . f i l t e r ( m o d e l s . A s s e t L o g . c r e a t e d _ a t   < =   e n d _ d a t e )  
                          
                         a s s e t s _ c o u n t   =   a s s e t s _ q u e r y . s c a l a r ( )   o r   0  
                          
                         #   T √ ≠ n h   ƒ  i · ª ím   h i · ª ! u   s u · ∫ • t   ( s i m p l e :   t · ª " n g   s · ª    ƒ  ƒ ín g   k √ Ω )  
                         p e r f o r m a n c e _ s c o r e   =   g u e s t s _ c o u n t   +   a s s e t s _ c o u n t  
                          
                         u s e r _ s t a t s . a p p e n d ( s c h e m a s . U s e r A c t i v i t y S t a t s (  
                                 u s e r _ i d = u s e r . i d ,  
                                 f u l l _ n a m e = u s e r . f u l l _ n a m e ,  
                                 d e p a r t m e n t = u s e r . d e p a r t m e n t   o r   " " ,  
                                 g u e s t s _ r e g i s t e r e d = g u e s t s _ c o u n t ,  
                                 a s s e t s _ r e g i s t e r e d = a s s e t s _ c o u n t ,  
                                 p e r f o r m a n c e _ s c o r e = f l o a t ( p e r f o r m a n c e _ s c o r e )  
                         ) )  
                  
                 #   S · ∫ Ø p   x · ∫ ø p   t h e o   p e r f o r m a n c e   s c o r e   g i · ∫ £ m   d · ∫ ß n  
                 u s e r _ s t a t s . s o r t ( k e y = l a m b d a   x :   x . p e r f o r m a n c e _ s c o r e ,   r e v e r s e = T r u e )  
                  
                 #   F o r m a t   d a t e   r a n g e  
                 i f   s t a r t _ d a t e   a n d   e n d _ d a t e :  
                         d a t e _ r a n g e   =   f " { s t a r t _ d a t e . s t r f t i m e ( ' % Y - % m - % d ' ) }   t o   { e n d _ d a t e . s t r f t i m e ( ' % Y - % m - % d ' ) } "  
                 e l i f   s t a r t _ d a t e :  
                         d a t e _ r a n g e   =   f " F r o m   { s t a r t _ d a t e . s t r f t i m e ( ' % Y - % m - % d ' ) } "  
                 e l i f   e n d _ d a t e :  
                         d a t e _ r a n g e   =   f " U n t i l   { e n d _ d a t e . s t r f t i m e ( ' % Y - % m - % d ' ) } "  
                 e l s e :  
                         d a t e _ r a n g e   =   " A l l   t i m e "  
                  
                 r e t u r n   s c h e m a s . U s e r A c t i v i t y R e s p o n s e (  
                         u s e r s = u s e r _ s t a t s ,  
                         d a t e _ r a n g e = d a t e _ r a n g e  
                 )  
                  
         e x c e p t   E x c e p t i o n   a s   e :  
                 l o g g e r . e r r o r ( f " E r r o r   i n   u s e r _ a c t i v i t y :   { e } " ,   e x c _ i n f o = T r u e )  
                 r a i s e   H T T P E x c e p t i o n ( s t a t u s _ c o d e = 5 0 0 ,   d e t a i l = s t r ( e ) )  
 