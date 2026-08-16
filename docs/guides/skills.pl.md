<!-- i18n-source-sha256: df2b62b1f847968432f0ba0309173e5de379bc9b821789715295018f72d58cf6 -->
# Agent Skills

`local-shell-mcp` obsługuje wielokrotnego użytku Agent Skills oparte na Markdown przez stały MCP tool surface. Instalowanie lub usuwanie Skill nigdy nie zmienia listy narzędzi MCP, więc client nie musi się ponownie łączyć.

## Źródła Skills

LSM skanuje następujące katalogi według priorytetu:

```text
1. <workspace_root>/.agents/skills/
2. <state_dir>/agent_config/skills/
3. ${XDG_CONFIG_HOME:-~/.config}/agents/skills/
```

Przy domyślnym workspace i state directory pierwsze dwie ścieżki to:

```text
/workspace/.agents/skills
/workspace/.local-shell-mcp/agent_config/skills
```

Każdy bezpośredni katalog podrzędny reprezentuje jedną Skill. Nazwa katalogu jest nazwą Skill i musi zawierać `SKILL.md`. Katalogi Skill, `SKILL.md`, related files i related directories mogą być symlinkami.

Gdy ta sama nazwa Skill występuje w kilku source, project source ma pierwszeństwo przed LSM-managed source, a ta przed global source. `skill_list` raportuje `source` i `source_path` każdej przyjętej Skill oraz pełną uporządkowaną listę `skills_dirs`.

## Stałe narzędzia

| Tool | Zastosowanie |
|---|---|
| `skill_list` | Ponownie skanuje wszystkie source i listuje nazwy Skills, descriptions, sources, entry paths, related files oraz non-fatal warnings bez ładowania pełnych instrukcji. |
| `skill_load` | Ładuje pełne instrukcje `SKILL.md` dla dokładnej nazwy zwróconej przez `skill_list`. |
| `skill_read` | Czyta jeden ograniczony related text file przez Skill-relative path zwrócony przez `skill_load`. |

Zalecany przebieg:

```text
skill_list
  -> choose the relevant Skill
  -> skill_load(name)
  -> skill_read(name, path) only when a related file is needed
  -> follow the Skill with the existing shell, Git, browser, and remote tools
```

Zmiany na dysku są widoczne przy następnym wywołaniu. Nie rejestruje się osobnych MCP tools dla każdej Skill.

## Instalacja przez Skills CLI

Project i global sources odpowiadają uniwersalnym katalogom używanym przez otwarte `skills` CLI.

Instalacja w bieżącym LSM workspace:

```bash
cd /workspace
npx skills add owner/repository --agent universal -y
```

Instalacja globalna:

```bash
npx skills add owner/repository --agent universal --global -y
```

Dla konkretnej Skill:

```bash
npx skills add XiNian-dada/Fuck_My_Shit_Mountain \
  --skill fuck-my-shit-mountain \
  --agent universal \
  -y
```

LSM-managed source pozostaje dostępny dla bezpośrednich workflow file lub Git:

```bash
git clone https://example.com/team/my-skill.git \
  /workspace/.local-shell-mcp/agent_config/skills/my-skill
```

Updates i removals wykonywane przez CLI, Git lub zwykłe filesystem operations są automatycznie wykrywane przy następnym Skill call.

## Walidacja

Registry pomija niepoprawne nazwy Skill i katalogi bez czytelnego `SKILL.md`. Nadal obowiązują limity file-size, Skill-count, scan-entry, related-file i path-output. Stringi directory traversal są odrzucane, a symlinki filesystem są śledzone.

## Zgodność REST

Opcjonalny REST surface udostępnia ten sam połączony registry:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```
