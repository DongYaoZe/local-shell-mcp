<!-- i18n-source-sha256: db40797f92f76326aa62db50ac4bb293edb4248791806c2fb46477a65c3e73cc -->
# Runtime rozszerzenia VS Code

Rozszerzenie VS Code jest launcherem i convenience UI dla tego samego servera `local-shell-mcp`. To wybór runtime, ponieważ uruchamia server process dla bieżącego editor workspace.

Nie jest to sam ChatGPT connector. Przy użyciu web/app ChatGPT nadal łączy się z public HTTPS `/mcp` endpoint.

## Co robi rozszerzenie

Rozszerzenie:

- Uruchamia `local-shell-mcp` dla bieżącego VS Code workspace.
- Stop i restart servera.
- Pokazuje server output w VS Code output channel.
- Sprawdza `/healthz`.
- Kopiuje MCP URL.
- Kopiuje ChatGPT setup prompt zawierający workspace i endpoint.

Rozszerzenie nie bundleuje server binary. Zainstaluj `local-shell-mcp` osobno i wskaż executable, jeśli nie jest w `PATH`.

## Kiedy używać

Używaj tego runtime, gdy:

- Zwykle zaczynasz pracę z VS Code folder.
- Chcesz button/command-palette flow zamiast ręcznego terminal command.
- Project dependencies są już zainstalowane na host.
- Pracujesz na trusted repositories lub wąskim workspace.
- Akceptujesz expose tylko tego workspace modelowi.

Używaj Docker, gdy:

- Repository jest untrusted.
- Task będzie installował arbitrary packages.
- Potrzebujesz broad preinstalled toolchain.
- Chcesz łatwy reset przez recreated container.
- Chcesz czystszej boundary niż host account.

## Instalacja executable

Wybierz server install method:

```bash
pipx install local-shell-mcp
```

lub download release binary dla OS i umieść w `PATH`.

Następnie install VSIX release asset:

```bash
code --install-extension local-shell-mcp-<version>.vsix
```

Alternatywnie użyj **Extensions: Install from VSIX...** w command palette.

## Extension settings

| Setting | Purpose | Typical value |
|---|---|---|
| `local-shell-mcp.executablePath` | Server executable path | `local-shell-mcp` or an absolute binary path |
| `local-shell-mcp.host` | Local server bind address | `127.0.0.1` for local-only, `0.0.0.0` only behind a controlled network/proxy |
| `local-shell-mcp.port` | Local server port | `8765` |
| `local-shell-mcp.workspaceRoot` | Workspace expose do MCP | Empty dla pierwszego VS Code folder lub explicit path |
| `local-shell-mcp.authMode` | Authentication mode | `oauth` for ChatGPT, `none` only for trusted localhost testing |
| `local-shell-mcp.publicBaseUrl` | Public HTTPS origin copy do prompts i URLs | Tunnel/proxy origin such as `https://mcp.example.com` |
| `local-shell-mcp.oauthAdminPin` | PIN do OAuth authorization | Strong random value dla public use |
| `local-shell-mcp.allowFullContainer` | Full-container behavior flag | Dla direct host usage trzymaj `false` |
| `local-shell-mcp.extraEnv` | Extra environment dla server process | Tylko project-specific safe values |

## Basic flow

1. Otwórz project folder w VS Code.
2. Uruchom **local-shell-mcp: Start Server**.
3. Uruchom **Show Server Status** lub **Check Health**, jeśli dostępne.
4. Użyj **Copy MCP URL** dla local MCP client albo **Copy ChatGPT Setup Prompt** dla ChatGPT.
5. Dodaj endpoint do client.

Local endpoint zwykle wygląda tak:

```text
http://127.0.0.1:8765/mcp
```

Jest użyteczny dla local clients, ale ChatGPT web/app go nie osiągnie.

## Użycie z ChatGPT

Aby użyć VS Code-launched server z ChatGPT, dodaj HTTPS tunnel lub reverse proxy przed local port.

Przykład:

```text
ChatGPT
  -> https://your-public-host.example.com/mcp
  -> tunnel or reverse proxy
  -> 127.0.0.1:8765 on your machine
  -> VS Code-launched local-shell-mcp process
```

Set:

```text
local-shell-mcp.publicBaseUrl = https://your-public-host.example.com
local-shell-mcp.authMode = oauth
local-shell-mcp.oauthAdminPin = <strong pin>
```

URL copy dla ChatGPT musi kończyć się `/mcp`:

```text
https://your-public-host.example.com/mcp
```

## Host-runtime safety

Rozszerzenie zwykle wykonuje commands jako host user. To istotnie różni się od disposable Docker container.

Zalecane zasady:

- Otwieraj tylko repository, które model ma kontrolować.
- Trzymaj `allowFullContainer` wyłączone.
- Nie setuj workspace root na home directory.
- Nie trzymaj unrelated secrets w workspace.
- Używaj `secret_scan` przed commit/push.
- Preferuj Docker dla unfamiliar repositories lub package-install-heavy tasks.

## Common prompt

Po copy setup prompt zacznij od read-only task:

```text
Użyj local-shell-mcp. Najpierw wywołaj environment_get i file_tree na workspace. Jeszcze nie modyfikuj plików.
```

Potem przejdź do bounded edit:

```text
Napraw failing test w tym workspace. Najpierw przeczytaj relevant files, zrób najmniejszy patch, uruchom targeted test i pokaż git diff. Nie rób commit przed moją zgodą.
```

## Troubleshooting

| Objaw | Sprawdź |
|---|---|
| Extension nie może uruchomić server | Potwierdź, że `local-shell-mcp.executablePath` istnieje i `--help` działa w terminal |
| ChatGPT nie może dotrzeć | Local `127.0.0.1` URL nie jest public; skonfiguruj tunnel/proxy i `publicBaseUrl` |
| Tools expose niewłaściwy folder | Set `local-shell-mcp.workspaceRoot` explicit |
| Auth psuje się po restart | Set stabilny OAuth admin PIN i JWT secret przez `extraEnv` lub runtime configuration |
| Commands nie mają dependencies | Install dependencies na host lub przejdź na Docker runtime |
