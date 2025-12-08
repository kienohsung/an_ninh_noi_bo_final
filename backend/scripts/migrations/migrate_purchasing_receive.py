import sqlite3
import os

# Đường dẫn đến file CSDL
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_FILE = os.path.join(BASE_DIR, 'security_v2_3.db')

if not os.path.exists(DB_FILE):
    print(f"LỖI: Không tìm thấy file CSDL tại '{DB_FILE}'.")
    exit(1)

def migrate_receive_goods():
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print(f"Đã kết nối thành công đến {DB_FILE}")

        # 1. Update table purchasing_logs
        print("\n=== KIỂM TRA BẢNG purchasing_logs ===")
        cursor.execute("PRAGMA table_info(purchasing_logs)")
        columns_logs = [info[1] for info in cursor.fetchall()]
        
        if 'received_at' not in columns_logs:
            print("Đang thêm cột 'received_at'...")
            cursor.execute("ALTER TABLE purchasing_logs ADD COLUMN received_at DATETIME")
            print("✓ Đã thêm cột 'received_at'.")
        
        if 'received_note' not in columns_logs:
            print("Đang thêm cột 'received_note'...")
            cursor.execute("ALTER TABLE purchasing_logs ADD COLUMN received_note TEXT DEFAULT ''")
            print("✓ Đã thêm cột 'received_note'.")

        # 2. Update table purchasing_images
        print("\n=== KIỂM TRA BẢNG purchasing_images ===")
        cursor.execute("PRAGMA table_info(purchasing_images)")
        columns_imgs = [info[1] for info in cursor.fetchall()]

        if 'image_type' not in columns_imgs:
            print("Đang thêm cột 'image_type'...")
            cursor.execute("ALTER TABLE purchasing_images ADD COLUMN image_type VARCHAR(32) DEFAULT 'request'")
            print("✓ Đã thêm cột 'image_type'.")

        conn.commit()
        print("\n" + "="*50)
        print("✓ MIGRATION (Receive Goods) ĐÃ HOÀN TẤT!")
        print("="*50)

    except Exception as e:
        print(f"\n❌ ĐÃ XẢY RA LỖI: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_receive_goods()
