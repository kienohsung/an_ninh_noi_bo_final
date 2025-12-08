# File: backend/app/services/gsheets_reader.py
from __future__ import annotations
from typing import List, Dict, Tuple, Optional
from datetime import datetime, date
from collections import Counter, defaultdict
import pytz
import logging

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..core.config import settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TZ = pytz.timezone(settings.TZ)
logger = logging.getLogger("[GSheet Reader]")

def _get_service():
    """Builds and returns a Google Sheets API service object."""
    logger.info("Attempting to build Google Sheets service...")
    try:
        creds = Credentials.from_service_account_file(settings.GSHEETS_CREDENTIALS_PATH, scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        logger.info("Successfully built Google Sheets service.")
        return service
    except FileNotFoundError:
        logger.error(f"FATAL: Credentials file not found at '{settings.GSHEETS_CREDENTIALS_PATH}'.")
        raise
    except Exception as e:
        logger.error(f"FATAL: Failed to build Google Sheets service: {e}")
        raise

def read_sheet_all(service, sheet_id: str, sheet_name: str) -> List[List]:
    """Reads all values from a given sheet."""
    logger.info(f"Reading sheet ID '{sheet_id[:10]}...' name '{sheet_name}'...")
    try:
        range_name = f"'{sheet_name}'!A:C"
        resp = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name).execute()
        values = resp.get("values", [])
        logger.info(f"Successfully read {len(values)} rows from sheet '{sheet_name}'.")
        return values
    except HttpError as e:
        logger.error(f"API Error reading sheet ID '{sheet_id[:10]}...', name '{sheet_name}': {e.reason}")
        if e.status_code == 403:
            logger.error("Error 403: PERMISSION_DENIED. Please ensure the service account email has 'Viewer' access to this Google Sheet.")
        elif e.status_code == 404:
            logger.error(f"Error 404: Not Found. Check if Sheet ID '{sheet_id}' and Sheet Name '{sheet_name}' are correct.")
        return [] # Return empty on error to avoid crashing
    except Exception as e:
        logger.error(f"An unexpected error occurred while reading sheet '{sheet_name}': {e}")
        return []

def read_form_responses(service, sheet_id: str) -> List[List]:
    """
    Reads form responses from 'Câu trả lời biểu mẫu 1'.
    Uses valueRenderOption='FORMATTED_VALUE' to ensure consistent date strings.
    """
    sheet_name = "Câu trả lời biểu mẫu 1"
    logger.info(f"Reading form responses from '{sheet_name}'...")
    try:
        range_name = f"'{sheet_name}'!A2:K" # Read from A2 to K (skipping header)
        # Use FORMATTED_VALUE to get strings for dates/times
        resp = service.spreadsheets().values().get(
            spreadsheetId=sheet_id, 
            range=range_name, 
            valueRenderOption='FORMATTED_VALUE'
        ).execute()
        values = resp.get("values", [])
        logger.info(f"Successfully read {len(values)} rows from '{sheet_name}'.")
        return values
    except HttpError as e:
        logger.error(f"API Error reading form responses: {e.reason}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error reading form responses: {e}")
        return []

def batch_update_status(service, sheet_id: str, updates: List[Tuple[int, str]]):
    """
    Batch updates the SYNC_STATUS column (Column H) for multiple rows.
    
    Args:
        service: Google Sheets service object
        sheet_id: ID of the spreadsheet
        updates: List of tuples (row_index, status_value). 
                 row_index should be the Excel row number (1-based).
    """
    if not updates:
        return

    sheet_name = "Câu trả lời biểu mẫu 1"
    data = []
    
    for row_idx, status in updates:
        # Construct range for column K (Index 10) at specific row
        # Example: 'Câu trả lời biểu mẫu 1'!K5
        range_name = f"'{sheet_name}'!K{row_idx}"
        data.append({
            "range": range_name,
            "values": [[status]]
        })

    body = {
        "valueInputOption": "RAW",
        "data": data
    }

    try:
        logger.info(f"Batch updating {len(updates)} rows in '{sheet_name}'...")
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=sheet_id, 
            body=body
        ).execute()
        logger.info("Batch update completed successfully.")
    except Exception as e:
        logger.error(f"Failed to batch update status: {e}")

def parse_rows(values: List[List]) -> List[Dict]:
    """Parses raw sheet values into structured dictionaries."""
    if not values or len(values) <= 1:
        return []
    
    parsed_count = 0
    rows = []
    for r in values[1:]:
        if not r or len(r) < 3 or not r[0] or not r[1] or not r[2]:
            continue

        plate = r[0].strip()
        d_raw, t_raw = r[1], r[2]
        d_obj, t_obj = None, None

        if isinstance(d_raw, str) and d_raw:
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                try: d_obj = datetime.strptime(d_raw, fmt).date(); break
                except (ValueError, TypeError): continue
        
        if isinstance(t_raw, str) and t_raw:
            for fmt in ("%H:%M:%S", "%H:%M"):
                try: t_obj = datetime.strptime(t_raw, fmt).time(); break
                except (ValueError, TypeError): continue
        
        if plate and d_obj and t_obj:
            rows.append({"plate": plate, "date": d_obj, "time": t_obj})
            parsed_count += 1
            
    logger.info(f"Successfully parsed {parsed_count} valid rows from raw data.")
    return rows

def month_span(start: date, end: date) -> List[Tuple[int,int]]:
    res = []
    y, m = start.year, start.month
    while True:
        res.append((y, m))
        if y == end.year and m == end.month: break
        m += 1;
        if m > 12: m = 1; y += 1
    return res

def normalize_text(s: Optional[str]) -> str:
    import unicodedata
    return unicodedata.normalize("NFD", (s or "")).encode("ascii", "ignore").decode("ascii").lower().strip()

def filter_and_aggregate(q: Optional[str], start: Optional[date], end: Optional[date]):
    try:
        service = _get_service()
    except Exception:
        # If service fails to build, return empty data to prevent frontend crash
        return [], {"daily": {}, "hours": {}, "heatmap": {}, "top10": {}}, {"totalInRange": "Lỗi"}

    values_all = []
    if settings.GSHEETS_LIVE_SHEET_ID:
        live_values = read_sheet_all(service, settings.GSHEETS_LIVE_SHEET_ID, settings.GSHEETS_SHEET_NAME)
        if live_values and len(live_values) > 1:
            values_all.extend(live_values[1:])

    if start and end:
        logger.info(f"Date range detected. Reading from archive files between {start} and {end}.")
        for y, m in month_span(start, end):
            arch_id = settings.GSHEETS_ARCHIVE_SHEETS.get(str(y))
            if arch_id:
                sheet_name = f"Thang{str(m).zfill(2)}_{y}"
                v = read_sheet_all(service, arch_id, sheet_name)
                if v and len(v) > 1:
                    values_all.extend(v[1:])
    
    rows = parse_rows([["Số xe", "Ngày", "Giờ"]] + values_all)
    logger.info(f"Successfully parsed {len(rows)} rows from all sources.")

    qn = normalize_text(q) if q else ""
    out = []
    for r in rows:
        if start and r["date"] and r["date"] < start: continue
        if end and r["date"] and r["date"] > end: continue
        if qn and qn not in normalize_text(r["plate"]): continue
        out.append(r)

    out.sort(key=lambda x: (x["date"] or date.min, x["time"] or datetime.min.time()), reverse=True)
    logger.info(f"{len(out)} rows remaining after filtering.")

    # --- Aggregation logic (unchanged but now more reliable) ---
    daily, hours, plate_cnt = Counter(), Counter(), Counter()
    heatmap = defaultdict(lambda: Counter())
    for r in out:
        if r["date"]: daily[str(r["date"])] += 1
        if r["time"]: hours[f"{r['time'].hour:02d}"] += 1
        if r["plate"]: plate_cnt[r["plate"]] += 1
        if r["date"] and r["time"]: heatmap[str(r["date"])][f"{r['time'].hour:02d}"] += 1

    daily_labels = sorted(daily.keys())
    daily_series = [daily[k] for k in daily_labels]
    hour_labels = [f"{i:02d}" for i in range(24)]
    hour_series = [hours.get(h, 0) for h in hour_labels]
    top = plate_cnt.most_common(10)
    top_labels = [p for p,_ in top]
    top_series = [c for _,c in top]

    heat_rows = sorted(heatmap.keys())
    matrix = [[heatmap[dkey].get(h, 0) for h in hour_labels] for dkey in heat_rows]

    total = len(out)
    peak_hour = hour_labels[hour_series.index(max(hour_series))] if total>0 and max(hour_series)>0 else None
    top_plate = top_labels[0] if top_labels else None
    avg_per_day = round(sum(daily_series)/len(daily_series), 1) if daily_series else 0.0

    charts = {
        "daily": {"labels": daily_labels, "series": daily_series},
        "hours": {"labels": hour_labels, "series": hour_series},
        "heatmap": {"rows": heat_rows, "cols": hour_labels, "matrix": matrix},
        "top10": {"labels": top_labels, "series": top_series}
    }
    kpi = {"totalInRange": total, "peakHour": peak_hour, "topPlate": top_plate, "avgPerDay": avg_per_day}
    
    return out, charts, kpi

def delete_row_by_guest_info(service, sheet_id: str, guest_info: dict):
    """
    Finds and deletes a row in 'Câu trả lời biểu mẫu 1' matching the guest info.
    Matching criteria:
    - Guest Name (Column C / Index 2)
    - Estimated Date Time (Column I / Index 8) - derived from 'test' column
    """
    sheet_name = "Câu trả lời biểu mẫu 1"
    try:
        # 1. Read all data to find the row index
        rows = read_form_responses(service, sheet_id)
        if not rows:
            logger.warning("No data found in sheet to delete.")
            return

        target_row_index = -1
        
        # guest_info keys: full_name, estimated_datetime (datetime object)
        target_name = normalize_text(guest_info.get("full_name"))
        target_est_dt = guest_info.get("estimated_datetime")

        for i, row in enumerate(rows):
            # Row structure: 0:Timestamp, 1:UserID, 2:GuestName, ..., 8:EstimatedTime
            if len(row) <= 8: continue
            
            row_name = normalize_text(row[2])
            row_est_time_str = row[8]
            
            # Check Name
            if row_name != target_name:
                continue

            # Check Estimated Time
            # Parse row_est_time_str to datetime
            row_dt = None
            if row_est_time_str:
                for fmt in ("%Y-%m-%dT%H:%M", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M"):
                    try:
                        dt_naive = datetime.strptime(row_est_time_str, fmt)
                        row_dt = pytz.timezone(settings.TZ).localize(dt_naive)
                        break
                    except ValueError:
                        continue
            
            # Compare datetimes (allowing small difference if seconds are lost)
            if target_est_dt and row_dt:
                diff = abs((target_est_dt - row_dt).total_seconds())
                if diff < 60: # Match within 1 minute
                    target_row_index = i + 2 # +2 because rows is 0-indexed from A2
                    break
        
        if target_row_index != -1:
            logger.info(f"Found matching row at index {target_row_index}. Deleting...")
            
            # 2. Delete the row
            # We need the sheetId (integer), not the spreadsheetId (string)
            # First, get the sheetId for "Câu trả lời biểu mẫu 1"
            ss = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            sheet_meta = next((s for s in ss['sheets'] if s['properties']['title'] == sheet_name), None)
            
            if not sheet_meta:
                logger.error(f"Sheet '{sheet_name}' not found.")
                return

            sheet_id_int = sheet_meta['properties']['sheetId']

            request = {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id_int,
                        "dimension": "ROWS",
                        "startIndex": target_row_index - 1, # 0-based inclusive
                        "endIndex": target_row_index # 0-based exclusive
                    }
                }
            }

            service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body={"requests": [request]}
            ).execute()
            logger.info(f"Successfully deleted row {target_row_index} in '{sheet_name}'.")
        else:
            logger.warning(f"Could not find row to delete for guest: {guest_info.get('full_name')}")

    except Exception as e:
        logger.error(f"Error deleting row from sheet: {e}")
