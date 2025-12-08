from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime, date, timedelta
import io
import pandas as pd
import logging
from app.services.gsheets_reader import filter_and_aggregate

logger = logging.getLogger(__name__)

class VehicleLogService:
    @staticmethod
    def parse_date(s: Optional[str]) -> Optional[date]:
        if not s: return None
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            logger.warning(f"Invalid date format received: {s}")
            return None

    @staticmethod
    def quick_range_to_dates(quick: Optional[str]) -> Tuple[Optional[date], Optional[date]]:
        if not quick: return (None, None)
        today = date.today()
        if quick == "today":
            return (today, today)
        if quick == "last7":
            return (today - timedelta(days=6), today)
        if quick == "last30":
            return (today - timedelta(days=29), today)
        if quick == "thisWeek":
            start = today - timedelta(days=today.weekday())
            return (start, today)
        if quick == "thisMonth":
            start = today.replace(day=1)
            return (start, today)
        if quick == "prevMonth":
            first_this = today.replace(day=1)
            last_prev = first_this - timedelta(days=1)
            start = last_prev.replace(day=1)
            end = last_prev
            return (start, end)
        return (None, None)

    def get_vehicle_logs(
        self, 
        quick: Optional[str] = None, 
        start: Optional[str] = None, 
        end: Optional[str] = None, 
        q: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Any, Any]:
        start_date, end_date = self.quick_range_to_dates(quick)
        if start:
            start_date_parsed = self.parse_date(start)
            if start_date_parsed: start_date = start_date_parsed
        
        if end:
            end_date_parsed = self.parse_date(end)
            if end_date_parsed: end_date = end_date_parsed

        if start_date and end_date and start_date > end_date:
            raise ValueError("Ngày bắt đầu không thể lớn hơn ngày kết thúc.")

        try:
            logger.info(f"Fetching vehicle logs. Quick={quick}, Start={start_date}, End={end_date}, Q={q}")
            rows, charts, kpi = filter_and_aggregate(q=q, start=start_date, end=end_date)
            logger.info(f"Vehicle logs fetched. Rows={len(rows)}")
            return rows, charts, kpi
        except FileNotFoundError as e:
            logger.critical(f"CRITICAL ERROR in GSheet service: {e}")
            raise FileNotFoundError("Lỗi nghiêm trọng: Không tìm thấy file credentials.json của Google. Vui lòng kiểm tra lại cấu hình.")
        except Exception as service_exc:
            logger.error(f"Error calling GSheet service: {service_exc}", exc_info=True)
            raise RuntimeError(f"Không thể kết nối hoặc đọc dữ liệu từ Google Sheets. Chi tiết: {service_exc}")

    def generate_excel_export(
        self,
        quick: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        q: Optional[str] = None
    ) -> Tuple[io.BytesIO, str]:
        rows, _, _ = self.get_vehicle_logs(quick, start, end, q)
        
        export_data = [{
            "Số xe": r.get("plate", ""),
            "Ngày": r["date"].strftime("%Y-%m-%d") if r.get("date") else "",
            "Giờ": r["time"].strftime("%H:%M:%S") if r.get("time") else ""
        } for r in rows]
        
        df = pd.DataFrame(export_data)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="NhatKyXe")
        output.seek(0)

        today_str = date.today().strftime("%Y%m%d")
        filename = f"NhatKyXe_Export_{today_str}.xlsx"
        
        return output, filename

vehicle_log_service = VehicleLogService()
