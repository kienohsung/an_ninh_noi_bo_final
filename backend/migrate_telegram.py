import sqlite3
import os

# Đường dẫn đến file CSDL
DB_FILE = os.path.join(os.path.dirname(__file__), 'security_v2_3.db')

if not os.path.exists(DB_FILE):
    print(f"LỖI: Không tìm thấy file CSDL tại '{DB_FILE}'.")
    exit(1)

def migrate_telegram_id():
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print(f"Đã kết nối thành công đến {DB_FILE}")

        print("\n=== BẢNG: users ===")
        try:
            print("Đang thêm cột 'telegram_id' (VARCHAR(32)) vào bảng 'users'...")
            cursor.execute("ALTER TABLE users ADD COLUMN telegram_id VARCHAR(32)")
            print("✓ Thành công!")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ Cột 'telegram_id' đã tồn tại. Bỏ qua.")
            else:
                raise e
        
        # Tạo index cho telegram_id
        try:
            print("Đang tạo index 'idx_users_telegram_id'...")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)")
            print("✓ Index 'idx_users_telegram_id' đã được tạo!")
        except Exception as e:
            print(f"⚠ Lỗi khi tạo index 'idx_users_telegram_id': {e}")

        conn.commit()
        print("\n" + "="*50)
        print("✓ DI TRÚ TELEGRAM ID ĐÃ HOÀN TẤT!")
        print("="*50)

    except Exception as e:
        print(f"\n❌ ĐÃ XẢY RA LỖI: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_telegram_id()
