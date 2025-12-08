
import sqlite3
import os
from passlib.context import CryptContext

# Setup password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

# Connect to DB
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_FILE = os.path.join(BASE_DIR, 'backend', 'app', 'security_v2_3.db')
if not os.path.exists(DB_FILE):
    DB_FILE = os.path.join(BASE_DIR, 'backend', 'security_v2_3.db')

print(f"Connecting to DB: {DB_FILE}")

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

try:
    new_password = "123456"
    hashed_pw = get_password_hash(new_password)
    
    cursor.execute("UPDATE users SET password_hash = ? WHERE username = 'baove'", (hashed_pw,))
    conn.commit()
    
    if cursor.rowcount > 0:
        print(f"SUCCESS: Password for 'baove' has been reset to '{new_password}'.")
    else:
        print("ERROR: User 'baove' not found.")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
