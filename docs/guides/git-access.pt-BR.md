<!-- i18n-source-sha256: 3b7d6ab07c5d6bad2bfb22f366893819ac8de8754c7c28bcb35f24ea5695979c -->
# Acesso ao Git

`local-shell-mcp` usa a interface padrão de linha de comando do Git por meio de `run_shell`, `shell_start` ou `job_start`. Wrappers MCP dedicados ao Git não são expostos de propósito: a CLI é completa, familiar aos coding agents e evita duplicar cada subcomando Git na lista de ferramentas.

## Fluxo comum

Use comandos delimitados e não interativos sempre que possível:

```bash
git status --short --branch
git diff --stat
git diff
git add -- path/to/file
git commit -m "fix: concise description"
git push origin HEAD
```

Uma sequência típica do agent é:

1. Inspecionar com `run_shell(command="git status --short --branch")`.
2. Ler e editar apenas os arquivos relevantes.
3. Executar testes direcionados.
4. Revisar com `run_shell(command="git diff --check && git diff")`.
5. Executar `secret_scan` antes de commit ou push.
6. Fazer stage, commit e push com comandos Git CLI explícitos.

Use `machine` na mesma ferramenta shell quando o repository estiver em um remote worker.

## Credenciais

Deployments Docker podem persistir locais comuns de credentials Git em `/persist/credentials`. Trate esse volume como sensível. Prefira deploy keys com escopo de repository, tokens GitHub App de curta duração, usuários de automação isolados e revisão manual antes do push.

## Higiene de commits

Mantenha os commits focados, exclua caches gerados e build artifacts, registre os testes executados e evite adicionar mudanças não relacionadas. Para comandos destrutivos como reset, clean ou force-push, inspecione primeiro o alvo exato.

## Solução de problemas

Quando `git push` falhar, verifique a remote URL, persistência de credentials, branch protection e permissões do token. `gh auth status` é útil quando o GitHub CLI está instalado.
