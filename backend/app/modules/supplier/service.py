from sqlalchemy.orm import Session
import logging
from typing import List, Optional
import io
import pandas as pd

from app import models
from app.modules.supplier import schema as schemas

logger = logging.getLogger(__name__)

class SupplierService:
    @staticmethod
    def create_supplier(db: Session, payload: schemas.SupplierCreate) -> models.Supplier:
        if db.query(models.Supplier).filter(models.Supplier.name == payload.name).first():
            raise ValueError("Supplier exists")
        s = models.Supplier(name=payload.name)
        db.add(s)
        db.commit()
        db.refresh(s)
        return s

    @staticmethod
    def list_suppliers(db: Session) -> List[models.Supplier]:
        return db.query(models.Supplier).all()

    @staticmethod
    def update_supplier(db: Session, supplier_id: int, payload: schemas.SupplierUpdate) -> models.Supplier:
        s = db.query(models.Supplier).get(supplier_id)
        if not s:
            return None
        if payload.name is not None:
            s.name = payload.name
        db.commit()
        db.refresh(s)
        return s

    @staticmethod
    def delete_supplier(db: Session, supplier_id: int) -> bool:
        s = db.query(models.Supplier).get(supplier_id)
        if not s:
            return False
        db.delete(s)
        db.commit()
        return True

    @staticmethod
    def add_plate(db: Session, supplier_id: int, payload: schemas.SupplierPlateCreate) -> models.SupplierPlate:
        s = db.query(models.Supplier).get(supplier_id)
        if not s:
            return None
        p = models.SupplierPlate(supplier_id=supplier_id, plate=payload.plate.upper())
        db.add(p)
        db.commit()
        db.refresh(p)
        return p

    @staticmethod
    def list_plates(db: Session, supplier_id: int) -> List[models.SupplierPlate]:
        return db.query(models.SupplierPlate).filter_by(supplier_id=supplier_id).all()

    @staticmethod
    def delete_plate(db: Session, supplier_id: int, plate_id: int) -> bool:
        p = db.query(models.SupplierPlate).get(plate_id)
        if not p or p.supplier_id != supplier_id:
            return False
        db.delete(p)
        db.commit()
        return True

    @staticmethod
    def clear_suppliers(db: Session):
        try:
            db.query(models.SupplierPlate).delete(synchronize_session=False)
            db.query(models.Supplier).delete(synchronize_session=False)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def export_suppliers(db: Session):
        df = pd.read_sql(db.query(models.Supplier).statement, db.bind)
        bio = io.BytesIO()
        df.to_excel(bio, index=False, sheet_name="suppliers")
        bio.seek(0)
        return bio

    @staticmethod
    def import_suppliers(db: Session, file_content: bytes):
        try:
            df = pd.read_excel(io.BytesIO(file_content)).fillna('')
        except Exception as e:
            raise ValueError(f"Invalid Excel file: {e}")
        
        for _, row in df.iterrows():
            try:
                if not row.get("name"):
                    continue
                if not db.query(models.Supplier).filter_by(name=row["name"]).first():
                    db.add(models.Supplier(name=row["name"]))
            except Exception as e:
                logger.error(f"Failed to process row: {row.to_dict()}", exc_info=True)
                continue
                
        db.commit()

supplier_service = SupplierService()
