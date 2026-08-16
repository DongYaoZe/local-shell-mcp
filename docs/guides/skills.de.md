<!-- i18n-source-sha256: df2b62b1f847968432f0ba0309173e5de379bc9b821789715295018f72d58cf6 -->
# Agent Skills

`local-shell-mcp` unterstützt wiederverwendbare Markdown-basierte Agent Skills über eine feste MCP-Tool-Oberfläche. Das Installieren oder Entfernen einer Skill ändert niemals die MCP-Tool-Liste, sodass Clients keine neue Verbindung herstellen müssen.

## Skill-Quellen

LSM durchsucht diese Verzeichnisse in Prioritätsreihenfolge:

```text
1. <workspace_root>/.agents/skills/
2. <state_dir>/agent_config/skills/
3. ${XDG_CONFIG_HOME:-~/.config}/agents/skills/
```

Mit dem Standard-Workspace und State-Verzeichnis sind die ersten beiden Pfade:

```text
/workspace/.agents/skills
/workspace/.local-shell-mcp/agent_config/skills
```

Jedes direkte Unterverzeichnis ist eine Skill. Der Verzeichnisname ist der Skill-Name und es muss eine `SKILL.md` enthalten. Skill-Verzeichnisse, `SKILL.md`, zugehörige Dateien und zugehörige Verzeichnisse dürfen Symlinks sein.

Wenn derselbe Skill-Name in mehreren Quellen vorkommt, hat die Project-Quelle Vorrang vor der LSM-managed Quelle und diese wiederum vor der globalen Quelle. `skill_list` meldet `source` und `source_path` jeder akzeptierten Skill sowie die vollständige geordnete Liste `skills_dirs`.

## Feste Tools

| Tool | Zweck |
|---|---|
| `skill_list` | Alle Quellen erneut scannen und Skill-Namen, Beschreibungen, Quellen, Entry Paths, zugehörige Dateien und nicht-fatale Warnungen auflisten, ohne die vollständigen Anweisungen zu laden. |
| `skill_load` | Die vollständigen `SKILL.md`-Anweisungen für einen exakten von `skill_list` gelieferten Namen laden. |
| `skill_read` | Eine begrenzte zugehörige Textdatei über den von `skill_load` gelieferten Skill-relativen Pfad lesen. |

Empfohlener Ablauf:

```text
skill_list
  -> choose the relevant Skill
  -> skill_load(name)
  -> skill_read(name, path) only when a related file is needed
  -> follow the Skill with the existing shell, Git, browser, and remote tools
```

Änderungen auf dem Datenträger sind beim nächsten Aufruf sichtbar. Pro Skill werden keine MCP-Tools registriert.

## Installation mit der Skills CLI

Project- und globale Quellen entsprechen den universellen Verzeichnissen der offenen `skills` CLI.

Installation im aktuellen LSM-Workspace:

```bash
cd /workspace
npx skills add owner/repository --agent universal -y
```

Globale Installation:

```bash
npx skills add owner/repository --agent universal --global -y
```

Für eine bestimmte Skill:

```bash
npx skills add XiNian-dada/Fuck_My_Shit_Mountain \
  --skill fuck-my-shit-mountain \
  --agent universal \
  -y
```

Die LSM-managed Quelle bleibt für direkte Datei- oder Git-Workflows verfügbar:

```bash
git clone https://example.com/team/my-skill.git \
  /workspace/.local-shell-mcp/agent_config/skills/my-skill
```

Updates und Entfernungen durch CLI, Git oder normale Filesystem-Operationen werden beim nächsten Skill-Aufruf automatisch erkannt.

## Validierung

Die Registry überspringt ungültige Skill-Namen und Verzeichnisse ohne lesbare `SKILL.md`. Limits für Dateigröße, Skill-Anzahl, Scan-Einträge, zugehörige Dateien und Pfadausgabe gelten weiterhin. Directory-Traversal-Strings werden abgelehnt, Filesystem-Symlinks hingegen verfolgt.

## REST-Kompatibilität

Die optionale REST-Oberfläche stellt dieselbe zusammengeführte Registry bereit:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```
