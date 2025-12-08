import sqlite3
import os

# Đường dẫn đến file CSDL
DB_FILE = os.path.join(os.path.dirname(__file__), 'security_v2_3.db')

if not os.path.exists(DB_FILE):
    print(f"LỖI: Không tìm thấy file CSDL tại '{DB_FILE}'.")
    print("Vui lòng kiểm tra lại tên file CSDL trong script.")
    exit(1)

def migrate_purchasing():
    conn = None
    try:
        # 1. Kết nối đến CSDL
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print(f"Đã kết nối thành công đến {DB_FILE}")

        # === TẠO BẢNG 'purchasing_logs' ===
        print("\n=== BẢNG: purchasing_logs ===")
        
        try:
            print("Đang tạo bảng 'purchasing_logs' (nếu chưa tồn tại)...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS purchasing_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_name VARCHAR(128) NOT NULL,
                    department VARCHAR(128) DEFAULT '',
                    category VARCHAR(64) NOT NULL,
                    item_name VARCHAR(255) NOT NULL,
                    supplier_name VARCHAR(128) DEFAULT '',
                    approved_price INTEGER DEFAULT 0,
                    status VARCHAR(16) DEFAULT 'new',
                    created_at DATETIME
                )
            """)
            print("✓ Bảng 'purchasing_logs' đã được tạo!")
        except Exception as e:
            print(f"⚠ Lỗi khi tạo bảng 'purchasing_logs': {e}")
            raise e

        # === TẠO BẢNG 'purchasing_images' ===
        print("\n=== BẢNG: purchasing_images ===")
        
        try:
            print("Đang tạo bảng 'purchasing_images' (nếu chưa tồn tại)...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS purchasing_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    purchasing_id INTEGER NOT NULL,
                    image_path VARCHAR(255) NOT NULL,
                    FOREIGN KEY (purchasing_id) REFERENCES purchasing_logs(id) ON DELETE CASCADE
                )
            """)
            print("✓ Bảng 'purchasing_images' đã được tạo!")
        except Exception as e:
            print(f"⚠ Lỗi khi tạo bảng 'purchasing_images': {e}")
            raise e

        # === TẠO INDEX CHO HIỆU SUẤT ===
        print("\n=== TẠO INDEX ===")
        
        # Index cho created_at (phục vụ lọc theo thời gian)
        try:
            print("Đang tạo index 'idx_purchasing_logs_created_at'...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchasing_logs_created_at ON purchasing_logs(created_at)")
            print("✓ Index 'idx_purchasing_logs_created_at' đã được tạo!")
        except Exception as e:
            print(f"⚠ Lỗi khi tạo index created_at: {e}")

        # Index cho category (phục vụ lọc theo loại hàng)
        try:
            print("Đang tạo index 'idx_purchasing_logs_category'...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchasing_logs_category ON purchasing_logs(category)")
            print("✓ Index 'idx_purchasing_logs_category' đã được tạo!")
        except Exception as e:
            print(f"⚠ Lỗi khi tạo index category: {e}")

        # Index cho status
        try:
            print("Đang tạo index 'idx_purchasing_logs_status'...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchasing_logs_status ON purchasing_logs(status)")
            print("✓ Index 'idx_purchasing_logs_status' đã được tạo!")
        except Exception as e:
            print(f"⚠ Lỗi khi tạo index status: {e}")

        # Index cho purchasing_id trong bảng images
        try:
            print("Đang tạo index 'idx_purchasing_images_purchasing_id'...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchasing_images_purchasing_id ON purchasing_images(purchasing_id)")
            print("✓ Index 'idx_purchasing_images_purchasing_id' đã được tạo!")
        except Exception as e:
            print(f"⚠ Lỗi khi tạo index purchasing_id: {e}")

        # === LƯU THAY ĐỔI ===
        conn.commit()
        print("\n" + "="*50)
        print("✓ DI TRÚ (Purchasing Module) ĐÃ HOÀN TẤT!")
        print("="*50)

    except Exception as e:
        print(f"\n❌ ĐÃ XẢY RA LỖI NGHIÊM TRỌNG: {e}")
        if conn:
            conn.rollback()
            print("↩ Đã hoàn tác (rollback) thay đổi.")
    finally:
        if conn:
            conn.close()
            print("\n🔒 Đã đóng kết nối CSDL.")

if __name__ == "__main__":
    print("="*50)
    print("BẮT ĐẦU DI TRÚ CSDL (Purchasing Module)")
    print("="*50)
    migrate_purchasing()
