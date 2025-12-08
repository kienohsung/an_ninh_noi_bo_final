
import sqlite3
import os

# Connect to DB
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_FILE = os.path.join(BASE_DIR, 'backend', 'app', 'security_v2_3.db')
if not os.path.exists(DB_FILE):
    DB_FILE = os.path.join(BASE_DIR, 'backend', 'security_v2_3.db')

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

try:
    cursor.execute("SELECT username, role, is_active FROM users WHERE username='baove'")
    row = cursor.fetchone()
    print(f"User: {row}")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
