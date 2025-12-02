🛑 SYSTEM INSTRUCTION & TEMPLATE
LƯU Ý QUAN TRỌNG CHO AI VÀ DEVELOPER:
Khi đọc file này để phân tích hoặc thêm nhật ký mới, BẮT BUỘC phải tuân thủ cấu trúc Template dưới đây. Không tự ý thay đổi định dạng heading hoặc cấu trúc mục lục để đảm bảo tính đồng bộ cho toàn bộ dự án.

📋 Template Mẫu (Copy & Paste khi thêm mới)
```markdown
# [DD/MM/YYYY] [Icon] [Tên Tính Năng / Công Việc Chính]
**Version:** vX.Y.Z | **Tags:** #tag1, #tag2

## 1. Tổng quan (Overview)
* **Mục tiêu:** [Mô tả ngắn gọn 1-2 dòng mục đích]
* **Trạng thái:** ✅ Hoàn thành / 🚧 Đang thực hiện / 🐛 Bug Fix

## 2. Vấn đề & Yêu cầu (Problem & Requirements)
* **Bối cảnh:** [Tại sao cần làm? Lỗi là gì?]
* **Yêu cầu cụ thể:**
    * [Gạch đầu dòng 1]
    * [Gạch đầu dòng 2]

## 3. Giải pháp Kỹ thuật (Technical Solution)
* **Kiến trúc/Logic:** [Mô tả luồng dữ liệu hoặc thuật toán chính]
* **Backend (`path/to/file.py`):**
    * [Mô tả thay đổi logic, hàm mới]
* **Frontend (`path/to/file.vue`):**
    * [Mô tả thay đổi UI/UX, logic JS]
* **Database:** [Thay đổi Schema/Migration nếu có]

## 4. Kết quả & Cập nhật (Impact & Metrics)
* **Files Modified:** `file_A.py`, `file_B.vue`, ...
* **Tính năng mới:** [Người dùng nhận được gì?]
* **Sửa lỗi:** [Bug nào đã được fix?]

## 5. Bài học & Ghi chú (Lessons Learned)
* [Kinh nghiệm rút ra hoặc lưu ý kỹ thuật cho maintenance]
```

<!-- BẮT ĐẦU NỘI DUNG NHẬT KÝ DỰ ÁN TỪ DƯỚI DÒNG NÀY -->

# Mục Lục (Table of Contents)

1.  [03/12/2025 - Google Form Integration & Telegram Polling Removal](#03122025-google-form-integration--telegram-polling-removal)
2.  [02/12/2025 - Auto Login & Force Home Redirect](#02122025-auto-login--force-home-redirect)
2.  [01/12/2025 - Asset Management: PDF Export & Smart Navigation](#01122025-asset-management-pdf-export--smart-navigation)
3.  [30/11/2025 - Asset Management Fixes & Refactor](#30112025-asset-management-fixes--refactor)
4.  [29/11/2025 - Refactoring Code & Security Optimization](#29112025-refactoring-code--security-optimization)
5.  [23/10/2025 - Telegram Real-time Notification](#23102025-telegram-real-time-notification)
6.  [22/10/2025 - Telegram History Archiving](#22102025-telegram-history-archiving)
7.  [21/10/2025 - License Plate Standardization](#21102025-license-plate-standardization)
8.  [16/10/2025 - Long-term Guest Registration](#16102025-long-term-guest-registration)
9.  [14/10/2025 - ID Card Scanning (AI Microservice)](#14102025-id-card-scanning-ai-microservice)
10. [12/10/2025 - Authentication Architecture: Refresh Token](#12102025-authentication-architecture-refresh-token)
11. [10/10/2025 - UI/UX: Audio Alert & Search](#10102025-uiux-audio-alert--search)
12. [09/10/2025 - Google Sheet Module](#09102025-google-sheet-module)
13. [08/10/2025 - Image Upload & Database Migration](#08102025-image-upload--database-migration)

---

# <a id="03122025-google-form-integration--telegram-polling-removal"></a> 03/12/2025 📝 Google Form Integration & Telegram Polling Removal
**Version:** v1.14.0 | **Tags:** #googleform, #telegram, #backend, #integration

## 1. Tổng quan (Overview)
* **Mục tiêu:** Thay thế tính năng đăng ký khách qua Telegram Bot bằng Google Form để ổn định hơn, đồng thời tối ưu hóa hệ thống bằng cách loại bỏ cơ chế Polling.
* **Trạng thái:** ✅ Hoàn thành

## 2. Vấn đề & Yêu cầu (Problem & Requirements)
* **Bối cảnh:**
    * Telegram Bot Polling đôi khi không ổn định hoặc bị trùng lặp xử lý.
    * Việc nhập liệu qua chat bot khó kiểm soát format hơn so với Form.
* **Yêu cầu cụ thể:**
    * Vô hiệu hóa Polling nhưng giữ lại tính năng gửi thông báo.
    * Đồng bộ dữ liệu từ Google Form (Sheet) về DB theo thời gian thực.
    * Tự động tính toán thời gian dự kiến và validate dữ liệu chặt chẽ.

## 3. Giải pháp Kỹ thuật (Technical Solution)
* **3.1. Google Form Sync (`backend/app/services/form_sync_service.py`):**
    * **Batch Processing:** Đọc toàn bộ Sheet, lọc các dòng chưa sync, xử lý và update lại trạng thái theo lô (Batch Update) để tiết kiệm quota API.
    * **Validation:** Kiểm tra `userID` (Mã nhân viên) tồn tại và active. Chặn trùng lặp dựa trên CCCD trong ngày.
    * **Time Logic:** `Estimated Time = Timestamp + 1h - 7h` (Fix lệch múi giờ Google Sheet).
* **3.2. Telegram Optimization:**
    * **Backend (`main.py`):** Loại bỏ `telegram_bot_service.start()` (Polling).
    * **Notification:** Tích hợp gửi thông báo vào `form_sync_service.py` ngay sau khi sync thành công.
* **3.3. Scheduler:**
    * Job `sync_google_form_job` chạy mỗi 30s (đã test ổn định ở 5s).

## 4. Kết quả & Cập nhật (Impact & Metrics)
* **Files Modified:** `main.py`, `gsheets_reader.py`, `form_sync_service.py` (New).
* **Tính năng mới:**
    * Khách đăng ký qua Google Form sẽ tự động vào danh sách chờ sau ~30s.
    * Thông báo Telegram vẫn hoạt động bình thường cho bảo vệ/lễ tân.
* **Hiệu năng:** Giảm tải cho server vì không phải duy trì kết nối Polling liên tục.

## 5. Bài học & Ghi chú (Lessons Learned)
* **Google Sheet API:** Cần chú ý `valueRenderOption='FORMATTED_VALUE'` để lấy ngày tháng chuẩn.
* **Timezone:** Google Form Timestamp thường là UTC hoặc múi giờ của Sheet, cần trừ/cộng phù hợp để ra giờ Local chính xác.

---

# <a id="02122025-auto-login--force-home-redirect"></a> 02/12/2025 🔐 Auto Login & Force Home Redirect
**Version:** v1.13.0 | **Tags:** #auth, #frontend, #ux, #router

## 1. Tổng quan (Overview)
* **Mục tiêu:** Cải thiện trải nghiệm đăng nhập (tự động đăng nhập lại sau khi clear cache) và điều hướng người dùng về trang chủ khi truy cập lần đầu.
* **Trạng thái:** ✅ Hoàn thành

## 2. Vấn đề & Yêu cầu (Problem & Requirements)
* **Bối cảnh:**
    * Trang Login tự động clear cache để tránh lỗi màn hình trắng, nhưng vô tình xóa luôn token xác thực, bắt người dùng đăng nhập lại.
    * Người dùng truy cập trực tiếp link con (deep linking) đôi khi gặp lỗi hoặc giao diện chưa load đủ context.
* **Yêu cầu cụ thể:**
    * Giữ lại phiên đăng nhập sau khi clear cache.
    * Nếu user truy cập link bất kỳ (VD: `/guard-gate`), tự động chuyển về Dashboard/Home trước.

## 3. Giải pháp Kỹ thuật (Technical Solution)
* **Kiến trúc/Logic:**
    * **Auto Login:** Tại `LoginPage`, khi clear cache, giữ lại `token` và `refreshToken`. Sau đó gọi `auth.bootstrap()` để kiểm tra. Nếu hợp lệ -> redirect về Home.
    * **Force Home:** Tại `router/index.js`, thêm Global Guard. Nếu là lần load đầu tiên (`from.matched.length === 0`) và không phải trang Login/Home -> Redirect về `/`.
* **Frontend (`src/pages/LoginPage.vue`):**
    * Sửa logic `localStorage.clear()` để backup và restore token.
    * Thêm logic check `auth.isAuthenticated` ngay sau khi mount.
* **Frontend (`src/router/index.js`):**
    * Thêm logic `if (from.matched.length === 0 ...)` trong `router.beforeEach`.

## 4. Kết quả & Cập nhật (Impact & Metrics)
* **Files Modified:** `LoginPage.vue`, `router/index.js`.
* **Tính năng mới:**
    * Không cần đăng nhập lại mỗi khi F5 hoặc mở lại tab (nếu token còn hạn).
    * Luôn bắt đầu từ Dashboard để đảm bảo quy trình làm việc chuẩn.

---

# <a id="01122025-asset-management-pdf-export--smart-navigation"></a> 01/12/2025 🎨 Nâng cấp Asset Management: PDF Export & Smart Navigation
**Version:** v1.12.0 | **Tags:** #assets, #pdf, #frontend, #ux

## 1. Tổng quan (Overview)
* **Mục tiêu:** Thay thế tính năng in ấn mặc định của trình duyệt bằng xuất PDF client-side chuyên nghiệp và cải thiện luồng điều hướng người dùng.
* **Trạng thái:** ✅ Hoàn thành

## 2. Vấn đề & Yêu cầu (Problem & Requirements)
* **Vấn đề Browser Print:**
    * CSS `@media print` không kiểm soát layout chính xác, form không fit trang A4.
    * Nền vàng (`bg-yellow-2`) vẫn hiển thị, margin không đồng bộ.
* **Vấn đề Navigation:**
    * User phải tự chuyển trang để in sau khi đăng ký.
    * Print dialog không tự mở, query params bị mất dẫn đến đóng dialog.
* **Vấn đề Cache:** Login page bị trắng màn hình do cache cũ.

## 3. Giải pháp Kỹ thuật (Technical Solution)
* **3.1. PDF Export Implementation:**
    * Công nghệ: `jspdf`, `html2canvas`
    * **Frontend (`AssetManagementPage.vue`):**
        * DOM Manipulation tạm thời (xóa class màu nền).
        * Scale font lên 125% để rõ nét.
        * Capture bằng html2canvas (scale 2x).
        * Tạo PDF A4 với jspdf và margin 5mm.
        * Restore lại DOM ban đầu.
* **3.2. Smart Navigation Flow:**
    * **Frontend (`RegisterAssetPage.vue`):** Lưu `lastCreatedAssetId`. Redirect sang `/asset-management` với query param `?printId=...`.
    * **Frontend (`AssetManagementPage.vue`):** `onMounted` check `route.query.printId`. Nếu có ID, tự động fetch data và mở dialog in.
* **3.3. Cache Management:**
    * **Frontend (`LoginPage.vue` & `index.html`):** Thêm Meta tags No-Cache. Programmatic Clearing: Xóa localStorage (trừ auth token), sessionStorage, và unregister Service Workers khi mount trang Login.

## 4. Kết quả & Cập nhật (Impact & Metrics)
* **Files Modified:** `AssetManagementPage.vue` (+60 lines), `RegisterAssetPage.vue`, `AssetFormPaper.vue`, `LoginPage.vue`.
* **Tính năng mới:**
    * Xuất PDF chuẩn A4, đẹp, không dính background màu.
    * Luồng: Đăng ký -> Tự chuyển trang -> Tự mở dialog in.
    * Giao diện: Print Dialog thu gọn 50% width, thêm FAB buttons (Print/Close).

## 5. Bài học & Ghi chú (Lessons Learned)
* `@media print` không đủ mạnh cho các layout phức tạp, nên dùng PDF generation.
* Cần cẩn thận với vòng đời của Vue Router Query Params để tránh component bị unmount sai thời điểm.

---

# <a id="30112025-asset-management-fixes--refactor"></a> 30/11/2025 🛠️ Asset Management Fixes & Refactor
**Version:** v1.11.1 | **Tags:** #assets, #bugfix, #permissions, #backend

## 1. Tổng quan (Overview)
* **Mục tiêu:** Hoàn thiện phân quyền Admin/Staff và xử lý các lỗi nghiêm trọng (CORS, Schema).
* **Trạng thái:** ✅ Hoàn thành

## 2. Vấn đề & Yêu cầu (Problem & Requirements)
* **Phân quyền:** Admin cần toàn quyền sửa/xóa tài sản. Staff chỉ được sửa khi status là 'pending'.
* **Lỗi CORS:** Chặn request từ frontend local.
* **Lỗi 500:** DB thiếu cột `estimated_datetime` trong bảng log.

## 3. Giải pháp Kỹ thuật (Technical Solution)
* **3.1. Phân quyền (Permissions):**
    * **Backend (`routers/assets.py`):** Bypass check status trong `update_asset` và `delete_asset` nếu role là admin.
    * **Frontend (`AssetManagementPage.vue`):** Disable nút Edit/Delete cho staff nếu tài sản đã ra cổng. Ẩn menu "Quản lý tài sản" với role staff.
* **3.2. Bug Fixes:**
    * **CORS (`main.py`):** Cấu hình lại `allow_origins` cụ thể (localhost, IP LAN) thay vì `*` khi dùng `allow_credentials=True`.
    * **Database:** Thêm migration script `add_estimated_datetime_column.py` để vá schema thiếu.

## 4. Kết quả & Cập nhật (Impact & Metrics)
* **Files Modified:** `main.py`, `routers/assets.py`, `RegisterGuest.vue`.
* **Kết quả:** Hệ thống chạy ổn định trên môi trường LAN, phân quyền chặt chẽ.

---

# <a id="29112025-refactoring-code--security-optimization"></a> 29/11/2025 🔧 Refactoring Code & Security Optimization
**Version:** v1.11.0 | **Tags:** #refactor, #security, #frontend, #backend

## 1. Tổng quan (Overview)
* **Mục tiêu:** Refactor code frontend (Upload ảnh), tăng cường bảo mật (xóa password cứng) và thêm tính năng xóa dữ liệu cũ.
* **Trạng thái:** ✅ Hoàn thành

## 2. Vấn đề & Yêu cầu (Problem & Requirements)
* **Code duplicate:** Nhiều đoạn mã lặp lại trong xử lý upload ảnh.
* **Hardcoded password:** Mật khẩu admin (`Kienhp@@123`) nằm cứng ở frontend -> Rủi ro bảo mật.
* **Tính năng thiếu:** Cần tính năng xóa khách cũ (pending quá hạn).

## 3. Giải pháp Kỹ thuật (Technical Solution)
* **3.1. Code Refactoring (Frontend):**
    * Tạo Utilities: `frontend/src/utils/imageUpload.js` (Tách logic resize, upload) và `frontend/src/utils/validators.js` (Tách logic validate).
    * Kết quả: Giảm `RegisterGuest.vue` từ 1221 xuống 1105 dòng (-10%).
* **3.2. Security Enhancement:**
    * **Backend (`routers/admin.py`):** Tạo endpoint `POST /admin/validate-delete-password`. Password lấy từ ENV `ADMIN_DELETE_PASSWORD`.
    * **Frontend:** Gọi API để validate password thay vì check cứng tại client.
* **3.3. Xóa dữ liệu cũ:**
    * **Backend (`routers/guests.py`):** Endpoint `POST /guests/delete-old`: Tìm khách pending quá hạn -> Archive ảnh -> Xóa record.

## 4. Kết quả & Cập nhật (Impact & Metrics)
* **Code Quality:** Clean, DRY (Don't Repeat Yourself), Modular.
* **Security:** Không còn hardcoded secret ở frontend.

---

# <a id="23102025-telegram-real-time-notification"></a> 23/10/2025 🛰️ Tính năng: Thông báo Telegram Real-time
**Version:** v1.10.0 | **Tags:** #telegram, #notification, #backend
**Liên quan:** [22/10/2025 - Telegram History Archiving](#22102025-telegram-history-archiving)

## 1. Tổng quan (Overview)
* **Mục tiêu:** Xây dựng hệ thống thông báo 2 kênh: Kênh Chính (Dashboard thời gian thực) và Kênh Lưu trữ (Log lịch sử).
* **Trạng thái:** ✅ Hoàn thành

## 2. Kiến trúc Hệ thống (Architecture)
* **Kênh Chính (Main Channel):** Chỉ giữ 1 tin nhắn duy nhất (Snapshot hiện tại của danh sách chờ). Cơ chế: Xóa tin cũ -> Gửi tin mới.
* **Kênh Lưu trữ (Archive Channel):** Ghi log mọi sự kiện (Đăng ký mới, Vào cổng). Cơ chế: Append only.

## 3. Giải pháp Kỹ thuật (Technical Solution)
* **Core Module (`backend/app/utils/notifications.py`):**
    * `run_pending_list_notification()`: Quản lý logic xóa/gửi lại tin nhắn kênh chính.
    * `send_event_to_archive_background()`: Gửi log sang kênh lưu trữ.
    * Sử dụng `telegram_last_message_id.txt` để tracking ID tin nhắn cần xóa.
* **Integration (BackgroundTasks):** Tích hợp vào `routers/guests.py` và `routers/guests_confirm.py` sử dụng FastAPI BackgroundTasks để không chặn main thread.

## 4. Kết quả & Cập nhật (Impact & Metrics)
* **Trải nghiệm:** Bảo vệ/Lễ tân có dashboard theo dõi ngay trên Telegram mà không bị spam thông báo. Quản lý có thể tra cứu lịch sử đầy đủ.

---

# <a id="22102025-telegram-history-archiving"></a> 22/10/2025 📜 Tính năng: Lưu trữ Lịch sử Telegram (Forwarding)
**Version:** v1.9.0 | **Tags:** #telegram, #notification, #backend
**Liên quan:** [23/10/2025 - Telegram Real-time Notification](#23102025-telegram-real-time-notification)

## 1. Tổng quan (Overview)
* **Mục tiêu:** Cải tiến logic thông báo Kênh Chính: Thay vì xóa tin nhắn cũ ngay, hãy Forward nó sang kênh lưu trữ trước khi xóa.
* **Trạng thái:** ✅ Hoàn thành

## 2. Giải pháp Kỹ thuật (Technical Solution)
* **Logic (`utils/notifications.py`):**
    1. Đọc `last_message_id`.
    2. Forward tin nhắn đó sang `TELEGRAM_ARCHIVE_CHAT_ID`.
    3. Delete tin nhắn đó ở `TELEGRAM_CHAT_ID`.
    4. Send tin nhắn mới (danh sách mới) vào `TELEGRAM_CHAT_ID`.
* **Cấu hình:** Thêm ENV `TELEGRAM_ARCHIVE_CHAT_ID`.

## 3. Bài học & Ghi chú (Lessons Learned)
* Bot cần quyền **Can delete messages** ở kênh chính và **Can post messages** ở kênh lưu trữ.

---

# <a id="21102025-license-plate-standardization"></a> 21/10/2025 📝 Chuẩn hóa Biển số xe
**Version:** v1.8.0 | **Tags:** #data, #normalization, #backend

## 1. Tổng quan (Overview)
* **Mục tiêu:** Đảm bảo nhất quán dữ liệu biển số (Format: `*-XXX.XX`).
* **Trạng thái:** ✅ Hoàn thành

## 2. Giải pháp Kỹ thuật (Technical Solution)
* **Batch Processing (Dữ liệu cũ):**
    * Script: `tools/standardize_plates.py`.
    * Logic: Quét toàn bộ DB, format lại regex, update ngược lại DB.
* **Real-time Processing (Dữ liệu mới):**
    * Module: `backend/app/utils/plate_formatter.py`.
    * Hook: Gọi hàm `format_license_plate()` tại các endpoints `create_guest`, `update_guest`, `import_guests`.

---

# <a id="16102025-long-term-guest-registration"></a> 16/10/2025 🔄 Tính năng: Đăng ký Khách Dài hạn (Scheduler)
**Version:** v1.7.0 | **Tags:** #scheduler, #backend, #automation

## 1. Tổng quan (Overview)
* **Mục tiêu:** Tự động tạo phiếu đăng ký hàng ngày cho khách thường xuyên (nhà thầu, chuyên gia).
* **Trạng thái:** ✅ Hoàn thành

## 2. Giải pháp Kỹ thuật (Technical Solution)
* **Database:** Bảng mới `LongTermGuest`.
* **Automation (Backend):**
    * Sử dụng `apscheduler` trong `main.py`.
    * Job: `create_daily_guest_entries` chạy mỗi 30 phút.
    * Logic: Query `LongTermGuest` đang active và trong hạn. Check xem hôm nay đã có bản ghi trong bảng `Guest` chưa. Nếu chưa -> Clone thông tin -> Tạo bản ghi `Guest` mới (status pending).
* **Cơ chế tự phục hồi:** Chạy mỗi 30p đảm bảo nếu server restart lúc 8h sáng thì 8h30 vẫn sẽ chạy lại, không bị miss.

---

# <a id="14102025-id-card-scanning-ai-microservice"></a> 14/10/2025 🤖 Tính năng: Quét CCCD (Microservices AI)
**Version:** v1.6.0 | **Tags:** #ai, #microservice, #gemini, #python

## 1. Tổng quan (Overview)
* **Mục tiêu:** Auto-fill thông tin khách từ ảnh chụp CCCD sử dụng Google Gemini.
* **Kiến trúc:** Microservice tách biệt.

## 2. Giải pháp Kỹ thuật (Technical Solution)
* **Kiến trúc:** Frontend -> Backend Gateway -> ID Card Extractor Service (Python/FastAPI riêng).
* **Microservice (`id_card_extractor_service`):**
    * Sử dụng Google Gemini API.
    * **Fix quan trọng:** Đồng bộ SDK Python (`google-generativeai`) sử dụng model `gemini-2.5-flash` và chế độ `response_mime_type="application/json"` để khớp với module TypeScript cũ.
* **Backend Gateway:** Proxy request file sang Microservice.

## 3. Bài học & Ghi chú (Lessons Learned)
* Sự khác biệt giữa các SDK (JS vs Python) và version model Gemini là nguyên nhân gây lỗi 404. Phải đồng bộ chính xác tên model.

---

# <a id="12102025-authentication-architecture-refresh-token"></a> 12/10/2025 🔐 Kiến trúc Xác thực: Refresh Token
**Version:** v1.5.0 | **Tags:** #auth, #security, #frontend, #backend

## 1. Tổng quan (Overview)
* **Mục tiêu:** Giữ phiên đăng nhập người dùng liên tục mà vẫn bảo mật, tránh lỗi 401 khó chịu.
* **Trạng thái:** ✅ Hoàn thành

## 2. Giải pháp Kỹ thuật (Technical Solution)
* **Backend:**
    * Phát hành cặp `access_token` (15p) và `refresh_token` (7 ngày).
    * Endpoint `/token/refresh`: Đổi refresh token lấy cặp token mới (Token Rotation).
* **Frontend (`api.js`):**
    * Axios Interceptor: Chặn lỗi 401 -> Gọi refresh token -> Retry request ban đầu.
    * Tự động logout nếu refresh token cũng hết hạn.

---

# <a id="10102025-uiux-audio-alert--search"></a> 10/10/2025 🔔 UI UX: Âm báo & Tìm kiếm
**Version:** v1.4.0 | **Tags:** #ui, #ux, #frontend, #database

## 1. Tổng quan (Overview)
* **Mục tiêu:** Cảnh báo âm thanh khi có khách mới và cải thiện bộ lọc tìm kiếm.
* **Trạng thái:** ✅ Hoàn thành

## 2. Giải pháp Kỹ thuật (Technical Solution)
* **Âm báo (`GuardGate.vue`):**
    * Dùng `setInterval` polling mỗi 5s.
    * So sánh `currentCount > previousCount` -> Play Audio.
    * Lưu setting bật/tắt vào `localStorage`.
* **Tìm kiếm Tiếng Việt (`database.py`):**
    * Tạo Custom SQLite Function `unaccent` bằng Python `unicodedata`.
    * Logic tìm kiếm: `func.unaccent(col).ilike(unaccent(query))`.

---

# <a id="09102025-google-sheet-module"></a> 09/10/2025 📊 Module Google Sheet
**Version:** v1.3.0 | **Tags:** #googlesheet, #data, #frontend, #backend

## 1. Tổng quan (Overview)
* **Mục tiêu:** Đọc dữ liệu từ Google Sheet, hiển thị biểu đồ thống kê.
* **Trạng thái:** ✅ Hoàn thành

## 2. Giải pháp Kỹ thuật (Technical Solution)
* **Backend:** Sử dụng `google-api-python-client` và `pandas` để fetch và xử lý dữ liệu.
* **Frontend:** Hiển thị biểu đồ thống kê dữ liệu xe ra vào từ Sheet.
* **Fix lỗi (10/10):** Xử lý lỗi "Duplicate keys" trên bảng Vue bằng cách tạo `__uniqueId` (index + data) làm row-key thay vì dùng Số xe.

---

# <a id="08102025-image-upload--database-migration"></a> 08/10/2025 📸 Tính năng: Upload Hình ảnh & Database Migration
**Version:** v1.2.0 | **Tags:** #images, #database, #migration, #frontend

## 1. Tổng quan (Overview)
* **Mục tiêu:** Cho phép đính kèm ảnh khách và xử lý migration dữ liệu an toàn.
* **Trạng thái:** ✅ Hoàn thành

## 2. Vấn đề & Yêu cầu (Problem & Requirements)
* Cần thêm bảng `GuestImage` nhưng sợ mất dữ liệu cũ khi update schema.

## 3. Giải pháp Kỹ thuật (Technical Solution)
* **Migration Strategy (Plan B):**
    1. Export toàn bộ dữ liệu ra Excel (cải tiến export kèm password hash).
    2. Update Backend Schema (thêm bảng ảnh).
    3. Tạo DB mới.
    4. Import lại từ Excel (Logic import được nâng cấp để map lại quan hệ guest-user).
* **Frontend:**
    * Thêm Dialog xem ảnh Fullscreen.
    * Logic tự động copy ảnh cho các thành viên khi đăng ký theo đoàn.
* **Archive & Restore Ảnh:** Khi xóa khách, không xóa file ảnh vật lý mà move vào `uploads/archived_guests`. Import/Export hỗ trợ đường dẫn ảnh.
* **Chỉnh sửa ảnh:** API `DELETE /guests/images/{id}` cho phép xóa từng ảnh cũ.