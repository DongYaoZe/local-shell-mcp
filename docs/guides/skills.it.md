<!-- i18n-source-sha256: df2b62b1f847968432f0ba0309173e5de379bc9b821789715295018f72d58cf6 -->
# Agent Skills

`local-shell-mcp` supporta Agent Skills riutilizzabili basate su Markdown tramite una MCP tool surface fissa. Installare o rimuovere una Skill non cambia mai l’elenco degli strumenti MCP, quindi i client non devono riconnettersi.

## Sorgenti delle Skills

LSM esamina queste directory in ordine di priorità:

```text
1. <workspace_root>/.agents/skills/
2. <state_dir>/agent_config/skills/
3. ${XDG_CONFIG_HOME:-~/.config}/agents/skills/
```

Con workspace e state directory predefiniti, i primi due percorsi sono:

```text
/workspace/.agents/skills
/workspace/.local-shell-mcp/agent_config/skills
```

Ogni directory figlia immediata rappresenta una Skill. Il nome della directory è il nome della Skill e deve contenere `SKILL.md`. Directory di Skill, `SKILL.md`, file correlati e directory correlate possono essere symlink.

Quando lo stesso nome di Skill compare in più sorgenti, la sorgente project prevale su quella gestita da LSM, che prevale sulla sorgente global. `skill_list` riporta `source` e `source_path` di ogni Skill accettata, oltre all’elenco completo e ordinato `skills_dirs`.

## Strumenti fissi

| Tool | Scopo |
|---|---|
| `skill_list` | Riesaminare tutte le sorgenti e elencare nomi, descriptions, sources, entry paths, file correlati e warnings non fatali senza caricare le istruzioni complete. |
| `skill_load` | Caricare tutte le istruzioni `SKILL.md` per un nome esatto restituito da `skill_list`. |
| `skill_read` | Leggere un file di testo correlato e limitato usando il percorso relativo alla Skill restituito da `skill_load`. |

Flusso consigliato:

```text
skill_list
  -> choose the relevant Skill
  -> skill_load(name)
  -> skill_read(name, path) only when a related file is needed
  -> follow the Skill with the existing shell, Git, browser, and remote tools
```

Le modifiche su disco sono visibili alla chiamata successiva. Non viene registrato alcuno strumento MCP per singola Skill.

## Installazione con Skills CLI

Le sorgenti project e global corrispondono alle directory universali usate dalla CLI aperta `skills`.

Installare nel workspace LSM corrente:

```bash
cd /workspace
npx skills add owner/repository --agent universal -y
```

Installare globalmente:

```bash
npx skills add owner/repository --agent universal --global -y
```

Per una Skill specifica:

```bash
npx skills add XiNian-dada/Fuck_My_Shit_Mountain \
  --skill fuck-my-shit-mountain \
  --agent universal \
  -y
```

La sorgente gestita da LSM resta disponibile per workflow diretti di file o Git:

```bash
git clone https://example.com/team/my-skill.git \
  /workspace/.local-shell-mcp/agent_config/skills/my-skill
```

Updates e rimozioni eseguiti da CLI, Git o normali operazioni filesystem vengono rilevati automaticamente alla chiamata Skill successiva.

## Validazione

Il registry ignora nomi di Skill non validi e directory prive di un `SKILL.md` leggibile. Restano applicati i limiti di dimensione file, numero di Skills, elementi di scan, file correlati e output dei path. Le stringhe di directory traversal vengono rifiutate, mentre i symlink del filesystem vengono seguiti.

## Compatibilità REST

La superficie REST opzionale espone lo stesso registry unificato:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```
