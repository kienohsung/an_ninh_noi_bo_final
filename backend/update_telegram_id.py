from app.database import SessionLocal
from app.models import User

def update_admin_telegram():
    db = SessionLocal()
    try:
        # Tìm user admin
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("Không tìm thấy user 'admin'")
            return

        # Cập nhật Telegram ID
        admin.telegram_id = "7930851420"
        db.commit()
        print(f"Đã cập nhật Telegram ID {admin.telegram_id} cho user {admin.username}")
    except Exception as e:
        print(f"Lỗi: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_admin_telegram()
