<!-- i18n-source-sha256: ed71ed496e65545264c76f97a154e8e0758faf58be0ba74c24c82f3b860ff4f2 -->
# Xử lý sự cố

Kiểm tra trạng thái dịch vụ:

```bash
curl -i http://127.0.0.1:8765/healthz
```

Kiểm tra log:

```bash
docker compose logs --tail=100 local-shell-mcp
```

Nếu ChatGPT không thể kết nối, hãy xác nhận `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` khớp chính xác với HTTPS origin công khai và `/mcp`, metadata OAuth cùng `/healthz` đều có thể truy cập qua tunnel hoặc reverse proxy.

Nếu remote worker không xuất hiện, hãy xác nhận chế độ remote đã bật, lời mời chưa hết hạn và máy từ xa có thể gửi các yêu cầu HTTPS đi ra tới máy chủ điều khiển.
