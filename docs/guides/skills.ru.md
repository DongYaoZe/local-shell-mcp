<!-- i18n-source-sha256: df2b62b1f847968432f0ba0309173e5de379bc9b821789715295018f72d58cf6 -->
# Agent Skills

`local-shell-mcp` поддерживает переиспользуемые Agent Skills на основе Markdown через фиксированный MCP tool surface. Установка или удаление Skill никогда не меняет список MCP-инструментов, поэтому clients не требуется переподключение.

## Источники Skills

LSM сканирует следующие каталоги в порядке приоритета:

```text
1. <workspace_root>/.agents/skills/
2. <state_dir>/agent_config/skills/
3. ${XDG_CONFIG_HOME:-~/.config}/agents/skills/
```

При стандартных workspace и state directory первые два пути выглядят так:

```text
/workspace/.agents/skills
/workspace/.local-shell-mcp/agent_config/skills
```

Каждый непосредственный дочерний каталог представляет одну Skill. Имя каталога является именем Skill, и внутри должен быть `SKILL.md`. Каталоги Skill, `SKILL.md`, связанные файлы и связанные каталоги могут быть symlink.

Если одинаковое имя Skill встречается в нескольких источниках, project source имеет приоритет над LSM-managed source, а та — над global source. `skill_list` сообщает `source` и `source_path` каждой принятой Skill, а также полный упорядоченный список `skills_dirs`.

## Фиксированные инструменты

| Tool | Назначение |
|---|---|
| `skill_list` | Повторно просканировать все источники и перечислить имена Skills, descriptions, sources, entry paths, связанные файлы и нефатальные warnings без загрузки полных инструкций. |
| `skill_load` | Загрузить полные инструкции `SKILL.md` для точного имени, возвращённого `skill_list`. |
| `skill_read` | Прочитать ограниченный связанный текстовый файл по Skill-relative path, возвращённому `skill_load`. |

Рекомендуемый процесс:

```text
skill_list
  -> choose the relevant Skill
  -> skill_load(name)
  -> skill_read(name, path) only when a related file is needed
  -> follow the Skill with the existing shell, Git, browser, and remote tools
```

Изменения на диске видны при следующем вызове. Отдельные MCP-инструменты для каждой Skill не регистрируются.

## Установка через Skills CLI

Project и global источники соответствуют универсальным каталогам, используемым открытой CLI `skills`.

Установка в текущий LSM workspace:

```bash
cd /workspace
npx skills add owner/repository --agent universal -y
```

Глобальная установка:

```bash
npx skills add owner/repository --agent universal --global -y
```

Для конкретной Skill:

```bash
npx skills add XiNian-dada/Fuck_My_Shit_Mountain \
  --skill fuck-my-shit-mountain \
  --agent universal \
  -y
```

LSM-managed source остаётся доступным для прямых file/Git workflow:

```bash
git clone https://example.com/team/my-skill.git \
  /workspace/.local-shell-mcp/agent_config/skills/my-skill
```

Updates и удаления через CLI, Git или обычные filesystem operations автоматически подхватываются при следующем Skill call.

## Валидация

Registry пропускает некорректные имена Skill и каталоги без читаемого `SKILL.md`. Ограничения file-size, Skill-count, scan-entry, related-file и path-output продолжают действовать. Строки directory traversal отклоняются, а filesystem symlink отслеживаются.

## Совместимость REST

Необязательный REST surface предоставляет тот же объединённый registry:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```
