<!-- i18n-source-sha256: b999ae6985930651e74b974b12109889360442811d6eeb306e6fa39754dbc173 -->
<div class="hero-shell" markdown>
<span class="hero-eyebrow">Control plane MCP zgodny z ChatGPT</span>

# local-shell-mcp

Daj AI assistant kontrolowany shell, prawdziwy workspace, Git, browser automation, file sharing i remote-worker access bez opuszczania chat.

<div class="hero-actions" markdown>
[Zacznij](getting-started/quickstart.md){ .hero-action .hero-action--primary }
[Wybierz runtime](guides/deployment.md){ .hero-action .hero-action--secondary }
[Referencja tools](reference/tools.md){ .hero-action .hero-action--secondary }
</div>
</div>

<div class="feature-grid" markdown>
<div class="feature-card" markdown>
### Prawdziwe środowisko coding
Uruchamiaj tests, sprawdzaj repositories, patch files, obsługuj Git i zachowuj audit trail z jednego MCP endpoint.
</div>

<div class="feature-card" markdown>
### Warstwy runtime i client
Wybierz runtime, np. Docker, VS Code extension, binary, Python lub stdio, a następnie osobno połącz ChatGPT lub inny MCP client.
</div>

<div class="feature-card" markdown>
### Kontrola remote machines
Podłączaj machines za NAT, firewall lub HPC przez outbound worker connections bez otwierania portów SSH.
</div>
</div>

## Co zapewnia

`local-shell-mcp` udostępnia ChatGPT i innym klientom MCP kontrolowany lokalny lub kontenerowy workspace. Zapewnia shell, persistent shell, filesystem, search, patch, Git, Playwright, audit, trwałe logical Sessions z opcjonalnymi Goal Plans, tokenized file links i narzędzia remote worker przez zgodny z ChatGPT MCP server z OAuth.

Używaj, gdy AI musi inspect repository, uruchamiać tests, edit files, operate Git, zbierać browser evidence, tworzyć downloadable artifacts lub kontrolować remote machine, która może tylko outbound connect do control server.

## Architektura

```text
Warstwa runtime: Docker / VS Code extension / binary / Python / stdio
Warstwa exposure: localhost / HTTPS proxy / tunnel / stdio pipe
Warstwa client: ChatGPT / generic MCP client / editor helper
Kontrolowany workspace: /workspace or configured workspace root
Optional remote workers: outbound machine connections
```

Docelową isolation boundary jest container lub VM uruchamiający service.

## Zacznij według scenariusza

| Scenariusz | Zacznij tutaj | Dlaczego |
|---|---|---|
| Pierwszy public ChatGPT deployment | [Quickstart](getting-started/quickstart.md) | Ścieżka Docker Compose z OAuth i setup `/mcp` |
| Wybór runtime layer | [Runtime choices](guides/deployment.md) | Opisuje Docker, VS Code, binary, Python i stdio jako osobne runtime options |
| Dodanie ChatGPT jako client | [ChatGPT connector](getting-started/chatgpt-connector.md) | Endpoint, OAuth, pierwszy bezpieczny prompt, tool discovery |
| Dodać LSM do DeepSeek Harness | [Plugin DeepSeek Harness](clients/deepseek-harness.md) | Zainstalować repository jako DSH bundle, zachowując pełną powierzchnię narzędzi LSM i remote workers |
| Uruchomienie z VS Code | [VS Code extension runtime](installation/vscode-extension.md) | Editor-launched runtime i uwagi host safety |
| Nauka obsługi toolset | [Usage patterns](guides/usage-patterns.md) | Prompt templates i tool-choice guidance |
| Zrozumienie każdego tool | [Tools reference](reference/tools.md) | Purpose, inputs, returns, combinations i notes dla każdego tool |
| Podłączenie HPC, NPU/GPU lub server node | [Remote workers](guides/remote-workers.md) | Outbound worker join flow i remote tool usage |
| Udostępnianie generated files | [File links](guides/file-links.md) | Tokenized download URLs z TTL i revoke |
| Hardening deployment | [Security](security.md) | Isolation, OAuth, workspace scope i audit logs |

## Główne tool families

| Family | Przykłady | Zastosowanie |
|---|---|---|
| Shell and Python | `run_shell`, `run_python`, `shell_start` | Builds, tests, scripts, long-running processes |
| Files and search | `file_tree`, `file_grep`, `file_read`, `file_patch` | Repository inspection i precise edits |
| Git | `run_shell`, `run_shell`, `run_shell`, `run_shell` | Reviewable source-control workflows |
| Sessions i goals | `session_manage`, `plan_manage` | Trwały task handoff, progress report i opcjonalny Goal mode |
| Browser | `browser_session`, `browser_snapshot`, `browser_act`, `browser_run_script` | Persistent interaction, UI checks, screenshots, rendered docs i page text |
| File links | `link_create`, `link_revoke` | Download generated artifacts z chat |
| Remote workers | `remote_manage`, `run_shell`, `remote_transfer` | Machines za NAT, firewalls lub cluster login flows |

## Typowe workflows

### Coding z ChatGPT

1. Uruchom runtime, np. Docker Compose, VS Code extension, binary lub Python, w dedicated workspace.
2. Expose HTTP runtime, jeśli ChatGPT potrzebuje network access.
3. Dodaj public `/mcp` endpoint do ChatGPT.
4. Najpierw poproś o repository inspection i read-only checks.
5. Po zatwierdzeniu pozwól na patch files, tests, diff review, commit i push.
6. Sprawdź audit log, gdy task dotyczy file links lub remote systems.

### Remote HPC lub accelerator host

1. Utwórz one-time remote worker invite.
2. Wklej generated command na remote host.
3. Używaj normal tools z `machine`; Git przez `run_shell`, transfer przez `remote_transfer`.
4. Po task revoke worker.

### Artifact generation

1. Pozwól AI generate file pod `/workspace`.
2. Utwórz tokenized file link z TTL/download limits.
3. Udostępnij link w chat.
4. Po zakończeniu revoke.

## Język

Ta site jest buildowana natywnym MkDocs i18n plugin. Użyj language selector w header, aby przełączać English i translated pages. Pages bez translation fallbackują do English.
