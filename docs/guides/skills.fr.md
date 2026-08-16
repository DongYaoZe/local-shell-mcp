<!-- i18n-source-sha256: df2b62b1f847968432f0ba0309173e5de379bc9b821789715295018f72d58cf6 -->
# Agent Skills

`local-shell-mcp` prend en charge des Agent Skills réutilisables fondées sur Markdown via une MCP tool surface fixe. Installer ou supprimer une Skill ne modifie jamais la liste des outils MCP ; les clients n’ont donc pas besoin de se reconnecter.

## Sources des Skills

LSM parcourt les répertoires suivants par ordre de priorité :

```text
1. <workspace_root>/.agents/skills/
2. <state_dir>/agent_config/skills/
3. ${XDG_CONFIG_HOME:-~/.config}/agents/skills/
```

Avec le workspace et le state directory par défaut, les deux premiers chemins sont :

```text
/workspace/.agents/skills
/workspace/.local-shell-mcp/agent_config/skills
```

Chaque répertoire enfant immédiat représente une Skill. Son nom est le nom de la Skill et il doit fournir `SKILL.md`. Les répertoires de Skill, `SKILL.md`, les fichiers associés et les répertoires associés peuvent être des symlinks.

Lorsque le même nom de Skill apparaît dans plusieurs sources, la source project l’emporte sur la source gérée par LSM, qui l’emporte sur la source global. `skill_list` indique le `source` et le `source_path` de chaque Skill retenue, ainsi que la liste complète et ordonnée `skills_dirs`.

## Outils fixes

| Tool | Rôle |
|---|---|
| `skill_list` | Rebalayer toutes les sources et lister noms, descriptions, sources, entry paths, fichiers associés et warnings non fatals sans charger les instructions complètes. |
| `skill_load` | Charger toutes les instructions `SKILL.md` pour un nom exact renvoyé par `skill_list`. |
| `skill_read` | Lire un fichier texte associé borné en utilisant le chemin relatif à la Skill renvoyé par `skill_load`. |

Flux recommandé :

```text
skill_list
  -> choose the relevant Skill
  -> skill_load(name)
  -> skill_read(name, path) only when a related file is needed
  -> follow the Skill with the existing shell, Git, browser, and remote tools
```

Les modifications sur disque sont visibles dès l’appel suivant. Aucun outil MCP propre à une Skill n’est enregistré.

## Installation avec Skills CLI

Les sources project et global correspondent aux répertoires universels utilisés par la CLI ouverte `skills`.

Installer dans le workspace LSM courant :

```bash
cd /workspace
npx skills add owner/repository --agent universal -y
```

Installer globalement :

```bash
npx skills add owner/repository --agent universal --global -y
```

Pour une Skill particulière :

```bash
npx skills add XiNian-dada/Fuck_My_Shit_Mountain \
  --skill fuck-my-shit-mountain \
  --agent universal \
  -y
```

La source gérée par LSM reste disponible pour les workflows directs de fichiers ou Git :

```bash
git clone https://example.com/team/my-skill.git \
  /workspace/.local-shell-mcp/agent_config/skills/my-skill
```

Les mises à jour et suppressions effectuées par la CLI, Git ou des opérations filesystem ordinaires sont détectées automatiquement au prochain appel Skill.

## Validation

Le registry ignore les noms de Skill mal formés et les répertoires dépourvus d’un `SKILL.md` lisible. Les limites de taille de fichier, nombre de Skills, entrées de scan, fichiers associés et sortie de chemins restent appliquées. Les chaînes de directory traversal sont rejetées, tandis que les symlinks du filesystem sont suivis.

## Compatibilité REST

La surface REST facultative expose le même registry fusionné :

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```
