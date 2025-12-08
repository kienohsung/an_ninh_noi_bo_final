# File: backend/app/routers/vehicle_log.py
from __future__ import annotations
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
import logging

from ..core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/vehicle-log", 
    tags=["Vehicle Log"],
    dependencies=[Depends(get_current_user)]
)



@router.get("", response_class=JSONResponse)
def list_vehicle_log(
    quick: Optional[str] = Query(None, description="Khoảng thời gian nhanh: today, last7, last30, thisWeek, thisMonth, prevMonth"),
    start: Optional[str] = Query(None, description="Ngày bắt đầu (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="Ngày kết thúc (YYYY-MM-DD)"),
    q: Optional[str] = Query(None, description="Từ khóa tìm kiếm (biển số xe)"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=200)
):
    from ..modules.vehicle_log.service import vehicle_log_service
    try:
        rows, charts, kpi = vehicle_log_service.get_vehicle_logs(quick, start, end, q)

        total_records = len(rows)
        start_index = (page - 1) * pageSize
        end_index = start_index + pageSize
        paginated_rows = rows[start_index:end_index]

        items = [{
            "plate": r.get("plate", ""),
            "date": r["date"].isoformat() if r.get("date") else "",
            "time": r["time"].strftime("%H:%M:%S") if r.get("time") else ""
        } for r in paginated_rows]

        return {
            "total": total_records,
            "page": page,
            "pageSize": pageSize,
            "items": items,
            "chart": charts,
            "kpi": kpi
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Lỗi không xác định trong endpoint vehicle-log: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi máy chủ nội bộ không xác định: {e}")

@router.get("/export")
def export_vehicle_log_to_excel(
    quick: Optional[str] = Query(None),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
):
    from ..modules.vehicle_log.service import vehicle_log_service
    try:
        output, filename = vehicle_log_service.generate_excel_export(quick, start, end, q)
        
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"'
        }

        return StreamingResponse(
            output, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Lỗi khi xuất file Excel: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Không thể tạo file Excel: {e}")

