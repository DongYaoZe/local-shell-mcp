<!-- i18n-source-sha256: 91695da5acbb82a8550b150249a9b97f17470140a72b27233e2470a93305e7fb -->
# Tự động hóa trình duyệt

Các tool trình duyệt dùng Playwright để kiểm tra trang, thu thập bằng chứng và chạy workflow trình duyệt có thể tái lập. Tool surface công khai được cố ý giữ nhỏ.

## Công cụ

| Tool | Mục đích |
|---|---|
| `browser_session` | Bắt đầu, liệt kê, đóng hoặc dọn các phiên trình duyệt bền vững; tùy chọn dùng lại profile hoặc storage state. |
| `browser_snapshot` | Đọc văn bản trang có giới hạn, lỗi page/network và phần tử tương tác với ref ngắn như `e1`; tùy chọn chụp screenshot. |
| `browser_act` | Chạy navigation, click, fill, select, key, wait và thao tác nhiều trang có cấu trúc bằng snapshot ref hoặc CSS selector. |
| `browser_run_script` | Chạy Python Playwright script đầy đủ khi tập hành động cấp cao không đủ. |

Mọi tool trình duyệt đều nhận `machine` tùy chọn. Các phụ thuộc trình duyệt phải được cài sẵn trên controller hoặc worker được chọn; việc cài đặt dùng lệnh shell thông thường như `python -m playwright install chromium`.

## Luồng thường dùng

Với công việc tương tác, gọi `browser_session(action="start", url=...)`, sau đó `browser_snapshot`. Snapshot trả về các tham chiếu ngắn như `e1` và `e2`; truyền trực tiếp chúng cho `browser_act`, ví dụ `{"action": "click", "target": "e1"}` hoặc `{"action": "fill", "target": "e2", "value": "..."}`. Chụp snapshot mới sau navigation vì element ref là tham chiếu trạng thái trang, không phải selector vĩnh viễn.

Với kiểm tra thông thường và screenshot, ưu tiên `browser_session` cùng `browser_snapshot`; snapshot có thể trả về visible text có giới hạn và lưu screenshot. Dùng `browser_run_script` cho JavaScript evaluation, logic capture/PDF tùy chỉnh hoặc tương tác không được `browser_act` biểu diễn.

Giữ script có giới hạn, đặt timeout rõ ràng, lưu artifact dưới workspace và tránh nhập credential trừ khi môi trường dành riêng cho tác vụ.
