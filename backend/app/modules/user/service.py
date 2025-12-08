from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
import logging
import io
import pandas as pd

from app import models
from app.modules.user import schema as schemas
from app.core import config
from app.core.auth import get_password_hash
from app.core.database import unaccent_string

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    def create_user(db: Session, payload: schemas.UserCreate) -> models.User:
        if db.query(models.User).filter(models.User.username == payload.username).first():
            raise ValueError("Username already exists")
        
        user = models.User(
            username=payload.username, 
            password_hash=get_password_hash(payload.password),
            full_name=payload.full_name, 
            role=payload.role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def list_users(db: Session, q: str | None = None) -> List[models.User]:
        query = db.query(models.User)
        if q:
            unaccented_q = unaccent_string(q)
            like = f"%{unaccented_q}%"
            query = query.filter(or_(
                models.User.username.ilike(like), 
                func.unaccent(models.User.full_name).ilike(like), 
                models.User.role.ilike(like)
            ))
        return query.order_by(models.User.created_at.desc()).all()

    @staticmethod
    def update_user(db: Session, user_id: int, payload: schemas.UserUpdate) -> models.User:
        user = db.query(models.User).get(user_id)
        if not user:
            return None

        if payload.username and payload.username != user.username:
            if db.query(models.User).filter(models.User.username == payload.username).first():
                raise ValueError("New username already exists")
            user.username = payload.username

        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.role is not None:
            user.role = payload.role
        if payload.password is not None and payload.password.strip():
            user.password_hash = get_password_hash(payload.password)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        user = db.query(models.User).get(user_id)
        if not user:
            return False
        
        # Admin protection
        if user.username == config.settings.ADMIN_USERNAME:
            raise PermissionError("Cannot delete the default admin user.")
            
        db.delete(user)
        db.commit()
        return True

    @staticmethod
    def clear_users(db: Session) -> int:
        # Delete all users except the admin
        try:
            num_deleted = db.query(models.User).filter(models.User.username != config.settings.ADMIN_USERNAME).delete()
            db.commit()
            return num_deleted
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def export_users(db: Session):
        users = db.query(models.User).all()
        data_to_export = [
            {
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
                "password_hash": user.password_hash,
                "password": "" 
            }
            for user in users
        ]
        
        df = pd.DataFrame(data_to_export)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Users')
        
        output.seek(0)
        return output

    @staticmethod
    def import_users(db: Session, file_content: bytes) -> int:
        try:
            df = pd.read_excel(io.BytesIO(file_content), keep_default_na=False)
            df.dropna(how='all', inplace=True)

            imported_count = 0
            for index, row in df.iterrows():
                try:
                    username = str(row.get("username", "")).strip()
                    full_name = str(row.get("full_name", "")).strip()
                    role = str(row.get("role", "")).strip()
                    
                    if not all([username, full_name, role]):
                        logger.warning(f"Skipping row {index + 2} due to missing data.")
                        continue
                    
                    if username == config.settings.ADMIN_USERNAME:
                        continue

                    if db.query(models.User).filter(models.User.username == username).first():
                        continue

                    password_hash = str(row.get("password_hash", "")).strip()
                    password = str(row.get("password", "")).strip()

                    final_hash = ""
                    if password_hash:
                        final_hash = password_hash
                    elif password:
                        final_hash = get_password_hash(password)
                    else:
                        continue

                    user = models.User(
                        username=username,
                        full_name=full_name,
                        role=role,
                        password_hash=final_hash
                    )
                    db.add(user)
                    imported_count += 1
                except Exception:
                    continue
            db.commit()
            return imported_count
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to import file: {e}")

user_service = UserService()
