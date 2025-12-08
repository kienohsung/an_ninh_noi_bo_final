from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from datetime import datetime
import pytz
import os
import uuid
import logging
import io
import pandas as pd
import uuid
import logging
from typing import List, Optional

from app import models
from app.core import config
from app.modules.guest import schema as schemas
from app.utils.plate_formatter import format_license_plate
from app.utils.name_formatter import format_full_name
from app.utils.notifications import send_event_to_archive_background, run_pending_list_notification
from app.services.gsheets_reader import _get_service, delete_row_by_guest_info
from app.core.database import unaccent_string

logger = logging.getLogger(__name__)

class GuestService:
    @staticmethod
    def create_guest(
        db: Session, 
        payload: schemas.GuestCreate, 
        user_id: int, 
        bg_tasks
    ) -> models.Guest:
        """
        Create a new single guest record.
        """
        # Validate estimated_datetime
        if not payload.estimated_datetime:
            raise ValueError("Ngày giờ dự kiến là bắt buộc")

        # Normalize license plate
        if payload.license_plate:
            payload.license_plate = format_license_plate(payload.license_plate)

        # Normalize name
        standardized_full_name = format_full_name(payload.full_name)

        guest = models.Guest(
            full_name=standardized_full_name,
            id_card_number=payload.id_card_number or "",
            company=payload.company or "",
            reason=payload.reason or "",
            license_plate=payload.license_plate or "",
            supplier_name=payload.supplier_name or "",
            status="pending",
            estimated_datetime=payload.estimated_datetime,
            registered_by_user_id=user_id
        )
        db.add(guest)
        db.commit()
        db.refresh(guest)

        # Background tasks
        bg_tasks.add_task(send_event_to_archive_background, guest.id, "Đăng ký mới", user_id)
        bg_tasks.add_task(run_pending_list_notification)

        return guest

    @staticmethod
    def create_guests_bulk(
        db: Session,
        payload: schemas.GuestBulkCreate,
        user_id: int,
        bg_tasks
    ) -> List[models.Guest]:
        """
        Create multiple guest records (bulk).
        """
        new_guests_db = []
        formatted_plate = format_license_plate(payload.license_plate) if payload.license_plate else ""

        for individual in payload.guests:
            if not individual.full_name:
                continue

            standardized_individual_name = format_full_name(individual.full_name)

            guest = models.Guest(
                full_name=standardized_individual_name,
                id_card_number=individual.id_card_number or "",
                company=payload.company or "",
                reason=payload.reason or "",
                license_plate=formatted_plate,
                supplier_name=payload.supplier_name or "",
                status="pending",
                estimated_datetime=payload.estimated_datetime,
                registered_by_user_id=user_id
            )
            db.add(guest)
            new_guests_db.append(guest)

        if not new_guests_db:
            raise ValueError("No valid guests to add.")

        db.commit()

        # Background tasks for each guest
        for guest in new_guests_db:
            db.refresh(guest)
            bg_tasks.add_task(send_event_to_archive_background, guest.id, "Đăng ký mới (theo đoàn)", user_id)
        
        # Single notification update
        bg_tasks.add_task(run_pending_list_notification)

        return new_guests_db

    @staticmethod
    def list_guests(
        db: Session,
        user: models.User,
        q: str | None = None,
        include_all_my_history: bool = False
    ) -> List[models.Guest]:
        """
        List guests with filtering and search.
        """
        query = db.query(
            models.Guest,
            models.User.full_name.label("registered_by_name")
        ).join(
            models.User, models.Guest.registered_by_user_id == models.User.id
        ).options(joinedload(models.Guest.images))

        if user.role == "staff":
            query = query.filter(models.Guest.registered_by_user_id == user.id)
            if not include_all_my_history:
                query = query.filter(models.Guest.status == "pending")

        if q:
            unaccented_q = unaccent_string(q)
            like = f"%{unaccented_q}%"

            query = query.filter(or_(
                func.unaccent(models.Guest.full_name).ilike(like),
                models.Guest.id_card_number.ilike(like),
                func.unaccent(models.Guest.company).ilike(like),
                func.unaccent(models.Guest.reason).ilike(like),
                models.Guest.license_plate.ilike(like),
                func.unaccent(models.Guest.supplier_name).ilike(like),
                func.unaccent(models.User.full_name).ilike(like),
                models.Guest.status.ilike(f"%{q}%")
            ))

        results = query.order_by(models.Guest.created_at.desc()).all()
        return results

    @staticmethod
    def update_guest(
        db: Session,
        guest_id: int,
        payload: schemas.GuestUpdate,
        user: models.User
    ) -> models.Guest:
        """
        Update guest details.
        """
        guest = db.query(models.Guest).get(guest_id)
        if not guest:
            return None # Or raise specific error

        if user.role == "staff" and guest.registered_by_user_id != user.id:
            raise PermissionError("Not allowed")

        update_data = payload.model_dump(exclude_unset=True)

        if 'license_plate' in update_data and update_data['license_plate']:
            update_data['license_plate'] = format_license_plate(update_data['license_plate'])

        if 'estimated_datetime' in update_data:
            guest.estimated_datetime = update_data['estimated_datetime']
            del update_data['estimated_datetime']

        for field, value in update_data.items():
            if field != 'estimated_time': # Legacy field check
                setattr(guest, field, value)

        db.commit()
        db.refresh(guest)
        return guest

    @staticmethod
    def _archive_image(image_path: str):
        try:
            archive_dir = os.path.join(config.settings.UPLOAD_DIR, "archived_guests")
            os.makedirs(archive_dir, exist_ok=True)

            source_path = os.path.join(config.settings.UPLOAD_DIR, image_path)
            if os.path.exists(source_path):
                file_name = os.path.basename(image_path)
                dest_path = os.path.join(archive_dir, file_name)
                if os.path.exists(dest_path):
                     dest_path = os.path.join(archive_dir, f"{uuid.uuid4()}_{file_name}")
                os.rename(source_path, dest_path)
                logger.info(f"Archived image from {source_path} to {dest_path}")
        except Exception as e:
            logger.error(f"Could not archive image file {image_path}: {e}")

    @staticmethod
    def delete_guest(
        db: Session,
        guest_id: int,
        user: models.User,
        bg_tasks
    ) -> bool:
        """
        Delete a guest and archive their images.
        """
        guest = db.query(models.Guest).options(joinedload(models.Guest.images)).get(guest_id)
        if not guest:
            return False # Not found
        
        if user.role not in ("admin", "manager") and not (user.role == "staff" and guest.registered_by_user_id == user.id):
             raise PermissionError("Not allowed")

        for image in guest.images:
            GuestService._archive_image(image.image_path)

        guest_info_for_sheet = {
            "full_name": guest.full_name,
            "estimated_datetime": guest.estimated_datetime
        }

        db.delete(guest)
        db.commit()

        # Sheet cleanup
        if config.settings.GSHEETS_LIVE_SHEET_ID:
            def bg_delete_sheet_row(sheet_id, info):
                try:
                    service = _get_service()
                    delete_row_by_guest_info(service, sheet_id, info)
                except Exception as e:
                    logger.error(f"Background sheet deletion failed: {e}")

            bg_tasks.add_task(bg_delete_sheet_row, config.settings.GSHEETS_LIVE_SHEET_ID, guest_info_for_sheet)

        return True

    @staticmethod
    def get_suggestions(db: Session) -> dict:
        """
        Get suggestions for forms.
        """
        license_plates = db.query(models.Guest.license_plate).filter(models.Guest.license_plate != "").distinct().all()
        supplier_names = db.query(models.Guest.supplier_name).filter(models.Guest.supplier_name != "").distinct().all()
        return {
            "companies": [],
            "license_plates": [lp[0] for lp in license_plates if lp[0]],
            "supplier_names": [sn[0] for sn in supplier_names if sn[0]]
        }
    
    @staticmethod
    def delete_old_pending_guests(db: Session) -> int:
        """
        Delete old pending guests.
        """
        tz = pytz.timezone(config.settings.TZ)
        today_start = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
        
        old_guests = db.query(models.Guest).filter(
            models.Guest.status == "pending",
            models.Guest.created_at < today_start,
            models.Guest.estimated_datetime < today_start
        ).options(joinedload(models.Guest.images)).all()
        
        if not old_guests:
            return 0
        
        deleted_count = 0
        for guest in old_guests:
            for image in guest.images:
                GuestService._archive_image(image.image_path)
            db.delete(guest)
            deleted_count += 1
        
        db.commit()
        return deleted_count

    @staticmethod
    def confirm_check_in(
        db: Session,
        guest_id: int,
        user: models.User,
        bg_tasks
    ) -> models.Guest:
        """
        Confirm guest check-in.
        """
        guest = db.query(models.Guest).options(joinedload(models.Guest.registered_by)).get(guest_id)
        if not guest:
            return None

        guest_updated = False
        if guest.status != "checked_in":
            guest.status = "checked_in"
            guest.check_in_time = models.get_local_time()
            db.commit()
            db.refresh(guest)
            guest_updated = True
            logger.info(f"User {user.username} confirmed check-in for guest ID {guest_id} ({guest.full_name}).")
        else:
            logger.info(f"Guest ID {guest_id} ({guest.full_name}) already checked in. No status change.")

        if guest_updated:
            bg_tasks.add_task(send_event_to_archive_background, guest.id, "Xác nhận vào cổng", user.id)
            bg_tasks.add_task(run_pending_list_notification)

        return guest

    @staticmethod
    def confirm_check_out(
        db: Session,
        guest_id: int,
        user: models.User,
        bg_tasks
    ) -> models.Guest:
        """
        Confirm guest check-out.
        """
        guest = db.query(models.Guest).options(joinedload(models.Guest.registered_by)).get(guest_id)
        if not guest:
            return None

        if guest.status == "checked_out":
             logger.info(f"Guest ID {guest_id} ({guest.full_name}) already checked out. No status change.")
             return guest

        guest.status = "checked_out"
        guest.check_out_time = models.get_local_time()
        db.commit()
        db.refresh(guest)
        
        logger.info(f"User {user.username} confirmed check-out for guest ID {guest_id} ({guest.full_name}).")

        bg_tasks.add_task(send_event_to_archive_background, guest.id, "Xác nhận ra cổng", user.id)
        bg_tasks.add_task(run_pending_list_notification)

        return guest

    @staticmethod
    def upload_guest_image(db: Session, guest_id: int, file, save_path_prefix: str) -> models.GuestImage:
        guest = db.query(models.Guest).get(guest_id)
        if not guest:
            return None

        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        
        # Determine full save path
        full_save_path = os.path.join(config.settings.UPLOAD_DIR, "guests", unique_filename)
        os.makedirs(os.path.dirname(full_save_path), exist_ok=True)
        
        # Save file (caller handles async read if needed, but here we assume file-like or bytes)
        # Note: passed 'file' here is UploadFile from FastAPI. logic needs async. 
        # But we are in sync method? Service methods can be async.
        # Let's make this async or handle it in router. 
        # Better: caller reads content and passes bytes.
        raise NotImplementedError("Handle in router due to async read")

    # Actually, for file upload, it's often easier to keep in router or make service async.
    # I will modify this to take 'file_content' (bytes).
    @staticmethod
    def upload_guest_image_bytes(db: Session, guest_id: int, file_filename: str, file_content: bytes) -> models.GuestImage:
        guest = db.query(models.Guest).get(guest_id)
        if not guest:
            return None

        ext = os.path.splitext(file_filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"

        save_path = os.path.join(config.settings.UPLOAD_DIR, "guests", unique_filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as buffer:
            buffer.write(file_content)

        db_image = models.GuestImage(
            guest_id=guest_id,
            image_path=f"guests/{unique_filename}"
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        return db_image

    @staticmethod
    def delete_guest_image(db: Session, image_id: int, user: models.User) -> bool:
        db_image = db.query(models.GuestImage).options(joinedload(models.GuestImage.guest)).get(image_id)
        if not db_image:
            return False # Not found

        guest = db_image.guest
        if not guest:
            return False # Orphaned

        is_admin_or_manager = user.role in ("admin", "manager")
        is_owner = guest.registered_by_user_id == user.id

        if not (is_admin_or_manager or is_owner):
            raise PermissionError("Not allowed")

        GuestService._archive_image(db_image.image_path)
        db.delete(db_image)
        db.commit()
        return True

    @staticmethod
    def import_guests(db: Session, file_content: bytes, user: models.User) -> dict:
        try:
            df = pd.read_excel(io.BytesIO(file_content), keep_default_na=False)
            df.dropna(how='all', inplace=True)

            users_cache = {u.username: u for u in db.query(models.User).all()}
            imported_count = 0

            for index, row in df.iterrows():
                if not row.get("Họ tên"):
                    logger.warning(f"Bỏ qua dòng {index + 2}: Thiếu họ tên.")
                    continue

                status_str = str(row.get("Trạng thái", "")).strip()
                status = "checked_in" if status_str == "ĐÃ VÀO" else "pending"

                check_in_time = None
                if status == "checked_in" and row.get("Giờ vào"):
                    try:
                        time_val = row.get("Giờ vào")
                        if isinstance(time_val, datetime):
                            check_in_time = time_val
                        else:
                            for fmt in ("%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M"):
                                 try:
                                     check_in_time = datetime.strptime(str(time_val), fmt)
                                     break
                                 except ValueError:
                                     continue
                            if not check_in_time:
                                 logger.warning(f"Không thể phân tích 'Giờ vào' '{time_val}' cho '{row.get('Họ tên')}' ở dòng {index+2}. Dùng giờ hiện tại.")
                    except Exception as e:
                        logger.warning(f"Lỗi khi xử lý 'Giờ vào' '{row.get('Giờ vào')}' cho '{row.get('Họ tên')}' ở dòng {index+2}. Lỗi: {e}")

                registered_by_user_id = user.id
                registered_by_username = str(row.get("Mã NV đăng ký", "")).strip()
                if registered_by_username in users_cache:
                    registered_by_user_id = users_cache[registered_by_username].id
                else:
                     logger.warning(f"Không tìm thấy username '{registered_by_username}' ở dòng {index+2}. Gán khách '{row.get('Họ tên')}' cho người import '{user.username}'.")

                license_plate_raw = row.get("Biển số", "")
                
                estimated_datetime_val = row.get("Ngày giờ dự kiến")
                estimated_datetime_obj = None

                if pd.notna(estimated_datetime_val):
                    try:
                        if isinstance(estimated_datetime_val, datetime):
                            estimated_datetime_obj = estimated_datetime_val
                        else:
                            for fmt_dt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M"):
                                try:
                                    estimated_datetime_obj = datetime.strptime(str(estimated_datetime_val), fmt_dt)
                                    break
                                except ValueError:
                                    continue
                    except Exception:
                         logger.warning(f"Không thể phân tích 'Ngày giờ dự kiến' '{estimated_datetime_val}' ở dòng {index+2}. Bỏ qua.")

                guest = models.Guest(
                    full_name=row.get("Họ tên", ""),
                    id_card_number=str(row.get("CCCD", "")),
                    supplier_name=row.get("Nhà cung cấp", row.get("Công ty", "")),
                    company=row.get("Công ty", ""),
                    reason=row.get("Lý do", ""),
                    license_plate=format_license_plate(license_plate_raw) if license_plate_raw else "",
                    status=status,
                    check_in_time=check_in_time,
                    estimated_datetime=estimated_datetime_obj,
                    registered_by_user_id=registered_by_user_id
                )

                image_paths_str = row.get("Hình ảnh", "")
                if image_paths_str and isinstance(image_paths_str, str):
                    image_paths = [path.strip() for path in image_paths_str.split(',') if path.strip()]
                    for path in image_paths:
                        if not path.startswith("guests/"): continue

                        full_path = os.path.join(config.settings.UPLOAD_DIR, path)
                        base_name = os.path.basename(path)
                        archived_path = os.path.join(config.settings.UPLOAD_DIR, "archived_guests", base_name)

                        if not os.path.exists(full_path) and os.path.exists(archived_path):
                            try:
                                os.rename(archived_path, full_path)
                                logger.info(f"Khôi phục ảnh lưu trữ từ {archived_path} về {full_path}")
                            except Exception as e:
                                logger.error(f"Không thể khôi phục ảnh {base_name}: {e}")

                        if os.path.exists(full_path):
                            image_record = models.GuestImage(image_path=path)
                            guest.images.append(image_record)
                        else:
                            logger.warning(f"Đường dẫn ảnh '{path}' được liệt kê trong file import nhưng không tìm thấy file.")

                db.add(guest)
                imported_count += 1

            db.commit()
            return {"ok": True, "message": f"Import thành công {imported_count} bản ghi."}
        except Exception as e:
            db.rollback()
            logger.error(f"Xử lý file thất bại: {e}", exc_info=True)
            raise ValueError(f"Xử lý file thất bại: {e}")

    @staticmethod
    def export_guests(
        db: Session,
        user: models.User,
        start_date: str | None = None,
        end_date: str | None = None,
        registrant_id: int | None = None,
        supplier_name: str | None = None,
        status: str | None = None
    ):
        query = db.query(
            models.Guest,
            models.User.full_name.label("registered_by_name"),
            models.User.username.label("registered_by_username")
        ).join(
            models.User, models.Guest.registered_by_user_id == models.User.id
        ).options(joinedload(models.Guest.images))

        if user.role == "staff":
            query = query.filter(models.Guest.registered_by_user_id == user.id)
        elif registrant_id:
            query = query.filter(models.Guest.registered_by_user_id == registrant_id)
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(models.Guest.created_at >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(models.Guest.created_at <= end_dt)
            except ValueError:
                pass

        if supplier_name:
             query = query.filter(models.Guest.supplier_name.ilike(f"%{supplier_name}%"))

        if status:
            query = query.filter(models.Guest.status == status)

        results = query.order_by(models.Guest.created_at.desc()).all()

        data_to_export = []
        for idx, (guest, registered_by_name, registered_by_username) in enumerate(results, start=1):
            check_in_str = ""
            if guest.check_in_time:
                check_in_str = guest.check_in_time.strftime("%d/%m/%Y %H:%M")
            
            check_out_str = ""
            if guest.check_out_time:
                check_out_str = guest.check_out_time.strftime("%d/%m/%Y %H:%M")
            
            data_to_export.append({
                "STT": idx,
                "Giờ vào": check_in_str,
                "Giờ ra": check_out_str,
                "Họ tên": guest.full_name,
                "CCCD": guest.id_card_number,
                "Nhà thầu": guest.supplier_name,
                "Biển số": guest.license_plate,
                "Người đăng ký": registered_by_name,
                "Mã nv": registered_by_username,
                "Lý do": guest.reason
            })

        df = pd.DataFrame(data_to_export)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Guests', startrow=1, header=True)
            
            workbook = writer.book
            worksheet = writer.sheets['Guests']
            
            worksheet.set_paper(8)
            worksheet.set_landscape()
            
            title_format = workbook.add_format({
                'font_name': 'Courier New',
                'font_size': 15,
                'bold': True,
                'align': 'center',
                'valign': 'vcenter'
            })
            
            header_format = workbook.add_format({
                'font_name': 'Courier New',
                'font_size': 11,
                'bold': True,
                'align': 'left',
                'valign': 'vcenter'
            })
            
            data_format = workbook.add_format({
                'font_name': 'Courier New',
                'font_size': 11,
                'align': 'left',
                'valign': 'vcenter'
            })
            
            num_columns = len(df.columns)
            worksheet.merge_range(0, 0, 0, num_columns - 1, 'SỔ THEO DÕI KHÁCH RA/VÀO', title_format)
            
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(1, col_num, value, header_format)
            
            for row_num in range(len(df)):
                for col_num in range(len(df.columns)):
                    worksheet.write(row_num + 2, col_num, df.iloc[row_num, col_num], data_format)
            
            for col_num, column in enumerate(df.columns):
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                worksheet.set_column(col_num, col_num, column_width + 2)

        output.seek(0)
        return output

    @staticmethod
    def clear_all_guests(db: Session, user: models.User) -> bool:
        if user.role != "admin":
            raise PermissionError("Only admin")
            
        all_images = db.query(models.GuestImage).all()
        for image in all_images:
            GuestService._archive_image(image.image_path)

        db.query(models.GuestImage).delete()
        db.query(models.Guest).delete()
        db.commit()
        return True

class LongTermGuestService:
    @staticmethod
    def create_long_term_guest(
        db: Session, 
        payload: schemas.LongTermGuestCreate, 
        user: models.User
    ) -> models.LongTermGuest:
        # Validate start and end dates
        if payload.end_date < payload.start_date:
            raise ValueError("End date cannot be earlier than start date.")

        db_long_term_guest = models.LongTermGuest(
            **payload.model_dump(),
            registered_by_user_id=user.id
        )
        db.add(db_long_term_guest)
        db.commit()

        # Sync logic: Create Guest for today if applicable
        today = models.get_local_time().date()
        if db_long_term_guest.start_date <= today <= db_long_term_guest.end_date:
            existing_guest = db.query(models.Guest).filter(
                models.Guest.full_name == payload.full_name,
                models.Guest.id_card_number == (payload.id_card_number or ""),
                func.date(models.Guest.created_at) == today,
                models.Guest.registered_by_user_id == user.id
            ).first()

            if not existing_guest:
                guest_for_today = models.Guest(
                    full_name=payload.full_name,
                    id_card_number=payload.id_card_number or "",
                    company=payload.company or "",
                    reason=payload.reason or "",
                    license_plate=payload.license_plate or "",
                    supplier_name=payload.supplier_name or "",
                    status="pending",
                    estimated_datetime=payload.estimated_datetime,
                    registered_by_user_id=user.id,
                    created_at=models.get_local_time()
                )
                db.add(guest_for_today)
                db.commit()

        db.refresh(db_long_term_guest)
        return db_long_term_guest

    @staticmethod
    def get_long_term_guests(db: Session, user: models.User) -> List[models.LongTermGuest]:
        query = db.query(models.LongTermGuest).options(joinedload(models.LongTermGuest.registered_by))
        if user.role == 'staff':
            query = query.filter(models.LongTermGuest.registered_by_user_id == user.id)
        
        return query.order_by(models.LongTermGuest.created_at.desc()).all()

    @staticmethod
    def update_long_term_guest(
        db: Session, 
        guest_id: int, 
        payload: schemas.LongTermGuestUpdate, 
        user: models.User
    ) -> models.LongTermGuest:
        db_guest = db.query(models.LongTermGuest).get(guest_id)
        if not db_guest:
            return None
        
        if user.role == 'staff' and db_guest.registered_by_user_id != user.id:
            raise PermissionError("Not authorized")

        update_data = payload.model_dump(exclude_unset=True)

        start_date = update_data.get('start_date', db_guest.start_date)
        end_date = update_data.get('end_date', db_guest.end_date)
        if end_date < start_date:
             raise ValueError("End date cannot be earlier than start date.")

        if 'estimated_datetime' in update_data:
            db_guest.estimated_datetime = update_data['estimated_datetime']
            del update_data['estimated_datetime']

        for key, value in update_data.items():
            if key != 'estimated_time':
                setattr(db_guest, key, value)
        
        db.commit()
        db.refresh(db_guest)
        return db_guest

    @staticmethod
    def cleanup_old_long_term_guests(db: Session, user: models.User) -> int:
        if user.role not in ['admin', 'manager']:
             raise PermissionError("Chỉ admin/manager mới có quyền xóa dữ liệu cũ")
        
        today = models.get_local_time().date()
        old_guests = db.query(models.LongTermGuest).filter(models.LongTermGuest.end_date < today).all()
        
        deleted_count = len(old_guests)
        for guest in old_guests:
            db.delete(guest)
        
        db.commit()
        return deleted_count

    @staticmethod
    def delete_long_term_guest(db: Session, guest_id: int, user: models.User) -> bool:
        db_guest = db.query(models.LongTermGuest).get(guest_id)
        if not db_guest:
            return False
        
        if user.role not in ('admin', 'manager') and db_guest.registered_by_user_id != user.id:
             raise PermissionError("Not authorized")
        
        db.delete(db_guest)
        db.commit()
        return True

    @staticmethod
    def process_daily_entries(db: Session, tz_name: str) -> int:
        """
        Create daily guest entries from active long-term guests.
        """
        from datetime import time, datetime
        from app.models import LongTermGuest, Guest, get_local_time
        import pytz
        from sqlalchemy import select

        today = datetime.now(pytz.timezone(tz_name)).date()
        
        active_long_term_guests = db.scalars(
            select(LongTermGuest).where(
                LongTermGuest.is_active == True,
                LongTermGuest.start_date <= today,
                LongTermGuest.end_date >= today
            )
        ).all()

        start_of_day = datetime.combine(today, time.min, tzinfo=pytz.timezone(tz_name))
        end_of_day = datetime.combine(today, time.max, tzinfo=pytz.timezone(tz_name))

        # Check for ANY guest with same ID card created today (to avoid duplicates)
        existing_guests_today = db.scalars(
            select(Guest.id_card_number).where(
                Guest.created_at >= start_of_day,
                Guest.created_at <= end_of_day,
                Guest.id_card_number != ""
            )
        ).all()
        existing_guest_set = set(existing_guests_today)

        count = 0
        for lt_guest in active_long_term_guests:
            if lt_guest.id_card_number and lt_guest.id_card_number not in existing_guest_set:
                # Use the original registrant's ID
                registrant_id = lt_guest.registered_by_user_id
                
                new_guest = Guest(
                    full_name=lt_guest.full_name,
                    id_card_number=lt_guest.id_card_number,
                    company=lt_guest.company or lt_guest.supplier_name,
                    reason=lt_guest.reason or "Khách đăng ký dài hạn",
                    license_plate=lt_guest.license_plate,
                    supplier_name=lt_guest.supplier_name,
                    estimated_datetime=lt_guest.estimated_datetime,
                    status="pending",
                    registered_by_user_id=registrant_id,
                    created_at=get_local_time()
                )
                db.add(new_guest)
                existing_guest_set.add(lt_guest.id_card_number)
                count += 1
        
        if count > 0:
            db.commit()
        return count

guest_service = GuestService()
long_term_guest_service = LongTermGuestService()
