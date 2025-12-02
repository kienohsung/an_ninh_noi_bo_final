```
🛑 SYSTEM INSTRUCTION & TEMPLATE
LƯU Ý QUAN TRỌNG CHO AI VÀ DEVELOPER:
Khi đọc file này để phân tích hoặc thêm nhật ký lỗi mới, BẮT BUỘC phải tuân thủ cấu trúc Template dưới đây. Không tự ý thay đổi định dạng heading hoặc cấu trúc mục lục để đảm bảo tính đồng bộ cho toàn bộ dự án.

📋 Template Mẫu (Copy & Paste khi thêm mới)
```markdown
# [DD/MM/YYYY] [Icon] [Tên Lỗi / Vấn Đề Chính]
**Version:** vX.Y.Z | **Tags:** #bugfix, #backend/frontend, #severity

## 1. Tổng quan (Overview)
* **Mục tiêu:** [Mô tả ngắn gọn lỗi và mục tiêu sửa lỗi]
* **Trạng thái:** ✅ Đã sửa / 🚧 Đang xử lý / ❌ Chưa giải quyết

## 2. Vấn đề & Triệu chứng (Problem & Symptoms)
* **Triệu chứng:**
    * [Mô tả hiện tượng lỗi]
* **Nguyên nhân gốc rễ (Root Cause):**
    * [Giải thích kỹ thuật tại sao lỗi xảy ra]

## 3. Giải pháp Kỹ thuật (Technical Solution)
* **Backend (`path/to/file.py`):**
    * [Mô tả thay đổi logic]
* **Frontend (`path/to/file.vue`):**
    * [Mô tả thay đổi UI/UX]
* **Database:** [Thay đổi Schema/Migration nếu có]

## 4. Kết quả & Cập nhật (Impact & Metrics)
* **Files Modified:** `file_A.py`, `file_B.vue`, ...
* **Kết quả:** [Lỗi đã được khắc phục như thế nào?]

## 5. Bài học & Ghi chú (Lessons Learned)
* [Kinh nghiệm rút ra]
```

<!-- BẮT ĐẦU NỘI DUNG BUG LOG TỪ DƯỚI DÒNG NÀY -->

# Mục Lục (Table of Contents)

1.  [03/12/2025 - Google Form Integration Fixes (Timezone & Schema)](#03122025-google-form-integration-fixes)
2.  [02/12/2025 - Timezone Discrepancy in Guard Gate & Telegram](#02122025-timezone-discrepancy)
2.  [02/12/2025 - ReferenceError in RegisterGuest](#02122025-reference-error-register-guest)
3.  [02/12/2025 - Syntax Error & Duplicate Identifier in RegisterGuest](#02122025-syntax-error--duplicate-identifier)
4.  [02/12/2025 - Telegram Bot Conflict & Duplicate Registration](#02122025-telegram-bot-conflict--duplicate-registration)
5.  [01/12/2025 - PDF Export & Print Layout Issues](#01122025-pdf-export--print-layout-issues)
6.  [30/11/2025 - Asset Management Registration Errors](#30112025-asset-management-registration-errors)
7.  [29/11/2025 - White Screen & Token Expiry](#29112025-white-screen--token-expiry)
8.  [28/11/2025 - Task List Loading & Image Upload Failures](#28112025-task-list-loading--image-upload-failures)
9.  [21-23/11/2025 - Database Schema Mismatch](#21-23112025-database-schema-mismatch)

---

# <a id="03122025-google-form-integration-fixes"></a> 03/12/2025 🐛 Google Form Integration Fixes (Timezone & Schema)
**Version:** v1.14.1 | **Tags:** #bugfix, #backend, #timezone, #database

## 1. Tổng quan (Overview)
* **Mục tiêu:** Khắc phục các lỗi phát sinh khi tích hợp Google Form: sai lệch múi giờ dự kiến và lỗi schema database.
* **Trạng thái:** ✅ Đã sửa

## 2. Vấn đề & Triệu chứng (Problem & Symptoms)
* **Triệu chứng 1 (Timezone):** Thời gian "Dự kiến" của khách từ Google Form bị lệch +7 tiếng so với thực tế (do Google Sheet trả về UTC/Local time không khớp).
* **Triệu chứng 2 (Schema):** Lỗi `TypeError: 'source' is an invalid keyword argument` khi tạo Guest.
* **Triệu chứng 3 (Notification):** Khách mới từ Google Form không bắn thông báo lên Telegram.

## 3. Giải pháp Kỹ thuật (Technical Solution)
* **Backend (`services/form_sync_service.py`):**
    * **Timezone Fix:** Áp dụng công thức `Estimated = Timestamp + 1h - 7h` để bù trừ độ lệch múi giờ và cộng thêm buffer time.
    * **Schema Fix:** Loại bỏ trường `source="google_form"` khỏi câu lệnh insert vì Database chưa có cột này.
    * **Notification Fix:** Import và gọi hàm `run_pending_list_notification` + `send_event_to_archive_background` ngay sau khi sync thành công.

## 4. Kết quả & Cập nhật (Impact & Metrics)
* **Files Modified:** `form_sync_service.py`.
* **Kết quả:**
    * Thời gian dự kiến hiển thị chính xác.
    * Không còn lỗi crash khi sync.
    * Telegram nhận thông báo ngay lập tức khi có khách điền form.

## 5. Bài học & Ghi chú (Lessons Learned)
* Khi làm việc với datetime từ nguồn bên ngoài (như Google Sheet), luôn phải kiểm tra kỹ múi giờ (Timezone Aware vs Naive).
* Kiểm tra kỹ Model Definition trước khi thêm trường mới vào code insert.

---

# <a id="02122025-timezone-discrepancy"></a> 02/12/2025 🕒 Timezone Discrepancy in Guard Gate & Telegram
**Version:** v1.13.3 | **Tags:** #bugfix, #frontend, #backend, #timezone

## 1. Tổng quan (Overview)
* **Mục tiêu:** Khắc phục lỗi hiển thị sai giờ (lệch 7 tiếng) tại cột "Giờ vào" trên trang Guard Gate và trong thông báo Telegram.
* **Trạng thái:** ✅ Đã sửa

## 2. Vấn đề & Triệu chứng (Problem & Symptoms)
* **Triệu chứng:**
    * "Giờ vào" trên web hiển thị chính xác theo giờ thực tế.
    * Thông báo Telegram hiển thị đúng giờ dự kiến và giờ sự kiện.

## 5. Bài học & Ghi chú (Lessons Learned)
* Không nên cộng/trừ giờ thủ công (hardcode offset) để xử lý múi giờ. Hãy luôn làm việc với UTC hoặc timezone-aware datetime object và để tầng hiển thị (frontend/formatter) lo việc format theo local time.

---

# <a id="02122025-telegram-bot-conflict--duplicate-registration"></a> 02/12/2025 🤖 Telegram Bot Conflict & Duplicate Registration
**Version:** v1.13.1 | **Tags:** #bugfix, #telegram, #backend, #concurrency

## 1. Tổng quan (Overview)
* **Mục tiêu:** Khắc phục lỗi Bot Telegram không khởi động được (409 Conflict) và lỗi xử lý trùng lặp tin nhắn đăng ký.
* **Trạng thái:** ✅ Đã sửa

## 2. Vấn đề & Triệu chứng (Problem & Symptoms)
* **Triệu chứng:**
    * Log báo lỗi `409 Conflict: Terminated by other getUpdates request`.
    * Một tin nhắn đăng ký từ người dùng tạo ra 2 bản ghi khách giống hệt nhau trong Database.
    * Bot không tự động restart khi crash trên môi trường Production.
* **Nguyên nhân gốc rễ (Root Cause):**
    * **409 Conflict:** Có nhiều process Python cùng chạy code Bot (do các terminal cũ chưa tắt hẳn).
    * **Duplicate Registration:** Process "ma" (zombie process) chạy ngầm vẫn nhận và xử lý tin nhắn song song với process chính.
    * **No Auto-restart:** Script `.bat` sử dụng vòng lặp giới hạn `(1,1,1)` thay vì vô hạn.

## 3. Giải pháp Kỹ thuật (Technical Solution)
* **Backend (`services/telegram_bot.py`):**
    * **Deduplication (Memory):** Thêm `processed_ids` (deque) để cache 100 message ID gần nhất, bỏ qua nếu đã xử lý.
    * **Deduplication (Database):** Query kiểm tra trong vòng 1 phút trước đó có bản ghi nào trùng `full_name`, `id_card`, `registered_by` không.
    * **Logging:** Thêm PID vào log khởi động để dễ dàng phát hiện process thừa.
* **System (`start_all_services_5173Port.bat`):**
    * Sửa vòng lặp từ `(1,1,1)` thành `(1,0,1)` để enable auto-restart vô hạn.
    * Kill toàn bộ process python thừa bằng `taskkill`.

## 4. Kết quả & Cập nhật (Impact & Metrics)
* **Files Modified:** `services/telegram_bot.py`, `start_all_services_5173Port.bat`.
* **Kết quả:**
    * Bot khởi động ổn định, không còn lỗi 409.
    * Hệ thống tự động chặn các đăng ký trùng lặp (cả từ spam tin nhắn hoặc lỗi process).
    * Service tự động hồi phục sau 5s nếu bị crash.

## 5. Bài học & Ghi chú (Lessons Learned)
* Luôn kiểm tra process ẩn (Zombie processes) khi gặp lỗi xử lý lặp lại (double processing).
* Với Polling Bot, cơ chế deduplication ở cả tầng Memory và Database là bắt buộc để đảm bảo tính toàn vẹn dữ liệu.

---

# <a id="01122025-pdf-export--print-layout-issues"></a> 01/12/2025 🖨️ PDF Export & Print Layout Issues
**Version:** v1.12.0 | **Tags:** #bugfix, #frontend, #css, #pdf

## 1. Tổng quan (Overview)
* **Mục tiêu:** Sửa lỗi giao diện khi in ấn phiếu tài sản và lỗi mất state khi reload trang.
* **Trạng thái:** ✅ Đã sửa

## 2. Vấn đề & Triệu chứng (Problem & Symptoms)
* **Triệu chứng:**
    * `window.print()` làm vỡ layout, không fit giấy A4, lề không đều.
    * Nền vàng của ứng dụng vẫn hiển thị khi in.
---

# <a id="30112025-asset-management-registration-errors"></a> 30/11/2025 🛠️ Asset Management Registration Errors
**Version:** v1.11.1 | **Tags:** #bugfix, #backend, #cors, #database

## 1. Tổng quan (Overview)
* **Mục tiêu:** Khắc phục lỗi không đăng ký được tài sản (CORS, 500 Error) và lỗi giao diện Vue.
* **Trạng thái:** ✅ Đã sửa

## 2. Vấn đề & Triệu chứng (Problem & Symptoms)
* **Triệu chứng:**
    * Frontend báo lỗi CORS khi gọi API từ port 5173.
    * Backend trả về 500 Internal Server Error khi submit form.
    * Build lỗi "Element is missing end tag".
* **Nguyên nhân gốc rễ (Root Cause):**
    * **CORS:** Cấu hình `allow_origins=["*"]` xung đột với `allow_credentials=True`.
    * **Database:** Bảng `asset_log` thiếu cột `estimated_datetime` so với model Pydantic.
    * **Vue:** Lỗi cú pháp HTML thiếu thẻ đóng trong `AssetManagementPage.vue`.

## 3. Giải pháp Kỹ thuật (Technical Solution)
* **Backend (`main.py`):** Cấu hình lại CORS, chỉ định rõ origin (localhost, IP LAN).
* **Database:** Chạy migration script thêm cột `estimated_datetime`.
* **Frontend:** Sửa lỗi cú pháp HTML trong file Vue.

## 4. Kết quả & Cập nhật (Impact & Metrics)
* **Files Modified:** `main.py`, `AssetManagementPage.vue`.
* **Kết quả:** Đăng ký tài sản thành công, không còn lỗi mạng hay lỗi server.

---

# <a id="29112025-white-screen--token-expiry"></a> 29/11/2025 ⚪ White Screen & Token Expiry
**Version:** v1.11.0 | **Tags:** #bugfix, #frontend, #auth

## 1. Tổng quan (Overview)
* **Mục tiêu:** Sửa lỗi màn hình trắng chết chóc khi token hết hạn.
* **Trạng thái:** ✅ Đã sửa

## 2. Vấn đề & Triệu chứng (Problem & Symptoms)
* **Triệu chứng:** Người dùng truy cập ứng dụng chỉ thấy màn hình trắng, phải dùng Tab ẩn danh mới vào được.
* **Nguyên nhân gốc rễ (Root Cause):**
    * Token trong `localStorage` bị lỗi hoặc hết hạn nhưng code không handle đúng.
    * `JSON.parse` token rác gây crash ứng dụng ngay khi khởi động.

## 3. Giải pháp Kỹ thuật (Technical Solution)
* **Frontend (`stores/auth.js`):**
    * Thêm `try-catch` khi parse token.
    * Validate token string ngay khi khởi tạo state.
    * Tự động `logout()` và `localStorage.clear()` nếu phát hiện token lỗi.

## 4. Kết quả & Cập nhật (Impact & Metrics)
* **Files Modified:** `stores/auth.js`.
* **Kết quả:** Ứng dụng tự động đá người dùng về trang Login thay vì treo màn hình trắng.

## 5. Bài học & Ghi chú (Lessons Learned)
* Kiểm tra kỹ scope của biến khi refactor code.

---

# <a id="28112025-task-list-loading--image-upload-failures"></a> 28/11/2025 📉 Task List Loading & Image Upload Failures
**Version:** v1.10.1 | **Tags:** #bugfix, #frontend, #backend

## 1. Tổng quan (Overview)
* **Mục tiêu:** Sửa lỗi Task List trên dashboard bị trống và lỗi upload ảnh thiết bị.
* **Trạng thái:** ✅ Đã sửa

## 2. Vấn đề & Triệu chứng (Problem & Symptoms)
* **Triệu chứng:**
    * Task list dashboard không hiển thị dữ liệu.
    * Ảnh thiết bị không upload được lên Google Sheets.
    * Note của thiết bị bị nhân đôi (duplicate) khi edit.
* **Nguyên nhân gốc rễ (Root Cause):**
    * **Task List:** Bug trong logic data fetching và xử lý token không chặt chẽ.
    * **Image Upload:** Frontend không chuyển đổi đúng ảnh sang base64.
    * **Duplicate Note:** Logic prepend note không kiểm tra nội dung cũ đã tồn tại chưa.

## 3. Giải pháp Kỹ thuật (Technical Solution)
* **Frontend:**

## 1. Tổng quan (Overview)
* **Mục tiêu:** Đồng bộ Database Schema với Application Models sau khi thay thế file DB.
* **Trạng thái:** ✅ Đã sửa

## 2. Vấn đề & Triệu chứng (Problem & Symptoms)
* **Triệu chứng:** `sqlite3.IntegrityError: NOT NULL constraint failed` và lỗi 500 khi login.
* **Nguyên nhân gốc rễ (Root Cause):**
    * File DB mới thiếu bảng `asset_images`.
    * Thiếu các cột: `asset_description`, `employee_code`, `department`, `registered_by_user_id`.

## 3. Giải pháp Kỹ thuật (Technical Solution)
* **Database:**
    * Viết script migration kiểm tra từng cột.
    * Sử dụng `ALTER TABLE` để thêm các cột thiếu.
    * Sync lại định nghĩa Model SQLAlchemy.

## 4. Kết quả & Cập nhật (Impact & Metrics)
* **Files Modified:** `models.py`, `migrate.py`.
* **Kết quả:** Database schema đã khớp hoàn toàn với code, không còn lỗi Integrity.

---

# <a id="02122025-syntax-error--duplicate-identifier"></a> 02/12/2025 🐛 Syntax Error & Duplicate Identifier in RegisterGuest
**Version:** v1.13.2 | **Tags:** #bugfix, #frontend, #vue, #syntax-error

## 1. Tổng quan (Overview)
* **Mục tiêu:** Khắc phục lỗi cú pháp (thiếu khai báo hàm) và lỗi trùng lặp định danh (duplicate identifier) trong `RegisterGuest.vue` gây crash ứng dụng frontend.
* **Trạng thái:** ✅ Đã sửa

## 2. Vấn đề & Triệu chứng (Problem & Symptoms)
* **Triệu chứng:**
    * Màn hình console báo lỗi `[vue/compiler-sfc] Unexpected token` tại dòng 396.
    * Lỗi `Identifier 'filterSuppliers' has already been declared` khi chạy `npm run dev`.
    * Ứng dụng không load được trang `register-guest`.
* **Nguyên nhân gốc rễ (Root Cause):**
    * **Syntax Error:** Hàm `openSearchDialog` bị mất dòng khai báo `function openSearchDialog(...) {` trong quá trình refactor/merge code, dẫn đến cấu trúc code bị gãy.
    * **Duplicate Identifier:** Hàm `filterSuppliers` được khai báo 2 lần trong cùng một file (do copy-paste hoặc merge lỗi).

## 3. Giải pháp Kỹ thuật (Technical Solution)
* Luôn kiểm tra console log ngay sau khi sửa code để phát hiện sớm các lỗi cú pháp.

---

# <a id="02122025-reference-error-register-guest"></a> 02/12/2025 🐛 ReferenceError in RegisterGuest
**Version:** v1.13.4 | **Tags:** #bugfix, #frontend, #javascript

## 1. Tổng quan (Overview)
* **Mục tiêu:** Khắc phục lỗi `ReferenceError: d is not defined` khi chọn ngày giờ dự kiến đăng ký khách.
* **Trạng thái:** ✅ Đã sửa

## 2. Vấn đề & Triệu chứng (Problem & Symptoms)
* **Triệu chứng:**
    * Nhấn nút "OK" trong popup chọn ngày giờ không có phản hồi.
    * Console báo lỗi `Uncaught ReferenceError: d is not defined` tại `setEstimatedDatetime`.
* **Nguyên nhân gốc rễ (Root Cause):
    * Biến `d` được sử dụng để gọi `.toISOString()` nhưng chưa được khai báo trong scope của hàm `setEstimatedDatetime`.

## 3. Giải pháp Kỹ thuật (Technical Solution)
* **Frontend (`RegisterGuest.vue`):**
    * Khởi tạo đối tượng `Date` từ chuỗi ngày giờ đã chọn trước khi convert sang ISO string.
    * Code: `const d = new Date(newVal);`

## 4. Kết quả & Cập nhật (Impact & Metrics)
* **Files Modified:** `RegisterGuest.vue`.
* **Kết quả:** Chức năng chọn ngày giờ và đăng ký khách hoạt động bình thường.

## 5. Bài học & Ghi chú (Lessons Learned)
* Kiểm tra kỹ scope của biến khi refactor code.
```