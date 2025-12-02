import sqlite3
import os

# Đường dẫn đến file database
DB_PATH = "backend/security_v2_3.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Thêm cột vietnamese_manager_name
        try:
            cursor.execute("ALTER TABLE asset_log ADD COLUMN vietnamese_manager_name TEXT")
            print("Added column 'vietnamese_manager_name'")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("Column 'vietnamese_manager_name' already exists")
            else:
                raise e

        # Thêm cột korean_manager_name
        try:
            cursor.execute("ALTER TABLE asset_log ADD COLUMN korean_manager_name TEXT")
            print("Added column 'korean_manager_name'")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("Column 'korean_manager_name' already exists")
            else:
                raise e

        conn.commit()
        print("Migration completed successfully.")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
