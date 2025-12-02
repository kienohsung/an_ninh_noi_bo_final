# 🛑 SYSTEM INSTRUCTION & TEMPLATE
LƯU Ý QUAN TRỌNG:
File này dùng để theo dõi các điểm khôi phục (Restore Points) của dự án Git.
Mục đích: Giúp Developer dễ dàng quyết định quay lại (checkout) thời điểm nào khi gặp sự cố hoặc muốn rẽ nhánh phát triển.
Quy tắc:
1. Sau mỗi tính năng lớn, fix lỗi quan trọng, hoặc trước khi refactor, hãy tạo commit và ghi lại vào đây.
2. BẮT BUỘC cập nhật Mục Lục (Table of Contents) mỗi khi thêm nội dung mới.

📋 Template Mẫu (Copy & Paste khi thêm mới)
```markdown
## [DD/MM/YYYY] 🏷️ [Tên Restore Point / Commit Message Dễ Nhớ]
**Hash/Tag:** `[git-hash-hoặc-tag-nếu-có]` | **Trạng thái:** ✅ Stable (Ổn định) / 🚧 Experimental (Thử nghiệm)

* **Mô tả:** [Mô tả ngắn gọn trạng thái dự án tại thời điểm này. VD: Đã xong tính năng A, chưa test kỹ tính năng B]
* **Thay đổi chính:**
    * [Thay đổi 1]
    * [Thay đổi 2]
* **Lý do tạo:** [Tại sao cần điểm khôi phục này? VD: Trước khi nâng cấp thư viện X]
```

---

<!-- BẮT ĐẦU NỘI DUNG GIT DIARY TỪ DƯỚI DÒNG NÀY -->

# Mục Lục (Table of Contents)

1. [03/12/2025 - Google Form Integration Complete](#03122025-google-form-integration-complete)

---

# Nhật Ký Restore Point (Git Diary)

## <a id="03122025-google-form-integration-complete"></a> [03/12/2025] 🏷️ Google Form Integration Complete
**Hash/Tag:** `N/A` | **Trạng thái:** ✅ Stable

* **Mô tả:** Phiên bản đã hoàn tất tích hợp Google Form thay thế cho Telegram Bot Polling. Hệ thống hoạt động ổn định, đã fix các lỗi về Timezone và Schema.
* **Thay đổi chính:**
    * Thêm Service đồng bộ Google Form (`form_sync_service.py`).
    * Tắt Telegram Polling, chuyển sang chỉ gửi thông báo (`main.py`).
    * Cập nhật `gsheets_reader.py` hỗ trợ ghi dữ liệu.
    * Fix lỗi lệch giờ (-7h) và lỗi cột `source` trong DB.
* **Lý do tạo:** Hoàn thành Milestone chuyển đổi phương thức đăng ký khách. Điểm mốc an toàn để deploy hoặc phát triển tiếp.
