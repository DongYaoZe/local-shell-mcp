<!-- i18n-source-sha256: 8b4e2e48e58e65721bf5ebf9f7b1d8aedf34d62d5a7948d36d6b9102ee1f6cc3 -->
# Wybór runtime i model deploymentu

`local-shell-mcp` wymaga dwóch niezależnych decyzji:

1. **Runtime**: jak działa proces serwera i jaki workspace kontroluje.
2. **Client connection**: jak ChatGPT lub inny MCP client dociera do tego serwera.

Nie traktuj ChatGPT jako metody deploymentu. ChatGPT jest client. Docker, VS Code extension, release binaries, instalacje Python i stdio mode są opcjami runtime.

```text
Runtime layer                      Exposure layer                 Client layer
-------------------------------    ---------------------------    ----------------------
Docker Compose                     local HTTP only                ChatGPT custom MCP
VS Code extension                  HTTPS reverse proxy/tunnel     Generic MCP client
Standalone binary                  stdio process pipe             VS Code extension UI
pipx / source checkout             remote-worker outbound join    REST-style diagnostics
```

Typowy publiczny setup:

```text
ChatGPT
  -> https://mcp.example.com/mcp
  -> reverse proxy or tunnel
  -> local-shell-mcp runtime
  -> controlled workspace
```

Lokalny setup MCP client może być prostszy:

```text
Local MCP client
  -> starts local-shell-mcp --mode stdio
  -> controlled workspace
```

## Macierz wyboru runtime

| Runtime | Najlepszy dla | Granica izolacji | Źródło toolchain | Publiczny dostęp ChatGPT | Strona |
|---|---|---|---|---|---|
| Docker Compose | Większość coding-agent workloads i odtwarzalne workspaces | Container | Project image zawiera szeroki default toolchain | Dodaj HTTPS proxy lub tunnel | [Docker Compose](../installation/docker.md) |
| Docker Compose + tunnel sidecar | Publiczny deployment w jednym stack z Cloudflare Tunnel | Container | Project image | Wbudowane w profile Compose `tunnel` | [Docker Compose](../installation/docker.md#cloudflare-tunnel-sidecar) |
| VS Code extension | Start/stop server z editor workspace | Zwykle host process | Host tools plus configured executable | Dodaj zewnętrzny HTTPS tunnel/proxy dla ChatGPT | [VS Code extension](../installation/vscode-extension.md) |
| Standalone binary | Host lub VM bez Docker | Host or VM | Host tools plus configured executable | Dodaj HTTPS proxy lub tunnel | [Standalone binary](../installation/binary.md) |
| `pipx` / source install | Użycie Python-native, debugging, development | Host virtualenv or VM | Python package plus host tools | Dodaj HTTPS proxy lub tunnel | [Python install](../installation/python.md) |
| Stdio mode | Lokalne MCP clients bezpośrednio spawnujące procesy | Client process boundary | Host tools plus configured executable | Nieużywalny z ChatGPT web/app | [Stdio mode](../installation/stdio.md) |

## Macierz połączeń client

| Client path | Wymaga public HTTPS | Używa `/mcp` | Wymaga OAuth | Typowy runtime |
|---|---:|---:|---:|---|
| ChatGPT custom MCP connector | Tak | Tak | Tak dla użycia publicznego | Docker, VS Code extension, binary, or Python |
| Generic local MCP client over stdio | Nie | Nie | Nie | `local-shell-mcp --mode stdio` |
| Generic HTTP MCP client | Zwykle nie na localhost; tak między sieciami | Tak | Zalecane poza localhost | Any HTTP runtime |
| VS Code extension helper flow | Tylko jeśli ChatGPT ma się łączyć | Tak przy kopiowaniu ChatGPT URL | Zalecane dla ChatGPT | VS Code-launched runtime |

Zobacz [ChatGPT connector](../getting-started/chatgpt-connector.md), [generic MCP clients](../clients/generic-mcp.md), [network connectivity](../clients/connectivity.md).

## Co kontroluje każdy runtime

Każdy runtime uruchamia ten sam server code i udostępnia te same family MCP tools, jeśli są włączone:

- Shell i persistent shell sessions.
- Filesystem, search i patch tools.
- Git operations.
- Browser automation przez Playwright.
- Audit log i task-state tools.
- Tokenized file links.
- Optional remote-worker lifecycle i machine-routed tools.

Różnica nie dotyczy abstract API, lecz **operating environment** za nim.

| Pytanie | Docker Compose | VS Code extension | Binary / Python |
|---|---|---|---|
| Gdzie działają komendy? | W container | Zwykle w host workspace | W host lub VM process environment |
| Default workspace? | Mounted `/workspace` | Bieżący folder VS Code lub configured path | `LOCAL_SHELL_MCP_WORKSPACE_ROOT` |
| Compiler/browser preinstalled? | Tak, szeroko | Tylko jeśli zainstalowane na host | Tylko jeśli zainstalowane na host |
| Czy reset jest łatwy? | Odtwórz container i workspace volume | Zależy od workspace | Zależy od host/VM |
| Dobre do arbitrary package install? | Tak, jeśli disposable | Ryzykowniejsze na host | Ryzykowniejsze poza VM |

## Zalecany wybór

Użyj najpierw **Docker Compose**, chyba że masz powód, by tego nie robić. Zapewnia najczytelniejszą safety boundary i najbardziej kompletny default toolchain.

Użyj **VS Code extension**, gdy workflow zaczyna się w editor i potrzebujesz local launcher. To nadal runtime. Sam nie udostępnia servera ChatGPT; dla ChatGPT web/app dodaj tunnel lub reverse proxy.

Użyj **standalone binary**, jeśli Docker jest niedostępny, ale VM, container host lub dedicated user account już tworzy boundary.

Użyj **`pipx` lub source install** do development/debugging `local-shell-mcp` albo gdy Python-based environment jest łatwiejsze w utrzymaniu.

Użyj **stdio mode** tylko dla lokalnych MCP clients zdolnych spawnować server process. Nie jest to public deployment i ChatGPT web/app nie użyje go bezpośrednio.

## Reguła public endpoint

Dla HTTP MCP clients takich jak ChatGPT MCP endpoint to:

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` zawiera tylko origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Nie dodawaj `/mcp` do `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## Strony runtime

- [Docker Compose](../installation/docker.md)
- [VS Code extension](../installation/vscode-extension.md)
- [Standalone binary](../installation/binary.md)
- [Python, `pipx`, and source install](../installation/python.md)
- [Stdio mode](../installation/stdio.md)

## Strony client

- [ChatGPT connector](../getting-started/chatgpt-connector.md)
- [Generic MCP clients](../clients/generic-mcp.md)
- [Public HTTPS exposure](../clients/connectivity.md)
