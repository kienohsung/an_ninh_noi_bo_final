import sqlite3
import os

# Đường dẫn đến file CSDL
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_FILE = os.path.join(BASE_DIR, 'security_v2_3.db')

if not os.path.exists(DB_FILE):
    print(f"LỖI: Không tìm thấy file CSDL tại '{DB_FILE}'.")
    exit(1)

def migrate_purchasing_v2():
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print(f"Đã kết nối thành công đến {DB_FILE}")

        # Kiểm tra cột using_department
        print("\n=== KIỂM TRA BẢNG purchasing_logs ===")
        cursor.execute("PRAGMA table_info(purchasing_logs)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'using_department' not in columns:
            print("Đang thêm cột 'using_department'...")
            cursor.execute("ALTER TABLE purchasing_logs ADD COLUMN using_department VARCHAR(128) DEFAULT ''")
            print("✓ Đã thêm cột 'using_department' thành công!")
        else:
            print("ℹ Cột 'using_department' đã tồn tại. Bỏ qua.")

        conn.commit()
        print("\n" + "="*50)
        print("✓ MIGRATION V2 (Purchasing) ĐÃ HOÀN TẤT!")
        print("="*50)

    except Exception as e:
        print(f"\n❌ ĐÃ XẢY RA LỖI: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_purchasing_v2()
