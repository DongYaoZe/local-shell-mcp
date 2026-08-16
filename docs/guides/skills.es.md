<!-- i18n-source-sha256: df2b62b1f847968432f0ba0309173e5de379bc9b821789715295018f72d58cf6 -->
# Agent Skills

`local-shell-mcp` admite Agent Skills reutilizables basadas en Markdown mediante una MCP tool surface fija. Instalar o eliminar una Skill nunca cambia la lista de herramientas MCP, por lo que los clients no necesitan reconectarse.

## Fuentes de Skills

LSM examina estos directorios en orden de prioridad:

```text
1. <workspace_root>/.agents/skills/
2. <state_dir>/agent_config/skills/
3. ${XDG_CONFIG_HOME:-~/.config}/agents/skills/
```

Con el workspace y state directory predeterminados, las dos primeras rutas son:

```text
/workspace/.agents/skills
/workspace/.local-shell-mcp/agent_config/skills
```

Cada directorio hijo inmediato es una Skill. El nombre del directorio es el nombre de la Skill y debe proporcionar `SKILL.md`. Los directorios de Skill, `SKILL.md`, los archivos relacionados y los directorios relacionados pueden ser symlinks.

Cuando el mismo nombre de Skill aparece en varias fuentes, la fuente del proyecto prevalece sobre la gestionada por LSM, que a su vez prevalece sobre la global. `skill_list` informa del `source` y `source_path` de cada Skill aceptada, además de la lista completa y ordenada `skills_dirs`.

## Herramientas fijas

| Tool | Propósito |
|---|---|
| `skill_list` | Volver a examinar todas las fuentes y listar nombres, descriptions, sources, entry paths, archivos relacionados y warnings no fatales sin cargar las instrucciones completas. |
| `skill_load` | Cargar las instrucciones completas de `SKILL.md` para un nombre exacto devuelto por `skill_list`. |
| `skill_read` | Leer un archivo de texto relacionado y acotado usando la ruta relativa a la Skill devuelta por `skill_load`. |

Flujo recomendado:

```text
skill_list
  -> choose the relevant Skill
  -> skill_load(name)
  -> skill_read(name, path) only when a related file is needed
  -> follow the Skill with the existing shell, Git, browser, and remote tools
```

Los cambios en disco son visibles en la siguiente llamada. No se registran herramientas MCP por Skill.

## Instalación con Skills CLI

Las fuentes project y global coinciden con los directorios universales usados por la CLI abierta `skills`.

Instalar en el workspace LSM actual:

```bash
cd /workspace
npx skills add owner/repository --agent universal -y
```

Instalar globalmente:

```bash
npx skills add owner/repository --agent universal --global -y
```

Para una Skill específica:

```bash
npx skills add XiNian-dada/Fuck_My_Shit_Mountain \
  --skill fuck-my-shit-mountain \
  --agent universal \
  -y
```

La fuente gestionada por LSM sigue disponible para flujos directos de archivos o Git:

```bash
git clone https://example.com/team/my-skill.git \
  /workspace/.local-shell-mcp/agent_config/skills/my-skill
```

Las actualizaciones y eliminaciones realizadas por CLI, Git u operaciones filesystem normales se detectan automáticamente en la siguiente llamada de Skill.

## Validación

El registry omite nombres de Skill mal formados y directorios sin un `SKILL.md` legible. Siguen aplicándose límites de tamaño de archivo, número de Skills, entradas de escaneo, archivos relacionados y salida de rutas. Se rechazan cadenas de directory traversal y se siguen los symlinks del filesystem.

## Compatibilidad REST

La superficie REST opcional expone el mismo registry combinado:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```
