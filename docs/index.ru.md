<!-- i18n-source-sha256: b999ae6985930651e74b974b12109889360442811d6eeb306e6fa39754dbc173 -->
<div class="hero-shell" markdown>
<span class="hero-eyebrow">MCP control plane, совместимый с ChatGPT</span>

# local-shell-mcp

Дайте AI assistant контролируемый shell, настоящий workspace, Git, browser automation, file sharing и remote-worker access, не покидая chat.

<div class="hero-actions" markdown>
[Начать](getting-started/quickstart.md){ .hero-action .hero-action--primary }
[Выбрать runtime](guides/deployment.md){ .hero-action .hero-action--secondary }
[Справочник tools](reference/tools.md){ .hero-action .hero-action--secondary }
</div>
</div>

<div class="feature-grid" markdown>
<div class="feature-card" markdown>
### Настоящая coding environment
Запускайте tests, изучайте repositories, patch files, работайте с Git и сохраняйте audit trail через один MCP endpoint.
</div>

<div class="feature-card" markdown>
### Уровни runtime и client
Выберите runtime: Docker, VS Code extension, binary, Python или stdio, затем отдельно подключите ChatGPT или другой MCP client.
</div>

<div class="feature-card" markdown>
### Управление remote machines
Подключайте NAT, firewall или HPC machines через outbound worker connections без открытия SSH ports.
</div>
</div>

## Что предоставляет

`local-shell-mcp` предоставляет ChatGPT и другим MCP-клиентам контролируемый локальный или контейнерный workspace. Он включает shell, persistent shell, filesystem, search, patch, Git, Playwright, audit, durable logical Sessions с необязательными Goal Plans, tokenized file links и remote-worker tools через совместимый с ChatGPT MCP server с OAuth.

Используйте, когда AI должен изучать repository, запускать tests, редактировать files, работать с Git, собирать browser evidence, создавать downloadable artifacts или управлять remote machine, которая может только исходяще подключаться к control server.

## Архитектура

```text
Runtime layer: Docker / VS Code extension / binary / Python / stdio
Exposure layer: localhost / HTTPS proxy / tunnel / stdio pipe
Client layer: ChatGPT / generic MCP client / editor helper
Controlled workspace: /workspace or configured workspace root
Optional remote workers: outbound machine connections
```

Предполагаемая isolation boundary — container или VM, где запущен service.

## Начать по сценарию

| Сценарий | Начать здесь | Почему |
|---|---|---|
| Первый публичный ChatGPT deployment | [Quickstart](getting-started/quickstart.md) | Docker Compose с OAuth и настройкой `/mcp` |
| Выбор runtime layer | [Runtime choices](guides/deployment.md) | Объясняет Docker, VS Code, binary, Python и stdio как отдельные runtime options |
| Добавить ChatGPT как client | [ChatGPT connector](getting-started/chatgpt-connector.md) | Endpoint, OAuth, первый безопасный prompt, tool discovery |
| Добавить LSM в DeepSeek Harness | [Плагин DeepSeek Harness](clients/deepseek-harness.md) | Установить repository как DSH bundle, сохранив полный набор LSM tools и remote-worker capabilities |
| Запуск из VS Code | [VS Code extension runtime](installation/vscode-extension.md) | Editor-launched runtime и заметки по host safety |
| Научиться работать с toolset | [Usage patterns](guides/usage-patterns.md) | Prompt templates и руководство по выбору tools |
| Понять каждый tool | [Tools reference](reference/tools.md) | Purpose, inputs, returns, combinations и notes для каждого tool |
| Подключить HPC, NPU/GPU или server node | [Remote workers](guides/remote-workers.md) | Outbound worker join flow и remote tool usage |
| Поделиться generated files | [File links](guides/file-links.md) | Tokenized download URL с TTL и revoke |
| Усилить безопасность deployment | [Security](security.md) | Isolation, OAuth, workspace scope и audit logs |

## Основные семейства tools

| Семейство | Примеры | Назначение |
|---|---|---|
| Shell and Python | `run_shell`, `run_python`, `shell_start` | Builds, tests, scripts, long-running processes |
| Files and search | `file_tree`, `file_grep`, `file_read`, `file_patch` | Repository inspection и precise edits |
| Git | `run_shell`, `run_shell`, `run_shell`, `run_shell` | Reviewable source-control workflows |
| Sessions и goals | `session_manage`, `plan_manage` | Durable task handoff, отчёты о прогрессе и необязательный Goal mode |
| Browser | `browser_session`, `browser_snapshot`, `browser_act`, `browser_run_script` | Persistent interaction, UI checks, screenshots, rendered docs и page text |
| File links | `link_create`, `link_revoke` | Скачивание generated artifacts из chat |
| Remote workers | `remote_manage`, `run_shell`, `remote_transfer` | Machines за NAT, firewall или cluster login flows |

## Типовые workflows

### Coding с ChatGPT

1. Запустите runtime, например Docker Compose, VS Code extension, binary или Python, в dedicated workspace.
2. Опубликуйте HTTP runtime, если ChatGPT нужен network access.
3. Добавьте public `/mcp` endpoint в ChatGPT.
4. Сначала попросите изучить repository и выполнить read-only checks.
5. После одобрения разрешите patch files, tests, diff review, commit и push.
6. Проверяйте audit log для задач с file links или remote systems.

### Remote HPC или accelerator host

1. Создайте одноразовый remote worker invite.
2. Вставьте generated command на remote host.
3. Используйте обычные tools с `machine`; Git через `run_shell`, transfer через `remote_transfer`.
4. После task revoke worker.

### Генерация artifacts

1. Пусть AI создаст file внутри `/workspace`.
2. Создайте tokenized file link с TTL/download limits.
3. Поделитесь link в chat.
4. После завершения revoke его.

## Язык

Этот site строится нативным MkDocs i18n plugin. Используйте language selector в header для переключения между English и переведёнными pages. Pages без перевода fallback на English.
