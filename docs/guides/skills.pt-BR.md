<!-- i18n-source-sha256: df2b62b1f847968432f0ba0309173e5de379bc9b821789715295018f72d58cf6 -->
# Agent Skills

`local-shell-mcp` oferece Agent Skills reutilizáveis baseadas em Markdown por meio de uma MCP tool surface fixa. Instalar ou remover uma Skill nunca altera a lista de ferramentas MCP, portanto os clients não precisam se reconectar.

## Fontes de Skills

LSM examina estes diretórios em ordem de prioridade:

```text
1. <workspace_root>/.agents/skills/
2. <state_dir>/agent_config/skills/
3. ${XDG_CONFIG_HOME:-~/.config}/agents/skills/
```

Com o workspace e state directory padrão, os dois primeiros caminhos são:

```text
/workspace/.agents/skills
/workspace/.local-shell-mcp/agent_config/skills
```

Cada diretório filho imediato representa uma Skill. O nome do diretório é o nome da Skill e ele deve fornecer `SKILL.md`. Diretórios de Skill, `SKILL.md`, arquivos relacionados e diretórios relacionados podem ser symlinks.

Quando o mesmo nome de Skill aparece em várias fontes, a fonte project vence a fonte gerenciada pelo LSM, que vence a fonte global. `skill_list` informa `source` e `source_path` de cada Skill aceita, além da lista completa e ordenada `skills_dirs`.

## Ferramentas fixas

| Tool | Finalidade |
|---|---|
| `skill_list` | Reexaminar todas as fontes e listar nomes de Skills, descriptions, sources, entry paths, arquivos relacionados e warnings não fatais sem carregar as instruções completas. |
| `skill_load` | Carregar as instruções completas de `SKILL.md` para um nome exato retornado por `skill_list`. |
| `skill_read` | Ler um arquivo de texto relacionado e limitado usando o caminho relativo à Skill retornado por `skill_load`. |

Fluxo recomendado:

```text
skill_list
  -> choose the relevant Skill
  -> skill_load(name)
  -> skill_read(name, path) only when a related file is needed
  -> follow the Skill with the existing shell, Git, browser, and remote tools
```

Alterações no disco ficam visíveis na chamada seguinte. Nenhuma ferramenta MCP por Skill é registrada.

## Instalação com Skills CLI

As fontes project e global correspondem aos diretórios universais usados pela CLI aberta `skills`.

Instalar no workspace LSM atual:

```bash
cd /workspace
npx skills add owner/repository --agent universal -y
```

Instalar globalmente:

```bash
npx skills add owner/repository --agent universal --global -y
```

Para uma Skill específica:

```bash
npx skills add XiNian-dada/Fuck_My_Shit_Mountain \
  --skill fuck-my-shit-mountain \
  --agent universal \
  -y
```

A fonte gerenciada pelo LSM continua disponível para workflows diretos de arquivo ou Git:

```bash
git clone https://example.com/team/my-skill.git \
  /workspace/.local-shell-mcp/agent_config/skills/my-skill
```

Updates e remoções feitos pela CLI, Git ou operações filesystem normais são detectados automaticamente na chamada Skill seguinte.

## Validação

O registry ignora nomes de Skill malformados e diretórios sem um `SKILL.md` legível. Limites de tamanho de arquivo, número de Skills, entradas de scan, arquivos relacionados e saída de paths continuam valendo. Strings de directory traversal são rejeitadas, enquanto symlinks do filesystem são seguidos.

## Compatibilidade REST

A superfície REST opcional expõe o mesmo registry mesclado:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```
