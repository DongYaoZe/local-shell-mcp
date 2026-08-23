<!-- i18n-source-sha256: 25bb55459e83ee02b923876bad8d288c7a2055c4474f2098d58ce1e4a5e72605 -->
# Nhật ký audit

`local-shell-mcp` ghi các mục audit có cấu trúc để giúp dựng lại những gì một client đã kết nối thực hiện.

Đường dẫn mặc định:

```text
/workspace/.local-shell-mcp/audit.jsonl
```

## Nội dung được ghi

Các mục audit bao gồm những sự kiện như:

- Bắt đầu/kết thúc tool call.
- Metadata thực thi lệnh.
- Timeout và lỗi đã xử lý.
- Đăng ký remote worker và hoạt động job.
- Tạo và thu hồi file link.
- Sự kiện liên quan tới xác thực khi áp dụng.

Các đối số nhạy cảm được che nếu máy chủ nhận diện được chúng.

## Đọc nhật ký

Dùng tool MCP:

```text
audit_tail
```

Hoặc kiểm tra trực tiếp:

```bash
tail -n 100 /workspace/.local-shell-mcp/audit.jsonl
```

## Sử dụng vận hành

Nhật ký audit đặc biệt hữu ích để:

- Xem lại các lệnh đã thay đổi tệp.
- Kiểm tra có dùng remote worker hay không.
- Gỡ lỗi các thất bại bất ngờ.
- Phát hiện việc vô tình làm lộ file link.
- Hỗ trợ incident response sau lỗi deployment công khai.

## Lưu giữ

`audit.jsonl` đang hoạt động mặc định được giới hạn ở 20 MB bởi `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES`. Khi bảo trì retention, các record cũ được chuyển sang archive Zstandard tự chứa `audit-archive/*.jsonl.zst` thay vì bị bỏ; các audit payload lớn đã tách riêng cũng được đưa vào archive trước khi bị prune khỏi hot store.

Archive nén có giới hạn riêng `LOCAL_SHELL_MCP_MAX_AUDIT_ARCHIVE_BYTES`, mặc định 512 MB. Khi vượt giới hạn, archive cũ nhất bị xóa trước. Đặt thành `0` để tắt lưu trữ nén dài hạn. Web UI, truy vấn Activity/Audit và `audit_tail` chỉ đọc hot log đang hoạt động. Archive nén là cold storage dùng cho retention hoặc export và không được tự động giải nén bởi các truy vấn UI thông thường.

## Giới hạn

Nhật ký audit không phải sandbox. Nó giúp truy vết nhưng không ngăn model đã kết nối thực hiện hành động trong phạm vi quyền được cấu hình.
