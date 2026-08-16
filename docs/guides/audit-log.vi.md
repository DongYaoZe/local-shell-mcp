<!-- i18n-source-sha256: 4aec137923c38de0ed4a1b760b5dbd6ce99090d508ce3fe838d35ad44b4ba4f1 -->
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

Nhật ký bị giới hạn bởi `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES`. Hãy xoay vòng hoặc export ra bên ngoài nếu cần lưu giữ lâu.

## Giới hạn

Nhật ký audit không phải sandbox. Nó giúp truy vết nhưng không ngăn model đã kết nối thực hiện hành động trong phạm vi quyền được cấu hình.
