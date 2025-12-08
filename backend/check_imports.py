import sys
import os

# Add backend directory to path (so 'app' module can be imported)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_imports():
    print("Checking imports...")
    try:
        print("1. Importing app.core.database...")
        from app.core.database import Base, engine
        print("   -> Success")
        
        print("2. Importing app.models (Facade)...")
        from app.models import User, Guest, AssetLog
        print("   -> Success")
        
        print("3. Importing app.schemas (Facade)...")
        from app.schemas import UserRead, GuestRead, AssetLogDisplay
        print("   -> Success")

        print("4. Importing app.main (Full Application)...")
        # This will trigger router imports
        from app.main import app
        print("   -> Success")
        
        print("\n✅ ALL IMPORTS PASSED! No circular dependencies found.")
        return True
    except ImportError as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ IMPORT ERROR: {e}")
        return False
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    if check_imports():
        sys.exit(0)
    else:
        sys.exit(1)
