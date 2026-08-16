<!-- i18n-source-sha256: 3b7d6ab07c5d6bad2bfb22f366893819ac8de8754c7c28bcb35f24ea5695979c -->
# Доступ к Git

`local-shell-mcp` использует стандартный Git CLI через `run_shell`, `shell_start` или `job_start`. Специализированные Git MCP wrapper намеренно не предоставляются: CLI полнофункционален, знаком coding agents и позволяет не дублировать каждый подкоманд Git в списке инструментов.

## Типичный процесс

По возможности используйте ограниченные неинтерактивные команды:

```bash
git status --short --branch
git diff --stat
git diff
git add -- path/to/file
git commit -m "fix: concise description"
git push origin HEAD
```

Типичная последовательность agent:

1. Проверить состояние через `run_shell(command="git status --short --branch")`.
2. Читать и редактировать только относящиеся к задаче файлы.
3. Запустить целевые тесты.
4. Проверить через `run_shell(command="git diff --check && git diff")`.
5. Перед commit или push запустить `secret_scan`.
6. Выполнить stage, commit и push явными командами Git CLI.

Если repository находится на remote worker, используйте `machine` в том же shell tool.

## Учётные данные

Docker deployments могут сохранять стандартные Git credential locations в `/persist/credentials`. Считайте этот volume чувствительным. Предпочитайте deploy keys с областью одного repository, краткоживущие GitHub App tokens, изолированные automation users и ручную проверку перед push.

## Качество commit

Делайте commits сфокусированными, исключайте сгенерированные caches и build artifacts, записывайте выполненные tests и не добавляйте несвязанные изменения. Перед разрушительными командами reset, clean или force-push сначала проверьте точную цель.

## Диагностика

При ошибке `git push` проверьте remote URL, сохранение credentials, branch protection и права token. Если установлен GitHub CLI, полезна команда `gh auth status`.
