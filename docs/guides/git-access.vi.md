<!-- i18n-source-sha256: 3b7d6ab07c5d6bad2bfb22f366893819ac8de8754c7c28bcb35f24ea5695979c -->
# Truy cập Git

`local-shell-mcp` dùng Git CLI chuẩn thông qua `run_shell`, `shell_start` hoặc `job_start`. Các Git MCP wrapper chuyên dụng cố ý không được cung cấp: CLI đầy đủ, quen thuộc với coding agent và tránh lặp lại mọi subcommand Git trong danh sách tool.

## Workflow thông thường

Ưu tiên lệnh có giới hạn và không tương tác khi có thể:

```bash
git status --short --branch
git diff --stat
git diff
git add -- path/to/file
git commit -m "fix: concise description"
git push origin HEAD
```

Một chuỗi agent điển hình:

1. Kiểm tra bằng `run_shell(command="git status --short --branch")`.
2. Chỉ đọc và chỉnh sửa các tệp liên quan.
3. Chạy test mục tiêu.
4. Xem lại bằng `run_shell(command="git diff --check && git diff")`.
5. Chạy `secret_scan` trước commit hoặc push.
6. Stage, commit và push bằng lệnh Git CLI rõ ràng.

Dùng `machine` trên cùng shell tool khi repository nằm trên remote worker.

## Credential

Deployment Docker có thể lưu bền các vị trí credential Git phổ biến dưới `/persist/credentials`. Hãy coi volume đó là nhạy cảm. Ưu tiên deploy key giới hạn theo repository, GitHub App token sống ngắn, tài khoản automation tách biệt và review thủ công trước push.

## Vệ sinh commit

Giữ commit tập trung, bỏ cache được tạo và build artifact, ghi lại test đã chạy và tránh stage thay đổi không liên quan. Với lệnh phá hủy như reset, clean hoặc force-push, hãy kiểm tra chính xác mục tiêu trước.

## Xử lý sự cố

Khi `git push` thất bại, kiểm tra remote URL, lưu credential, branch protection và quyền token. `gh auth status` hữu ích nếu đã cài GitHub CLI.
