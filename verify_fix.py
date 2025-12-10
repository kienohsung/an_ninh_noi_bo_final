import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app.core.config import settings

def verify_fix():
    print(f"Configured UPLOAD_DIR: {settings.UPLOAD_DIR}")
    
    if os.path.exists(settings.UPLOAD_DIR):
        print("UPLOAD_DIR exists: Yes")
        
        purchasing_dir = os.path.join(settings.UPLOAD_DIR, "purchasing")
        if os.path.exists(purchasing_dir):
            print("Purchasing uploads dir exists: Yes")
            files = os.listdir(purchasing_dir)
            print(f"Files in purchasing dir: {len(files)}")
            for f in files:
                print(f" - {f}")
        else:
             print("Purchasing uploads dir exists: No")
    else:
        print("UPLOAD_DIR exists: No")

if __name__ == "__main__":
    verify_fix()
