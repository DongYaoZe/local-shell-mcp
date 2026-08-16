<!-- i18n-source-sha256: 1f30fc9935125c84fb0838d17ec894d78aaa6253fe3903356414aac716ba2adc -->
# Bảo mật

Hãy dùng OAuth cho các triển khai công khai. Đặt giá trị mạnh cho `LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN` và `LOCAL_SHELL_MCP_OAUTH_JWT_SECRET`, đồng thời giữ chúng bí mật.

Theo mặc định, các thao tác đường dẫn bị giới hạn trong workspace và các đoạn đường dẫn nhạy cảm bị chặn. Chế độ Full-container vô hiệu hóa các giới hạn workspace và đường dẫn tích hợp, vì vậy chỉ nên dùng trong container hoặc VM có thể bỏ đi.

Các liên kết tải tệp được tạo là bearer URL công khai. Chúng dựa vào token có entropy cao, TTL, giới hạn số lượt tải xuống tùy chọn, giới hạn kích thước tùy chọn và khả năng thu hồi.
