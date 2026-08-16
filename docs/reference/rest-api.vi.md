<!-- i18n-source-sha256: 87dd7fb66311534dcd5a7217bba8c809f71fe6189e8c39b3e265da923cc82d22 -->
# REST API

Interface chính là MCP tại `/mcp`. REST surface cũng có sẵn cho health check, file link và một số service operation.

## Sức khỏe

```http
GET /healthz
```

Trả về tình trạng sức khỏe và trạng thái cơ bản của máy chủ.

## MCP

```http
POST /mcp
```

Streamable HTTP MCP endpoint được ChatGPT và các MCP client khác sử dụng.

## Gọi công cụ qua REST

Các lệnh gọi công cụ REST dùng envelope thành công/lỗi nhất quán. Lỗi xác thực trả về payload có cấu trúc `ok: false` thay vì exception thô của framework.

## Agent Skills

Registry Skills cố định cũng có thể dùng qua REST:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```

Các thay đổi trong thư mục Skill sẽ xuất hiện ở lần gọi tiếp theo và không làm thay đổi danh sách công cụ MCP.

## Liên kết tệp

Các lượt tải tệp có token được phục vụ bởi ứng dụng HTTP tích hợp. Liên kết là bearer URL với TTL, giới hạn số lượt tải tối đa tùy chọn và hỗ trợ thu hồi.

## Xác thực

Triển khai công khai nên dùng OAuth. Có thể bật localhost bypass khi phát triển, nhưng truy cập công khai không xác thực là không an toàn.
