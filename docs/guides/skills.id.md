<!-- i18n-source-sha256: df2b62b1f847968432f0ba0309173e5de379bc9b821789715295018f72d58cf6 -->
# Agent Skills

`local-shell-mcp` mendukung Agent Skills berbasis Markdown yang dapat digunakan ulang melalui MCP tool surface yang tetap. Memasang atau menghapus Skill tidak pernah mengubah daftar tool MCP, sehingga client tidak perlu terhubung ulang.

## Sumber Skill

LSM memindai direktori berikut sesuai urutan prioritas:

```text
1. <workspace_root>/.agents/skills/
2. <state_dir>/agent_config/skills/
3. ${XDG_CONFIG_HOME:-~/.config}/agents/skills/
```

Dengan workspace dan state directory default, dua path pertama adalah:

```text
/workspace/.agents/skills
/workspace/.local-shell-mcp/agent_config/skills
```

Setiap child directory langsung adalah satu Skill. Nama directory menjadi nama Skill dan harus menyediakan `SKILL.md`. Direktori Skill, `SKILL.md`, related file, dan related directory dapat berupa symlink.

Jika nama Skill yang sama muncul di beberapa source, project source mengalahkan LSM-managed source, yang mengalahkan global source. `skill_list` melaporkan `source` dan `source_path` setiap Skill yang diterima, beserta daftar lengkap `skills_dirs` yang sudah diurutkan.

## Tool tetap

| Tool | Tujuan |
|---|---|
| `skill_list` | Memindai ulang semua source dan menampilkan nama Skill, description, source, entry path, related file, dan warning non-fatal tanpa memuat instruction lengkap. |
| `skill_load` | Memuat instruction `SKILL.md` lengkap untuk nama persis yang dikembalikan `skill_list`. |
| `skill_read` | Membaca satu related text file secara terbatas menggunakan Skill-relative path yang dikembalikan `skill_load`. |

Alur yang disarankan:

```text
skill_list
  -> choose the relevant Skill
  -> skill_load(name)
  -> skill_read(name, path) only when a related file is needed
  -> follow the Skill with the existing shell, Git, browser, and remote tools
```

Perubahan di disk terlihat pada panggilan berikutnya. Tidak ada tool MCP per-Skill yang didaftarkan.

## Instalasi dengan Skills CLI

Source project dan global sesuai dengan direktori universal yang digunakan CLI terbuka `skills`.

Instal ke workspace LSM saat ini:

```bash
cd /workspace
npx skills add owner/repository --agent universal -y
```

Instal secara global:

```bash
npx skills add owner/repository --agent universal --global -y
```

Untuk Skill tertentu:

```bash
npx skills add XiNian-dada/Fuck_My_Shit_Mountain \
  --skill fuck-my-shit-mountain \
  --agent universal \
  -y
```

LSM-managed source tetap tersedia untuk workflow file atau Git langsung:

```bash
git clone https://example.com/team/my-skill.git \
  /workspace/.local-shell-mcp/agent_config/skills/my-skill
```

Update dan penghapusan oleh CLI, Git, atau operasi filesystem biasa otomatis terlihat pada panggilan Skill berikutnya.

## Validasi

Registry melewati nama Skill yang malformed dan directory tanpa `SKILL.md` yang dapat dibaca. Batas file-size, Skill-count, scan-entry, related-file, dan path-output tetap berlaku. String directory traversal ditolak, sedangkan symlink filesystem diikuti.

## Kompatibilitas REST

REST surface opsional mengekspos registry gabungan yang sama:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```
