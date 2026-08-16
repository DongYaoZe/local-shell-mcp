<!-- i18n-source-sha256: df2b62b1f847968432f0ba0309173e5de379bc9b821789715295018f72d58cf6 -->
# Agent Skills

`local-shell-mcp` hỗ trợ Agent Skills dựa trên Markdown có thể tái sử dụng thông qua một MCP tool surface cố định. Cài hoặc xóa Skill không bao giờ làm thay đổi danh sách tool MCP, vì vậy client không cần kết nối lại.

## Nguồn Skill

LSM quét các thư mục sau theo thứ tự ưu tiên:

```text
1. <workspace_root>/.agents/skills/
2. <state_dir>/agent_config/skills/
3. ${XDG_CONFIG_HOME:-~/.config}/agents/skills/
```

Với workspace và state directory mặc định, hai đường dẫn đầu là:

```text
/workspace/.agents/skills
/workspace/.local-shell-mcp/agent_config/skills
```

Mỗi thư mục con trực tiếp là một Skill. Tên thư mục là tên Skill và phải có `SKILL.md`. Thư mục Skill, `SKILL.md`, related file và related directory có thể là symlink.

Khi cùng tên Skill xuất hiện ở nhiều source, project source ưu tiên hơn LSM-managed source, và LSM-managed source ưu tiên hơn global source. `skill_list` báo cáo `source` và `source_path` của mỗi Skill được chấp nhận, cùng danh sách `skills_dirs` đầy đủ theo thứ tự.

## Công cụ cố định

| Tool | Mục đích |
|---|---|
| `skill_list` | Quét lại mọi source và liệt kê tên Skill, description, source, entry path, related file và warning không nghiêm trọng mà không tải toàn bộ instruction. |
| `skill_load` | Tải instruction đầy đủ của `SKILL.md` cho tên chính xác do `skill_list` trả về. |
| `skill_read` | Đọc một related text file có giới hạn bằng Skill-relative path do `skill_load` trả về. |

Luồng khuyến nghị:

```text
skill_list
  -> choose the relevant Skill
  -> skill_load(name)
  -> skill_read(name, path) only when a related file is needed
  -> follow the Skill with the existing shell, Git, browser, and remote tools
```

Thay đổi trên disk sẽ xuất hiện ở lần gọi tiếp theo. Không đăng ký tool MCP riêng cho từng Skill.

## Cài bằng Skills CLI

Project source và global source khớp với các thư mục universal mà CLI mở `skills` sử dụng.

Cài vào workspace LSM hiện tại:

```bash
cd /workspace
npx skills add owner/repository --agent universal -y
```

Cài global:

```bash
npx skills add owner/repository --agent universal --global -y
```

Cho một Skill cụ thể:

```bash
npx skills add XiNian-dada/Fuck_My_Shit_Mountain \
  --skill fuck-my-shit-mountain \
  --agent universal \
  -y
```

LSM-managed source vẫn dùng được cho workflow file hoặc Git trực tiếp:

```bash
git clone https://example.com/team/my-skill.git \
  /workspace/.local-shell-mcp/agent_config/skills/my-skill
```

Update và remove thực hiện bằng CLI, Git hoặc thao tác filesystem thông thường sẽ tự động được nhận ở lần gọi Skill tiếp theo.

## Xác thực

Registry bỏ qua tên Skill malformed và directory không có `SKILL.md` đọc được. Các giới hạn file-size, Skill-count, scan-entry, related-file và path-output vẫn áp dụng. Chuỗi directory traversal bị từ chối, còn symlink filesystem được theo dõi.

## Tương thích REST

REST surface tùy chọn cung cấp cùng registry đã hợp nhất:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```
