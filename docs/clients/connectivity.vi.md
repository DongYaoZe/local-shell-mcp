<!-- i18n-source-sha256: 3986da6ff877609189b0d88d363aff1f5f45445f0cfe5ffa608a31929078542c -->
# Kết nối mạng

MCP client HTTP ở ngoài máy cần một HTTPS origin có thể truy cập. Trang này nói về định tuyến mạng, không phải việc chọn runtime.

client endpoint thường kết thúc bằng `/mcp`:

```text
https://your-public-host.example.com/mcp
```

Thiết lập public base URL của máy chủ chỉ là origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Không đưa `/mcp` vào base URL này.

## Các lựa chọn kết nối

| Lựa chọn | Khi nào dùng |
|---|---|
| Compose tunnel sidecar | Docker Compose với profile `tunnel` tích hợp |
| Tunnel bên ngoài | Bất kỳ runtime nào cần truy cập từ ngoài mạng cục bộ |
| Caddy | TLS tự động đơn giản |
| Nginx hoặc Nginx Proxy Manager | Hạ tầng Nginx hiện có |
| Traefik | Định tuyến container-native hiện có |

## Đường dẫn

Chuyển tiếp toàn bộ origin tới máy chủ đang chạy. Các đường dẫn quan trọng gồm:

| Đường dẫn | Mục đích |
|---|---|
| `/mcp` | MCP Streamable HTTP endpoint |
| `/healthz`, `/readyz` | Kiểm tra sức khỏe |
| `/.well-known/...` | Metadata khám phá client |
| `/oauth/...` | Luồng ủy quyền client |
| `/downloads/...` | Liên kết tệp được tạo tùy chọn |
| `/join/...`, `/remote/...` | Luồng remote-worker tùy chọn |

## Hành vi proxy

Proxy cần giữ nguyên đường dẫn, chuyển tiếp request body, hỗ trợ response dài và tránh timeout quá ngắn.

## Kiểm tra

```bash
curl -i http://127.0.0.1:8765/healthz
curl -i https://your-public-host.example.com/healthz
```

## Lỗi thường gặp

| Lỗi | Cách sửa |
|---|---|
| Dùng `https://host` thay vì `https://host/mcp` trong ChatGPT | Chỉ thêm `/mcp` vào client endpoint |
| Đặt `LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://host/mcp` | Chỉ đặt origin |
| Chỉ route `/mcp` | Route toàn bộ origin để discovery và ủy quyền cũng hoạt động |
| Chạy host runtime với workspace quá rộng | Dùng workspace hẹp hoặc Docker |

## Kết hợp gợi ý

| Runtime | Kiểu mạng |
|---|---|
| Docker Compose trên server | Reverse proxy hiện có hoặc Compose tunnel profile |
| Docker Compose trên máy gia đình | Outbound tunnel |
| VS Code extension trên laptop | Tunnel tạm thời cho phiên |
| Binary trên VM | Reverse proxy trên VM hoặc biên mạng |
| Server dev Python/source | Thường chỉ localhost |
| Stdio mode | Không có đường HTTP; dùng MCP client cục bộ |
