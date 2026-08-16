<!-- i18n-source-sha256: df2b62b1f847968432f0ba0309173e5de379bc9b821789715295018f72d58cf6 -->
# Agent Skills

`local-shell-mcp`, sabit bir MCP tool surface üzerinden yeniden kullanılabilir Markdown tabanlı Agent Skills destekler. Bir Skill’i kurmak veya kaldırmak MCP araç listesini hiçbir zaman değiştirmez; bu nedenle client’ların yeniden bağlanması gerekmez.

## Skill kaynakları

LSM şu dizinleri öncelik sırasıyla tarar:

```text
1. <workspace_root>/.agents/skills/
2. <state_dir>/agent_config/skills/
3. ${XDG_CONFIG_HOME:-~/.config}/agents/skills/
```

Varsayılan workspace ve state directory ile ilk iki yol şunlardır:

```text
/workspace/.agents/skills
/workspace/.local-shell-mcp/agent_config/skills
```

Her doğrudan alt dizin bir Skill’dir. Dizin adı Skill adıdır ve `SKILL.md` sağlamalıdır. Skill dizinleri, `SKILL.md`, related files ve related directories symlink olabilir.

Aynı Skill adı birden fazla source’da bulunursa project source, LSM-managed source’a; o da global source’a göre önceliklidir. `skill_list`, kabul edilen her Skill’in `source` ve `source_path` değerlerini, ayrıca tam ve sıralı `skills_dirs` listesini raporlar.

## Sabit araçlar

| Tool | Amaç |
|---|---|
| `skill_list` | Tüm source’ları yeniden tarayıp tam instruction’ları yüklemeden Skill adlarını, descriptions, sources, entry paths, related files ve non-fatal warnings listesini verir. |
| `skill_load` | `skill_list` tarafından döndürülen tam ad için eksiksiz `SKILL.md` instruction’larını yükler. |
| `skill_read` | `skill_load` tarafından döndürülen Skill-relative path ile sınırlı bir related text file okur. |

Önerilen akış:

```text
skill_list
  -> choose the relevant Skill
  -> skill_load(name)
  -> skill_read(name, path) only when a related file is needed
  -> follow the Skill with the existing shell, Git, browser, and remote tools
```

Diskteki değişiklikler bir sonraki çağrıda görünür. Skill başına MCP tool kaydedilmez.

## Skills CLI ile kurulum

Project ve global sources, açık `skills` CLI’nin kullandığı universal directories ile aynıdır.

Geçerli LSM workspace’e kurulum:

```bash
cd /workspace
npx skills add owner/repository --agent universal -y
```

Global kurulum:

```bash
npx skills add owner/repository --agent universal --global -y
```

Belirli bir Skill için:

```bash
npx skills add XiNian-dada/Fuck_My_Shit_Mountain \
  --skill fuck-my-shit-mountain \
  --agent universal \
  -y
```

LSM-managed source, doğrudan file veya Git workflows için de kullanılabilir:

```bash
git clone https://example.com/team/my-skill.git \
  /workspace/.local-shell-mcp/agent_config/skills/my-skill
```

CLI, Git veya normal filesystem operations ile yapılan update/remove işlemleri bir sonraki Skill çağrısında otomatik olarak algılanır.

## Doğrulama

Registry, hatalı Skill adlarını ve okunabilir `SKILL.md` bulunmayan dizinleri atlar. File-size, Skill-count, scan-entry, related-file ve path-output limitleri uygulanmaya devam eder. Directory traversal strings reddedilir, filesystem symlinks ise izlenir.

## REST uyumluluğu

İsteğe bağlı REST surface aynı birleştirilmiş registry’yi sunar:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```
