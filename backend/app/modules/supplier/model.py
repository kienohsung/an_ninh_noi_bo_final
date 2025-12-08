from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, index=True, nullable=False)

    plates = relationship("SupplierPlate", back_populates="supplier", cascade="all, delete-orphan")

class SupplierPlate(Base):
    __tablename__ = "supplier_plates"
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    plate = Column(String(32), index=True, nullable=False)

    supplier = relationship("Supplier", back_populates="plates", foreign_keys=[supplier_id])
    __table_args__ = (UniqueConstraint("supplier_id", "plate", name="uq_supplier_plate"),)
