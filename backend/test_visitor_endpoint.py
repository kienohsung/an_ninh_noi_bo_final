"""Test visitor-security-index endpoint directly"""
import sys
import traceback
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.routers.reports import visitor_security_index

db = SessionLocal()

try:
    print("Testing visitor_security_index endpoint...")
    result = visitor_security_index(db=db)
    print("✅ SUCCESS!")
    print(f"Result type: {type(result)}")
    print(f"Result keys: {list(result.__dict__.keys()) if hasattr(result, '__dict__') else 'N/A'}")
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
finally:
    db.close()
