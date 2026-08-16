<!-- i18n-source-sha256: 8b4e2e48e58e65721bf5ebf9f7b1d8aedf34d62d5a7948d36d6b9102ee1f6cc3 -->
# Runtime seçenekleri ve deployment modeli

`local-shell-mcp` içinde iki bağımsız karar vardır:

1. **Runtime**: server process’in nasıl çalıştığı ve hangi workspace’i kontrol ettiği.
2. **Client connection**: ChatGPT veya başka bir MCP client’ın bu server’a nasıl ulaştığı.

ChatGPT’yi deployment yöntemi olarak görmeyin. ChatGPT bir client’tır. Docker, VS Code extension, release binaries, Python installs ve stdio mode runtime seçenekleridir.

```text
Runtime layer                      Exposure layer                 Client layer
-------------------------------    ---------------------------    ----------------------
Docker Compose                     local HTTP only                ChatGPT custom MCP
VS Code extension                  HTTPS reverse proxy/tunnel     Generic MCP client
Standalone binary                  stdio process pipe             VS Code extension UI
pipx / source checkout             remote-worker outbound join    REST-style diagnostics
```

Yaygın bir public setup:

```text
ChatGPT
  -> https://mcp.example.com/mcp
  -> reverse proxy or tunnel
  -> local-shell-mcp runtime
  -> controlled workspace
```

Local MCP client setup daha basit olabilir:

```text
Local MCP client
  -> starts local-shell-mcp --mode stdio
  -> controlled workspace
```

## Runtime seçim matrisi

| Runtime | En uygun | Isolation boundary | Toolchain kaynağı | Public ChatGPT erişimi | Sayfa |
|---|---|---|---|---|---|
| Docker Compose | Çoğu coding-agent workload ve reproducible workspace | Container | Project image geniş default toolchain içerir | HTTPS proxy veya tunnel ekle | [Docker Compose](../installation/docker.md) |
| Docker Compose + tunnel sidecar | Cloudflare Tunnel ile tek-stack public deployment | Container | Project image | Compose `tunnel` profile içine gömülü | [Docker Compose](../installation/docker.md#cloudflare-tunnel-sidecar) |
| VS Code extension | Editor workspace içinden server start/stop | Genellikle host process | Host tools ve configured executable | ChatGPT için harici HTTPS tunnel/proxy ekle | [VS Code extension](../installation/vscode-extension.md) |
| Standalone binary | Docker olmayan host veya VM | Host or VM | Host tools ve configured executable | HTTPS proxy veya tunnel ekle | [Standalone binary](../installation/binary.md) |
| `pipx` / source install | Python-native kullanım, debugging, development | Host virtualenv or VM | Python package ve host tools | HTTPS proxy veya tunnel ekle | [Python install](../installation/python.md) |
| Stdio mode | Process’i doğrudan spawn eden local MCP client’lar | Client process boundary | Host tools ve configured executable | ChatGPT web/app ile kullanılamaz | [Stdio mode](../installation/stdio.md) |

## Client bağlantı matrisi

| Client path | Public HTTPS gerekir | `/mcp` kullanır | OAuth gerekir | Tipik runtime |
|---|---:|---:|---:|---|
| ChatGPT custom MCP connector | Evet | Evet | Public kullanımda evet | Docker, VS Code extension, binary, or Python |
| Generic local MCP client over stdio | Hayır | Hayır | Hayır | `local-shell-mcp --mode stdio` |
| Generic HTTP MCP client | localhost için genelde hayır; ağlar arası evet | Evet | localhost dışında önerilir | Any HTTP runtime |
| VS Code extension helper flow | Yalnız ChatGPT bağlanacaksa | ChatGPT URL copy edilirken evet | ChatGPT için önerilir | VS Code-launched runtime |

Bkz. [ChatGPT connector](../getting-started/chatgpt-connector.md), [generic MCP clients](../clients/generic-mcp.md), [network connectivity](../clients/connectivity.md).

## Her runtime neyi kontrol eder

Her runtime aynı server code’u başlatır ve etkinleştirildiğinde aynı MCP tool family’lerini sunar:

- Shell ve persistent shell sessions.
- Filesystem, search ve patch tools.
- Git operations.
- Playwright ile browser automation.
- Audit log ve task-state tools.
- Tokenized file links.
- Optional remote-worker lifecycle ve machine-routed tools.

Fark abstract API değil, arkasındaki **operating environment**’dır.

| Soru | Docker Compose | VS Code extension | Binary / Python |
|---|---|---|---|
| Command nerede çalışır? | Container içinde | Genellikle host workspace üzerinde | Host veya VM process environment içinde |
| Default workspace? | Mounted `/workspace` | Geçerli VS Code folder veya configured path | `LOCAL_SHELL_MCP_WORKSPACE_ROOT` |
| Compiler/browser önceden kurulu mu? | Büyük ölçüde evet | Yalnız host’ta kuruluysa | Yalnız host’ta kuruluysa |
| Reset kolay mı? | Container ve workspace volume yeniden oluştur | Workspace’e bağlı | Host/VM’e bağlı |
| Arbitrary package install için uygun mu? | Disposable ise evet | Host üzerinde daha riskli | VM dışında daha riskli |

## Önerilen seçim

Aksi için nedeniniz yoksa önce **Docker Compose** kullanın. En net safety boundary ve en kapsamlı default toolchain’i sağlar.

Workflow editor’dan başlıyor ve local launcher istiyorsanız **VS Code extension** kullanın. Bu da runtime’dır. Tek başına server’ı ChatGPT’den erişilebilir yapmaz; ChatGPT web/app için tunnel veya reverse proxy ekleyin.

Docker yoksa ancak VM, container host veya dedicated user account zaten boundary sağlıyorsa **standalone binary** kullanın.

`local-shell-mcp` development/debugging veya Python-based environment daha kolay yönetiliyorsa **`pipx` veya source install** kullanın.

Yalnız server process spawn edebilen local MCP client’lar için **stdio mode** kullanın. Public deployment değildir ve ChatGPT web/app tarafından doğrudan kullanılamaz.

## Public endpoint kuralı

ChatGPT gibi HTTP MCP client’larda MCP endpoint:

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` yalnız origin’dir:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` sonuna `/mcp` eklemeyin.

## Runtime sayfaları

- [Docker Compose](../installation/docker.md)
- [VS Code extension](../installation/vscode-extension.md)
- [Standalone binary](../installation/binary.md)
- [Python, `pipx`, and source install](../installation/python.md)
- [Stdio mode](../installation/stdio.md)

## Client sayfaları

- [ChatGPT connector](../getting-started/chatgpt-connector.md)
- [Generic MCP clients](../clients/generic-mcp.md)
- [Public HTTPS exposure](../clients/connectivity.md)
