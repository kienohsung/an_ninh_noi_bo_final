

# <a id="04122025-report-module-bugs"></a> 04/12/2025 📊 Report Module Implementation Bugs
**Version:** v1.15.0 | **Tags:** #bugfix, #backend, #frontend, #reports, #sqlalchemy

## 1. Tổng quan (Overview)
* **Mục tiêu:** Khắc phục 3 lỗi critical trong quá trình triển khai module Báo cáo & Phân tích cho admin/manager.
* **Trạng thái:** ✅ Đã sửa (100% - tất cả 4 endpoints hoạt động)

## 2. Vấn đề & Triệu chứng (Problem & Symptoms)

### **Bug #1: Frontend API Import Path Error**
* **Triệu chứng:** Console báo lỗi `Failed to resolve import "boot/axios"` và `Failed to resolve import "src/boot/axios"` trong tất cả 4 components báo cáo.
* **Nguyên nhân gốc rễ (Root Cause):**
    * Import statement `import { api } from 'boot/axios'` không khớp với cấu trúc dự án thực tế.
    * Dự án sử dụng file `api.js` ở thư mục `src/` thay vì boot plugin.

### **Bug #2: Missing date-fns Dependency**
* **Triệu chứng:** Build warning về missing dependency `date-fns` trong `AssetControlDashboard.vue`.
* **Nguyên nhân gốc rễ (Root Cause):**
    * Code sử dụng `import { format } from 'date-fns'` nhưng thư viện chưa được cài đặt.
    * Không muốn thêm dependency không cần thiết cho một chức năng đơn giản.

### **Bug #3: SQLAlchemy Case Function Syntax Error** ⚠️ **CRITICAL**
* **Triệu chứng:** 
    * Tab "Chỉ số An ninh Khách" trả về `500 Internal Server Error`.
    * 3 tabs còn lại hoạt động tốt.
    * Backend logs: `TypeError: Function.__init__() got an unexpected keyword argument 'else_'`
* **Nguyên nhân gốc rễ (Root Cause):**
    * Code sử dụng `func.case((condition, value), else_=default)` - syntax SAI!
    * SQLAlchemy KHÔNG có hàm `func.case()`, phải dùng `case()` trực tiếp từ `sql alchemy`.
    * Đúng cú pháp: `from sqlalchemy import case` → `case((condition, value), else_=default)`

## 3. Giải pháp Kỹ thuật (Technical Solution)

### **Fix Bug #1: API Import Path**
* **Frontend (4 files):**
    * `VisitorSecurityChart.vue`
    * `AssetControlDashboard.vue`
    * `SystemOverviewCards.vue`
    * `UserActivityTable.vue`
* **Thay đổi:**
    ```javascript
    // ❌ SAI:
    import { api } from 'boot/axios'
    
    // ✅ ĐÚNG:
    import api from '../../api'
    ```

### **Fix Bug #2: Date Formatting**
* **Frontend (`AssetControlDashboard.vue`):**
    * **Loại bỏ:** `import { format } from 'date-fns'`
    * **Thay thế:** Native JavaScript date formatting
    ```javascript
    // ❌ SAI:
    format(new Date(date), 'dd/MM/yyyy')
    
    // ✅ ĐÚNG:
    new Date(date).toLocaleDateString('vi-VN')
    ```

### **Fix Bug #3: SQLAlchemy CASE Syntax**
* **Backend (`app/routers/reports.py`):**
    * **Bước 1:** Thêm import
        ```python
        from sqlalchemy import func, desc, case  # Added 'case'
        ```
    * **Bước 2:** Thay thế toàn bộ `func.case()` → `case()`
        ```python
        # ❌ SAI:
        func.sum(func.case((models.Guest.status == 'pending', 1), else_=0))
        
        # ✅ ĐÚNG:
        func.sum(case((models.Guest.status == 'pending', 1), else_=0))
        ```
    * **Áp dụng cho:** 3 queries trong `visitor_security_index` endpoint (monthly_data, status_breakdown, query_status)

## 4. Kết quả & Cập nhật (Impact & Metrics)
* **Files Modified:**
    * Backend: `app/routers/reports.py` (1 file, 8 occurrences)
    * Frontend: 4 components (`VisitorSecurityChart.vue`, `AssetControlDashboard.vue`, `SystemOverviewCards.vue`, `UserActivityTable.vue`)
* **Kết quả:**
    * ✅ Tất cả 4 tabs báo cáo hoạt động hoàn hảo
    * ✅ Charts render chính xác với dữ liệu thực
    * ✅ No console errors
    * ✅ No missing dependencies
    * ✅ Backend queries execute successfully với performance indexes
* **Testing Method:**
    * Tạo script `test_visitor_endpoint.py` để test trực tiếp endpoint
    * Output: `✅ SUCCESS! Result type: <class 'app.schemas.VisitorStatsResponse'>`

## 5. Bài học & Ghi chú (Lessons Learned)
* **SQLAlchemy Syntax:** Luôn kiểm tra documentation khi sử dụng các hàm SQL phức tạp. `func.case()` KHÔNG TỒN TẠI - chỉ có `case()`.
* **Import Paths:** Khi tạo components mới, luôn xem lại pattern import của các components hiện có thay vì đoán.
* **Debugging Approach:** 
    * 3/4 endpoints hoạt động → vấn đề CỤ THỂ ở code endpoint lỗi, KHÔNG phải routing/auth/import chung.
    * Test script trực tiếp tách biệt khỏi HTTP layer giúp phát hiện lỗi nhanh hơn.
* **Error Logging:** Frontend error logging chi tiết (`console.log` with object expansion) giúp debug nhưng BACKEND traceback mới là nguồn chân lý.

---
