<!-- i18n-source-sha256: d758caead1c922385409aceebf498662f25f4cbf252a48d65b29d91f07e5a173 -->
# Liên kết tệp

`local-shell-mcp` có thể cung cấp tệp từ workspace được kiểm soát qua bearer URL có entropy cao. Điều này hữu ích khi AI tạo báo cáo, archive, PDF, screenshot hoặc artifact khác cần tải xuống từ hoặc hiển thị trong chat.

## Khi nào dùng liên kết tệp

Dùng liên kết tệp cho:

- PDF hoặc báo cáo được tạo.
- Screenshot và browser artifact.
- Output build.
- Log quá lớn để dán vào chat.
- Archive chuẩn bị cho kiểm tra thủ công.

Không dùng liên kết tệp cho secret, private key, kho credential hoặc dữ liệu cá nhân không liên quan.

## Luồng điển hình

1. Tạo hoặc tìm tệp dưới `/workspace`.
2. Gọi `link_create` với TTL và giới hạn tải xuống tùy chọn. Đặt `inline=true` nếu tệp cần hiển thị trực tiếp trong trình duyệt hoặc như ảnh Markdown; mặc định là `false`, buộc attachment download.
3. Chia sẻ URL trả về.
4. Thu hồi liên kết khi không còn cần.

## Công cụ liên quan

| Tool | Mục đích |
|---|---|
| `link_create` | Tạo URL có token cho tệp workspace. |
| `link_list` | Hiển thị liên kết đang hoạt động. |
| `link_revoke` | Vô hiệu hóa liên kết trước khi hết hạn. |

## Kiểm soát

Các tùy chọn cấu hình gồm:

- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_ENABLED`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_MAX_DOWNLOADS`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_FILE_BYTES`

Dùng TTL ngắn hơn cho artifact nhạy cảm và đặt maximum download count khi liên kết chỉ dành cho một người nhận.

## Ghi chú bảo mật

Liên kết tệp là bearer URL. Bất kỳ ai có URL đều có thể tải tệp cho tới khi liên kết hết hạn, đạt download limit hoặc bị thu hồi. Hãy coi chúng như secret tạm thời. Inline response có CSP sandbox và `X-Content-Type-Options: nosniff`, vì vậy định dạng chủ động không thể truy cập LSM origin hoặc thực thi như nội dung same-origin không sandbox.
