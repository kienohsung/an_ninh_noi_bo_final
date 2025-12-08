from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from datetime import datetime, date
from typing import List, Optional
import os
import uuid
import logging
import io
import pandas as pd

from app import models
from app.core import config
from app.modules.purchasing import schema as schemas

logger = logging.getLogger(__name__)

class PurchasingService:
    @staticmethod
    def get_purchasing_list(
        db: Session,
        start_date: date = None,
        end_date: date = None,
        category: str | None = None,
        status: str | None = None
    ) -> List[models.PurchasingLog]:
        query = (
            select(models.PurchasingLog)
            .options(joinedload(models.PurchasingLog.images))
            .order_by(models.PurchasingLog.created_at.desc())
        )
        
        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.filter(models.PurchasingLog.created_at >= start_dt)
        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time())
            query = query.filter(models.PurchasingLog.created_at <= end_dt)
        
        if category:
            query = query.filter(models.PurchasingLog.category == category)
        
        if status:
            query = query.filter(models.PurchasingLog.status == status)
        
        results = db.scalars(query).unique().all()
        return results

    @staticmethod
    def create_purchasing(db: Session, data: schemas.PurchasingLogCreate) -> models.PurchasingLog:
        db_purchasing = models.PurchasingLog(
            creator_name=data.creator_name,
            department=data.department,
            using_department=data.using_department,
            category=data.category,
            item_name=data.item_name,
            supplier_name=data.supplier_name,
            approved_price=data.approved_price,
            status=models.PURCHASING_STATUS_NEW,
            created_at=models.get_local_time()
        )
        db.add(db_purchasing)
        db.commit()
        db.refresh(db_purchasing)
        return db_purchasing

    @staticmethod
    def update_purchasing(
        db: Session,
        purchasing_id: int,
        data: schemas.PurchasingLogUpdate
    ) -> models.PurchasingLog:
        db_purchasing = db.get(models.PurchasingLog, purchasing_id)
        if not db_purchasing:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None and hasattr(db_purchasing, key):
                setattr(db_purchasing, key, value)
        
        db.commit()
        db.refresh(db_purchasing)
        return db_purchasing

    @staticmethod
    def delete_purchasing(db: Session, purchasing_id: int) -> bool:
        db_purchasing = db.get(
            models.PurchasingLog, 
            purchasing_id, 
            options=[joinedload(models.PurchasingLog.images)]
        )
        if not db_purchasing:
            return False
        
        for image in db_purchasing.images:
            try:
                file_path = os.path.join(config.settings.UPLOAD_DIR, image.image_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                logger.error(f"Could not delete file {image.image_path}: {e}")
        
        db.delete(db_purchasing)
        db.commit()
        return True

    @staticmethod
    def upload_purchasing_image(
        db: Session,
        purchasing_id: int,
        type: str,
        file_filename: str,
        file_content: bytes
    ) -> models.PurchasingImage:
        db_purchasing = db.get(models.PurchasingLog, purchasing_id)
        if not db_purchasing:
            return None
        
        ext = os.path.splitext(file_filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        
        save_dir = os.path.join(config.settings.UPLOAD_DIR, "purchasing")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, unique_filename)
        
        with open(save_path, "wb") as buffer:
            buffer.write(file_content)
        
        db_image = models.PurchasingImage(
            purchasing_id=purchasing_id,
            image_path=f"purchasing/{unique_filename}",
            image_type=type
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        return db_image

    @staticmethod
    def delete_purchasing_image(db: Session, image_id: int) -> bool:
        db_image = db.get(models.PurchasingImage, image_id)
        if not db_image:
            return False
        
        try:
            file_path = os.path.join(config.settings.UPLOAD_DIR, db_image.image_path)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Could not delete file {db_image.image_path}: {e}")
        
        db.delete(db_image)
        db.commit()
        return True

    @staticmethod
    def receive_purchasing(db: Session, purchasing_id: int, note: str) -> models.PurchasingLog:
        db_purchasing = db.get(models.PurchasingLog, purchasing_id)
        if not db_purchasing:
             return None # Not found
        
        if db_purchasing.status in ["completed", "rejected"]:
             raise ValueError("Status not valid for receiving")
        
        db_purchasing.status = "completed"
        db_purchasing.received_at = models.get_local_time()
        db_purchasing.received_note = note
        
        db.commit()
        db.refresh(db_purchasing)
        return db_purchasing

    @staticmethod
    def export_purchasing_logs(
        db: Session,
        start_date: str | None = None,
        end_date: str | None = None,
        department: str | None = None,
        status: str | None = None
    ):
        query = db.query(models.PurchasingLog)

        # --- Date range filtering ---
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(models.PurchasingLog.created_at >= start_dt)
            except ValueError:
                pass 
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                end_dt = end_dt.replace(hour=23, minute=59, second=59) # End of day
                query = query.filter(models.PurchasingLog.created_at <= end_dt)
            except ValueError:
                pass

        # --- Filtering ---
        if department:
            query = query.filter(models.PurchasingLog.department.ilike(f"%{department}%"))
        
        if status:
            query = query.filter(models.PurchasingLog.status == status)

        results = query.order_by(models.PurchasingLog.created_at.desc()).all()

        # === EXCEL FORMAT ===
        data_to_export = []
        for idx, log in enumerate(results, start=1):
            created_at_str = log.created_at.strftime("%d/%m/%Y %H:%M") if log.created_at else ""
            received_at_str = log.received_at.strftime("%d/%m/%Y %H:%M") if log.received_at else ""
            
            status_map = {
                "new": "Mới",
                "pending": "Chờ duyệt",
                "approved": "Đã duyệt",
                "rejected": "Từ chối",
                "completed": "Hoàn thành"
            }
            status_display = status_map.get(log.status, log.status)

            data_to_export.append({
                "STT": idx,
                "Ngày tạo": created_at_str,
                "Người tạo": log.creator_name,
                "Bộ phận đề xuất": log.department,
                "Bộ phận sử dụng": log.using_department,
                "Loại": "Vật tư" if log.category == "supplies" else "Thiết bị",
                "Tên hàng": log.item_name,
                "Nhà cung cấp": log.supplier_name,
                "Giá duyệt": log.approved_price,
                "Trạng thái": status_display,
                "Ngày nhận": received_at_str,
                "Ghi chú nhận": log.received_note or ""
            })

        df = pd.DataFrame(data_to_export)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Purchasing', startrow=1, header=True)
            
            workbook = writer.book
            worksheet = writer.sheets['Purchasing']
            
            # Formats
            title_format = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 14, 'bold': True, 'align': 'center', 'valign': 'vcenter'})
            header_format = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 11, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1})
            data_format = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 11, 'align': 'left', 'valign': 'vcenter', 'border': 1})
            
            # Title
            worksheet.merge_range(0, 0, 0, len(df.columns) - 1, 'BÁO CÁO MUA SẮM VẬT TƯ / THIẾT BỊ', title_format)
            
            # Header
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(1, col_num, value, header_format)
            
            # Data
            for row_num in range(len(df)):
                for col_num in range(len(df.columns)):
                    worksheet.write(row_num + 2, col_num, df.iloc[row_num, col_num], data_format)
            
            # Widths
            worksheet.set_column(0, 0, 5)   # STT
            worksheet.set_column(1, 1, 15)  # Date
            worksheet.set_column(4, 5, 20)  # Departments
            worksheet.set_column(6, 6, 30)  # Item Name

        output.seek(0)
        return output

purchasing_service = PurchasingService()
