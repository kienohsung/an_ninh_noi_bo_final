# File: backend/app/modules/supplier/normalization_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging
from typing import List, Dict, Tuple
from collections import defaultdict
import Levenshtein

from app import models
from app.modules.supplier import schema as schemas

logger = logging.getLogger(__name__)


class SupplierNormalizationService:
    """Service xử lý chuẩn hóa tên nhà cung cấp"""
    
    SIMILARITY_THRESHOLD = 0.85  # 85% similarity
    
    @staticmethod
    def _normalize_name(name: str) -> str:
        """Chuẩn hóa tên để so sánh: lowercase, strip, remove extra spaces"""
        if not name:
            return ""
        return " ".join(name.lower().strip().split())
    
    @staticmethod
    def _calculate_similarity(name1: str, name2: str) -> float:
        """Tính toán similarity score giữa 2 tên (0-1)"""
        if not name1 or not name2:
            return 0.0
        
        normalized1 = SupplierNormalizationService._normalize_name(name1)
        normalized2 = SupplierNormalizationService._normalize_name(name2)
        
        if normalized1 == normalized2:
            return 1.0
        
        # Sử dụng Levenshtein ratio
        return Levenshtein.ratio(normalized1, normalized2)
    
    @staticmethod
    def _get_all_supplier_names(db: Session) -> Dict[str, Dict[str, int]]:
        """
        Lấy tất cả tên NCC từ các bảng
        Returns: {supplier_name: {table_name: count}}
        """
        result = defaultdict(lambda: defaultdict(int))
        
        # Lấy từ guests
        guests_data = db.query(
            models.Guest.supplier_name,
            func.count(models.Guest.id)
        ).filter(
            models.Guest.supplier_name != "",
            models.Guest.supplier_name.isnot(None)
        ).group_by(models.Guest.supplier_name).all()
        
        for name, count in guests_data:
            result[name]["guests"] = count
        
        # Lấy từ long_term_guests
        lt_guests_data = db.query(
            models.LongTermGuest.supplier_name,
            func.count(models.LongTermGuest.id)
        ).filter(
            models.LongTermGuest.supplier_name != "",
            models.LongTermGuest.supplier_name.isnot(None)
        ).group_by(models.LongTermGuest.supplier_name).all()
        
        for name, count in lt_guests_data:
            result[name]["long_term_guests"] = count
        
        # Lấy từ purchasing_log
        from app.modules.purchasing.model import PurchasingLog
        purchasing_data = db.query(
            PurchasingLog.supplier_name,
            func.count(PurchasingLog.id)
        ).filter(
            PurchasingLog.supplier_name != "",
            PurchasingLog.supplier_name.isnot(None)
        ).group_by(PurchasingLog.supplier_name).all()
        
        for name, count in purchasing_data:
            result[name]["purchasing_log"] = count
        
        return dict(result)
    
    @staticmethod
    def _group_similar_names(
        names_data: Dict[str, Dict[str, int]]
    ) -> List[List[str]]:
        """
        Nhóm các tên tương tự lại với nhau
        Returns: List of groups, mỗi group là list các tên tương tự
        """
        names = list(names_data.keys())
        groups = []
        processed = set()
        
        for i, name1 in enumerate(names):
            if name1 in processed:
                continue
            
            # Tạo nhóm mới với name1
            current_group = [name1]
            processed.add(name1)
            
            # Tìm các tên tương tự
            for j, name2 in enumerate(names[i+1:], start=i+1):
                if name2 in processed:
                    continue
                
                similarity = SupplierNormalizationService._calculate_similarity(
                    name1, name2
                )
                
                if similarity >= SupplierNormalizationService.SIMILARITY_THRESHOLD:
                    current_group.append(name2)
                    processed.add(name2)
            
            # Chỉ thêm nhóm nếu có >= 2 variants
            if len(current_group) >= 2:
                groups.append(current_group)
        
        return groups
    
    @staticmethod
    def analyze_supplier_names(db: Session) -> schemas.NormalizationAnalysis:
        """
        Phân tích và nhóm các tên NCC tương tự
        """
        try:
            # Lấy tất cả tên NCC
            names_data = SupplierNormalizationService._get_all_supplier_names(db)
            
            if not names_data:
                return schemas.NormalizationAnalysis(groups=[], total_groups=0)
            
            # Nhóm các tên tương tự
            similar_groups = SupplierNormalizationService._group_similar_names(names_data)
            
            # Tạo response
            result_groups = []
            for group_names in similar_groups:
                # Tính tổng số records cho mỗi variant
                variants = []
                total_records = 0
                max_count = 0
                suggested_name = group_names[0]
                
                for name in group_names:
                    tables_data = names_data[name]
                    count = sum(tables_data.values())
                    total_records += count
                    
                    # Tìm tên có count cao nhất làm suggested_name
                    if count > max_count:
                        max_count = count
                        suggested_name = name
                    
                    variants.append(schemas.SupplierVariant(
                        name=name,
                        count=count,
                        tables=list(tables_data.keys())
                    ))
                
                # Tính similarity score trung bình
                similarities = []
                for i, name1 in enumerate(group_names):
                    for name2 in group_names[i+1:]:
                        sim = SupplierNormalizationService._calculate_similarity(
                            name1, name2
                        )
                        similarities.append(sim)
                
                avg_similarity = sum(similarities) / len(similarities) if similarities else 1.0
                
                result_groups.append(schemas.SupplierGroup(
                    variants=variants,
                    suggested_name=suggested_name,
                    total_records=total_records,
                    similarity_score=round(avg_similarity, 3)
                ))
            
            return schemas.NormalizationAnalysis(
                groups=result_groups,
                total_groups=len(result_groups)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing supplier names: {e}", exc_info=True)
            raise
    
    @staticmethod
    def preview_normalization(
        db: Session,
        mappings: Dict[str, str]
    ) -> schemas.NormalizationPreview:
        """
        Preview số lượng bản ghi sẽ bị update
        """
        try:
            old_names = list(mappings.keys())
            
            guests_count = db.query(func.count(models.Guest.id)).filter(
                models.Guest.supplier_name.in_(old_names)
            ).scalar() or 0
            
            lt_guests_count = db.query(func.count(models.LongTermGuest.id)).filter(
                models.LongTermGuest.supplier_name.in_(old_names)
            ).scalar() or 0
            
            from app.modules.purchasing.model import PurchasingLog
            purchasing_count = db.query(func.count(PurchasingLog.id)).filter(
                PurchasingLog.supplier_name.in_(old_names)
            ).scalar() or 0
            
            total = guests_count + lt_guests_count + purchasing_count
            
            return schemas.NormalizationPreview(
                guests=guests_count,
                long_term_guests=lt_guests_count,
                purchasing_log=purchasing_count,
                total=total
            )
            
        except Exception as e:
            logger.error(f"Error previewing normalization: {e}", exc_info=True)
            raise
    
    @staticmethod
    def execute_normalization(
        db: Session,
        mappings: Dict[str, str]
    ) -> schemas.NormalizationResult:
        """
        Thực hiện cập nhật đồng bộ tên NCC
        Sử dụng transaction để đảm bảo rollback nếu có lỗi
        """
        errors = []
        updated_counts = {}
        
        try:
            # Update guests
            guests_updated = 0
            for old_name, new_name in mappings.items():
                count = db.query(models.Guest).filter(
                    models.Guest.supplier_name == old_name
                ).update(
                    {models.Guest.supplier_name: new_name},
                    synchronize_session=False
                )
                guests_updated += count
            
            updated_counts["guests"] = guests_updated
            logger.info(f"Updated {guests_updated} guest records")
            
            # Update long_term_guests
            lt_guests_updated = 0
            for old_name, new_name in mappings.items():
                count = db.query(models.LongTermGuest).filter(
                    models.LongTermGuest.supplier_name == old_name
                ).update(
                    {models.LongTermGuest.supplier_name: new_name},
                    synchronize_session=False
                )
                lt_guests_updated += count
            
            updated_counts["long_term_guests"] = lt_guests_updated
            logger.info(f"Updated {lt_guests_updated} long-term guest records")
            
            # Update purchasing_log
            from app.modules.purchasing.model import PurchasingLog
            purchasing_updated = 0
            for old_name, new_name in mappings.items():
                count = db.query(PurchasingLog).filter(
                    PurchasingLog.supplier_name == old_name
                ).update(
                    {PurchasingLog.supplier_name: new_name},
                    synchronize_session=False
                )
                purchasing_updated += count
            
            updated_counts["purchasing_log"] = purchasing_updated
            logger.info(f"Updated {purchasing_updated} purchasing records")
            
            # Commit transaction
            db.commit()
            
            logger.info(f"Successfully normalized {len(mappings)} supplier names")
            
            return schemas.NormalizationResult(
                success=True,
                updated_records=updated_counts,
                errors=errors
            )
            
        except Exception as e:
            db.rollback()
            error_msg = f"Failed to execute normalization: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            
            return schemas.NormalizationResult(
                success=False,
                updated_records={},
                errors=errors
            )


supplier_normalization_service = SupplierNormalizationService()
