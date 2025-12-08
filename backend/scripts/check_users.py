
import sqlite3
import os

# Connect to DB
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_FILE = os.path.join(BASE_DIR, 'backend', 'app', 'security_v2_3.db')
# Try alternative path if first fails
if not os.path.exists(DB_FILE):
    DB_FILE = os.path.join(BASE_DIR, 'backend', 'security_v2_3.db')

if not os.path.exists(DB_FILE):
    print(f"Error: DB file not found at {DB_FILE}")
    exit(1)

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

try:
    cursor.execute("SELECT username, role, full_name FROM users")
    rows = cursor.fetchall()
    print(f"{'Username':<20} | {'Role':<15} | {'Full Name'}")
    print("-" * 50)
    for row in rows:
        print(f"{row[0]:<20} | {row[1]:<15} | {row[2]}")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
