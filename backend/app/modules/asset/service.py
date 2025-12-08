from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, or_
from datetime import datetime
import os
import uuid
import logging
from typing import List, Optional
import io
import pandas as pd

from app import models
from app.modules.asset import schema as schemas
from app.core import config
from app.utils.notifications import send_telegram_message, send_asset_event_to_archive_background

logger = logging.getLogger(__name__)

SECURITY_EVENT_STATUS = "security_event"

class AssetService:
    @staticmethod
    def create_asset(
        db: Session,
        asset_in: schemas.AssetLogCreate,
        current_user: models.User,
        bg_tasks
    ) -> models.AssetLog:
        """
        Create a new asset log.
        """
        if current_user.role not in ["admin", "manager", "staff"]:
            raise PermissionError("Access denied")
        
        db_asset = models.AssetLog(
            registered_by_user_id=current_user.id,
            full_name=current_user.full_name,
            employee_code=current_user.username,
            department=asset_in.department,
            destination=asset_in.destination,
            description_reason=asset_in.description_reason,
            asset_description=asset_in.asset_description,
            quantity=asset_in.quantity,
            expected_return_date=asset_in.expected_return_date,
            estimated_datetime=asset_in.estimated_datetime,
            vietnamese_manager_name=asset_in.vietnamese_manager_name,
            korean_manager_name=asset_in.korean_manager_name,
            status=models.ASSET_STATUS_PENDING_OUT,
            created_at=models.get_local_time()
        )
        
        if asset_in.estimated_datetime and not asset_in.expected_return_date:
            db_asset.expected_return_date = asset_in.estimated_datetime.date()
            
        db.add(db_asset)
        db.commit()
        db.refresh(db_asset)

        # Basic Telegram notification
        try:
            msg = f"""
[ASSET PENDING] - CÓ HÀNG CHỜ RA
- Người ĐK: {current_user.full_name}
- Bộ phận: {db_asset.department}
- Nơi đến: {db_asset.destination}
- Số lượng: {db_asset.quantity}
- Mô tả: {db_asset.description_reason}
- Dự kiến về: {db_asset.expected_return_date.strftime('%d/%m/%Y') if db_asset.expected_return_date else 'Không về'}
            """
            bg_tasks.add_task(send_telegram_message, msg, "GUARD")
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")

        bg_tasks.add_task(
            send_asset_event_to_archive_background,
            db_asset.id,
            "Đăng ký tài sản mới",
            current_user.id
        )

        db.refresh(db_asset, attribute_names=['registered_by'])
        return db_asset

    @staticmethod
    def upload_asset_image(
        db: Session,
        asset_id: int,
        file_filename: str,
        file_content: bytes,
        current_user: models.User
    ) -> models.AssetImage:
        """
        Upload asset image logic.
        """
        if current_user.role not in ["admin", "manager", "staff"]:
            raise PermissionError("Access denied")
            
        db_asset = db.get(models.AssetLog, asset_id)
        if not db_asset:
            return None # Not found
            
        if current_user.role == "staff" and db_asset.registered_by_user_id != current_user.id:
            raise PermissionError("Not owner")
            
        ext = os.path.splitext(file_filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        
        save_path = os.path.join(config.settings.UPLOAD_DIR, "assets", unique_filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, "wb") as buffer:
            buffer.write(file_content)
            
        db_image = models.AssetImage(
            asset_id=asset_id,
            image_path=f"assets/{unique_filename}"
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        return db_image

    @staticmethod
    def _archive_asset_image(image_path: str):
        try:
            archive_dir = os.path.join(config.settings.UPLOAD_DIR, "archived_assets")
            os.makedirs(archive_dir, exist_ok=True)
            
            source_path = os.path.join(config.settings.UPLOAD_DIR, image_path)
            if os.path.exists(source_path):
                file_name = os.path.basename(image_path)
                dest_path = os.path.join(archive_dir, file_name)
                if os.path.exists(dest_path):
                    dest_path = os.path.join(archive_dir, f"{uuid.uuid4()}_{file_name}")
                os.rename(source_path, dest_path)
                logger.info(f"Archived asset image from {source_path} to {dest_path}")
        except Exception as e:
            logger.error(f"Could not archive asset image file {image_path}: {e}")

    @staticmethod
    def delete_asset_image(
        db: Session,
        image_id: int,
        current_user: models.User
    ) -> bool:
        if current_user.role not in ["admin", "manager", "staff"]:
            raise PermissionError("Access denied")
            
        db_image = db.query(models.AssetImage).options(joinedload(models.AssetImage.asset)).get(image_id)
        if not db_image:
            return False # Not found
            
        asset = db_image.asset
        if not asset:
            raise ValueError("Orphaned image")
            
        is_admin_or_manager = current_user.role in ("admin", "manager")
        is_owner = asset.registered_by_user_id == current_user.id
        
        if not (is_admin_or_manager or is_owner):
            raise PermissionError("Access denied")
            
        AssetService._archive_asset_image(db_image.image_path)
        db.delete(db_image)
        db.commit()
        return True

    @staticmethod
    def get_assets(
        db: Session,
        current_user: models.User,
        start_date=None,
        end_date=None,
        status=None,
        department=None
    ) -> List[models.AssetLog]:
        if current_user.role not in ["admin", "manager", "staff"]:
            raise PermissionError("Access denied")

        query = (
            select(models.AssetLog)
            .options(joinedload(models.AssetLog.registered_by))
            .options(joinedload(models.AssetLog.check_out_by))
            .options(joinedload(models.AssetLog.check_in_back_by))
            .options(joinedload(models.AssetLog.images))
            .filter(models.AssetLog.status != SECURITY_EVENT_STATUS)
            .order_by(models.AssetLog.created_at.desc())
        )

        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.filter(models.AssetLog.created_at >= start_dt)
        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time())
            query = query.filter(models.AssetLog.created_at <= end_dt)
        
        if status:
            query = query.filter(models.AssetLog.status == status)
        
        if department:
            query = query.filter(models.AssetLog.department.ilike(f"%{department}%"))

        if current_user.role == 'staff':
            query = query.filter(models.AssetLog.registered_by_user_id == current_user.id)

        results = db.scalars(query).unique().all()
        return results

    @staticmethod
    def get_assets_for_guard_gate(
        db: Session,
        current_user: models.User,
        q: str | None = None
    ) -> List[models.AssetLog]:
        if current_user.role not in ["admin", "guard"]:
            raise PermissionError("Access denied")
        
        query = (
            select(models.AssetLog)
            .options(joinedload(models.AssetLog.registered_by))
            .options(joinedload(models.AssetLog.images))
            .filter(
                models.AssetLog.status != SECURITY_EVENT_STATUS,
                or_(
                    models.AssetLog.status == models.ASSET_STATUS_PENDING_OUT,
                    models.AssetLog.status == models.ASSET_STATUS_CHECKED_OUT
                )
            )
            .order_by(models.AssetLog.created_at.asc())
        )
        
        if q:
            search_term = f"%{q}%"
            query = query.filter(
                or_(
                    models.AssetLog.destination.ilike(search_term),
                    models.AssetLog.description_reason.ilike(search_term),
                    models.AssetLog.registered_by.has(models.User.full_name.ilike(search_term))
                )
            )

        results = db.scalars(query).unique().all()
        return results

    @staticmethod
    def confirm_asset_checkout(
        db: Session,
        asset_id: int,
        current_user: models.User,
        bg_tasks
    ) -> models.AssetLog:
        if current_user.role not in ["admin", "guard"]:
            raise PermissionError("Access denied")
            
        db_asset = db.get(models.AssetLog, asset_id, options=[joinedload(models.AssetLog.registered_by)])
        
        if not db_asset:
            return None
        
        if db_asset.status == SECURITY_EVENT_STATUS:
             raise ValueError("Security event cannot be checked out")
        
        if db_asset.status != models.ASSET_STATUS_PENDING_OUT:
            raise ValueError(f"Asset status is '{db_asset.status}', cannot checkout")

        is_returnable = (db_asset.estimated_datetime is not None) or (db_asset.expected_return_date is not None)
        
        status_msg = ""
        if is_returnable:
            db_asset.status = models.ASSET_STATUS_CHECKED_OUT
            db_asset.check_out_time = models.get_local_time()
            db_asset.check_out_by_user_id = current_user.id
            status_msg = "HÀNG ĐÃ RA"
        else:
            db_asset.status = models.ASSET_STATUS_RETURNED
            db_asset.check_out_time = models.get_local_time()
            db_asset.check_out_by_user_id = current_user.id
            db_asset.check_in_back_time = models.get_local_time()
            db_asset.check_in_back_by_user_id = current_user.id
            status_msg = "HÀNG ĐÃ RA (KHÔNG VỀ)"
        
        db.commit()

        try:
            msg = f"""
[ASSET CHECK-OUT] - {status_msg}
- Bảo vệ: {current_user.full_name}
- Người ĐK: {db_asset.registered_by.full_name}
- Bộ phận: {db_asset.department}
- Nơi đến: {db_asset.destination}
- Mô tả: {db_asset.description_reason}
            """
            bg_tasks.add_task(send_telegram_message, msg, "MANAGER")
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
        
        bg_tasks.add_task(
            send_asset_event_to_archive_background,
            db_asset.id,
            "Xác nhận ra cổng" if is_returnable else "Xác nhận ra cổng (không về)",
            current_user.id
        )
        
        db.refresh(db_asset, attribute_names=['registered_by', 'check_out_by'])
        return db_asset

    @staticmethod
    def confirm_asset_return(
        db: Session,
        asset_id: int,
        current_user: models.User,
        bg_tasks
    ) -> models.AssetLog:
        if current_user.role not in ["admin", "guard"]:
            raise PermissionError("Access denied")
            
        db_asset = db.get(models.AssetLog, asset_id, options=[joinedload(models.AssetLog.registered_by)])
        if not db_asset:
            return None
            
        if db_asset.status == SECURITY_EVENT_STATUS:
            raise ValueError("Security event")
            
        if db_asset.status != models.ASSET_STATUS_CHECKED_OUT:
            raise ValueError(f"Status is '{db_asset.status}', cannot confirm return")

        db_asset.status = models.ASSET_STATUS_RETURNED
        db_asset.check_in_back_time = models.get_local_time()
        db_asset.check_in_back_by_user_id = current_user.id
        db.commit()

        try:
            msg = f"""
[ASSET RETURNED] - HÀNG ĐÃ VỀ
- Bảo vệ: {current_user.full_name}
- Người ĐK: {db_asset.registered_by.full_name}
- Bộ phận: {db_asset.department}
- Nơi đến: {db_asset.destination}
- Mô tả: {db_asset.description_reason}
            """
            bg_tasks.add_task(send_telegram_message, msg, "MANAGER")
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
        
        bg_tasks.add_task(
            send_asset_event_to_archive_background,
            db_asset.id,
            "Xác nhận vào cổng",
            current_user.id
        )
        
        db.refresh(db_asset, attribute_names=['registered_by', 'check_in_back_by'])
        return db_asset

    @staticmethod
    def get_my_assets(
        db: Session,
        current_user: models.User
    ) -> List[models.AssetLog]:
        query = (
            select(models.AssetLog)
            .options(joinedload(models.AssetLog.registered_by))
            .options(joinedload(models.AssetLog.check_out_by))
            .options(joinedload(models.AssetLog.check_in_back_by))
            .options(joinedload(models.AssetLog.images))
            .filter(
                models.AssetLog.registered_by_user_id == current_user.id,
                models.AssetLog.status != SECURITY_EVENT_STATUS
            )
            .order_by(models.AssetLog.created_at.desc())
        )
        results = db.scalars(query).unique().all()
        return results

    @staticmethod
    def update_asset(
        db: Session,
        asset_id: int,
        asset_update: schemas.AssetLogUpdate,
        current_user: models.User
    ) -> models.AssetLog:
        db_asset = db.get(models.AssetLog, asset_id)
        if not db_asset:
             return None
        
        if current_user.role not in ['admin', 'manager']:
            if db_asset.registered_by_user_id != current_user.id:
                 raise PermissionError("Access denied")
        
        if current_user.role != 'admin' and db_asset.status != models.ASSET_STATUS_PENDING_OUT:
            raise ValueError("Only pending assets can be updated")
        
        update_data = asset_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(db_asset, key):
                setattr(db_asset, key, value)
        
        db.commit()
        db.refresh(db_asset)
        return db_asset

    @staticmethod
    def delete_asset(
        db: Session,
        asset_id: int,
        current_user: models.User
    ) -> bool:
        db_asset = db.get(models.AssetLog, asset_id)
        if not db_asset:
            return False
        
        if current_user.role not in ['admin', 'manager']:
            if db_asset.registered_by_user_id != current_user.id:
                 raise PermissionError("Access denied")
        
        if current_user.role != 'admin' and db_asset.status != models.ASSET_STATUS_PENDING_OUT:
             raise ValueError("Only pending assets can be deleted")
        
        for image in db_asset.images:
            AssetService._archive_asset_image(image.image_path)
            db.delete(image)
        
        db.delete(db_asset)
        db.commit()
        return True

    @staticmethod
    def increment_print_count(db: Session, asset_id: int, user: models.User) -> models.AssetLog:
        """
        Increment print count for an asset.
        """
        db_asset = db.get(models.AssetLog, asset_id)
        if not db_asset:
            return None
        
        db_asset.print_count += 1
        db.commit()
        db.refresh(db_asset)
        return db_asset

    @staticmethod
    def export_assets(
        db: Session,
        current_user: models.User,
        start_date=None,
        end_date=None,
        status=None,
        department=None
    ):
        query = (
            select(models.AssetLog)
            .options(joinedload(models.AssetLog.registered_by))
            .options(joinedload(models.AssetLog.check_out_by))
            .options(joinedload(models.AssetLog.check_in_back_by))
            .filter(models.AssetLog.status != SECURITY_EVENT_STATUS)
            .order_by(models.AssetLog.created_at.desc())
        )

        if current_user.role == 'staff':
            query = query.filter(models.AssetLog.registered_by_user_id == current_user.id)

        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.filter(models.AssetLog.created_at >= start_dt)
        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time())
            query = query.filter(models.AssetLog.created_at <= end_dt)
        
        if status:
            query = query.filter(models.AssetLog.status == status)
        
        if department:
            query = query.filter(models.AssetLog.department.ilike(f"%{department}%"))

        results = db.scalars(query).all()

        data = []
        for idx, asset in enumerate(results, start=1):
            reg = asset.registered_by
            out_by = asset.check_out_by
            in_by = asset.check_in_back_by
            
            data.append({
                "STT": idx,
                "Mã phiếu": asset.id,
                "Ngày tạo": asset.created_at.strftime("%d/%m/%Y %H:%M") if asset.created_at else "",
                "Người đăng ký": reg.full_name if reg else "N/A",
                "Mã NV": asset.employee_code,
                "Bộ phận": asset.department,
                "Nơi đến": asset.destination,
                "Lý do/Mô tả": asset.description_reason,
                "Tài sản": asset.asset_description or "",
                "Số lượng": asset.quantity,
                "Trạng thái": asset.status,
                "Giờ ra": asset.check_out_time.strftime("%d/%m/%Y %H:%M") if asset.check_out_time else "",
                "BV cho ra": out_by.full_name if out_by else "",
                "Dự kiến về": asset.expected_return_date.strftime("%d/%m/%Y") if asset.expected_return_date else "",
                "Giờ về": asset.check_in_back_time.strftime("%d/%m/%Y %H:%M") if asset.check_in_back_time else "",
                "BV nhận về": in_by.full_name if in_by else "",
                "QL Việt": asset.vietnamese_manager_name or "",
                "QL Hàn": asset.korean_manager_name or ""
            })

        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Assets')
            workbook = writer.book
            worksheet = writer.sheets['Assets']
            
            header_fmt = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D3D3D3', 'border': 1})
            date_fmt = workbook.add_format({'num_format': 'dd/mm/yyyy hh:mm', 'align': 'left', 'border': 1})
            text_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})
            
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_fmt)

            for i, col in enumerate(df.columns):
                width = 20
                if col in ["Lý do/Mô tả", "Tài sản"]:
                    width = 40
                elif col == "STT":
                    width = 5
                
                worksheet.set_column(i, i, width)

        output.seek(0)
        return output
              
asset_service = AssetService()
