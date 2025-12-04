"""
Quick test script to debug visitor-security-index endpoint
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app import models
from sqlalchemy import func
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz

db = SessionLocal()

try:
    # Test basic imports
    print("✓ Imports OK")
    
    # Test timezone
    from app.config import settings
    tz = pytz.timezone(settings.TZ)
    now = datetime.now(tz)
    print(f"✓ Timezone OK: {now}")
    
    # Test month calculation
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = current_month_start - relativedelta(months=1)
    print(f"✓ Month calc OK: current={current_month_start}, last={last_month_start}")
    
    # Test simple query
    count = db.query(func.count(models.Guest.id)).scalar()
    print(f"✓ Query OK: Total guests = {count}")
    
    # Test monthly query
    twelve_months_ago = current_month_start - relativedelta(months=11)
    result = db.query(
        func.strftime('%Y-%m', models.Guest.created_at).label('month'),
        func.count(models.Guest.id).label('total')
    ).filter(models.Guest.created_at >= twelve_months_ago).group_by('month').all()
    
    print(f"✓ Monthly query OK: {len(result)} months")
    
    print("\n🎉 All tests passed! Issue might be in response schema")
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
