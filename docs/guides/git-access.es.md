<!-- i18n-source-sha256: 3b7d6ab07c5d6bad2bfb22f366893819ac8de8754c7c28bcb35f24ea5695979c -->
# Acceso a Git

`local-shell-mcp` usa la interfaz de línea de comandos estándar de Git mediante `run_shell`, `shell_start` o `job_start`. Los wrappers MCP dedicados para Git no se exponen deliberadamente: la CLI es completa, familiar para los coding agents y evita duplicar cada subcomando de Git en la lista de herramientas.

## Flujo habitual

Use comandos acotados y no interactivos siempre que sea posible:

```bash
git status --short --branch
git diff --stat
git diff
git add -- path/to/file
git commit -m "fix: concise description"
git push origin HEAD
```

Una secuencia típica del agent es:

1. Inspeccionar con `run_shell(command="git status --short --branch")`.
2. Leer y editar solo los archivos relevantes.
3. Ejecutar pruebas específicas.
4. Revisar con `run_shell(command="git diff --check && git diff")`.
5. Ejecutar `secret_scan` antes de commit o push.
6. Hacer stage, commit y push con comandos Git CLI explícitos.

Use `machine` en la misma herramienta shell cuando el repository esté en un remote worker.

## Credenciales

Los deployments Docker pueden persistir ubicaciones comunes de credentials Git bajo `/persist/credentials`. Trate ese volume como sensible. Prefiera deploy keys limitadas al repository, tokens de GitHub App de corta duración, usuarios de automatización aislados y revisión manual antes del push.

## Higiene de commits

Mantenga los commits enfocados, omita caches generadas y build artifacts, registre las pruebas ejecutadas y evite hacer stage de cambios no relacionados. Para comandos destructivos como reset, clean o force-push, inspeccione primero el objetivo exacto.

## Solución de problemas

Cuando falle `git push`, revise la remote URL, persistencia de credenciales, branch protection y permisos del token. `gh auth status` es útil si GitHub CLI está instalado.
