<!-- i18n-source-sha256: 8b4e2e48e58e65721bf5ebf9f7b1d8aedf34d62d5a7948d36d6b9102ee1f6cc3 -->
# Runtime विकल्प और deployment model

`local-shell-mcp` में दो स्वतंत्र निर्णय हैं:

1. **Runtime**: server process कैसे चलता है और कौन-सा workspace नियंत्रित करता है।
2. **Client connection**: ChatGPT या दूसरा MCP client उस server तक कैसे पहुँचता है।

ChatGPT को deployment method न मानें। ChatGPT client है। Docker, VS Code extension, release binaries, Python installs और stdio mode runtime choices हैं।

```text
Runtime layer                      Exposure layer                 Client layer
-------------------------------    ---------------------------    ----------------------
Docker Compose                     local HTTP only                ChatGPT custom MCP
VS Code extension                  HTTPS reverse proxy/tunnel     Generic MCP client
Standalone binary                  stdio process pipe             VS Code extension UI
pipx / source checkout             remote-worker outbound join    REST-style diagnostics
```

एक सामान्य public setup:

```text
ChatGPT
  -> https://mcp.example.com/mcp
  -> reverse proxy or tunnel
  -> local-shell-mcp runtime
  -> controlled workspace
```

Local MCP client setup इससे सरल हो सकता है:

```text
Local MCP client
  -> starts local-shell-mcp --mode stdio
  -> controlled workspace
```

## Runtime choice matrix

| Runtime | सबसे उपयुक्त | Isolation boundary | Toolchain source | Public ChatGPT access | पेज |
|---|---|---|---|---|---|
| Docker Compose | अधिकांश coding-agent workloads और reproducible workspaces | Container | Project image में broad default toolchain | HTTPS proxy या tunnel जोड़ें | [Docker Compose](../installation/docker.md) |
| Docker Compose + tunnel sidecar | Cloudflare Tunnel सहित one-stack public deployment | Container | Project image | Compose `tunnel` profile में built-in | [Docker Compose](../installation/docker.md#cloudflare-tunnel-sidecar) |
| VS Code extension | Editor workspace से server start/stop | आमतौर पर host process | Host tools और configured executable | ChatGPT के लिए external HTTPS tunnel/proxy जोड़ें | [VS Code extension](../installation/vscode-extension.md) |
| Standalone binary | Host/VM जहाँ Docker उपलब्ध नहीं | Host or VM | Host tools और configured executable | HTTPS proxy या tunnel जोड़ें | [Standalone binary](../installation/binary.md) |
| `pipx` / source install | Python-native use, debugging, development | Host virtualenv or VM | Python package और host tools | HTTPS proxy या tunnel जोड़ें | [Python install](../installation/python.md) |
| Stdio mode | Local MCP clients जो process सीधे spawn करते हैं | Client process boundary | Host tools और configured executable | ChatGPT web/app में उपयोग नहीं | [Stdio mode](../installation/stdio.md) |

## Client connection matrix

| Client path | Public HTTPS चाहिए | `/mcp` उपयोग | OAuth चाहिए | Typical runtime |
|---|---:|---:|---:|---|
| ChatGPT custom MCP connector | हाँ | हाँ | Public use में हाँ | Docker, VS Code extension, binary, or Python |
| Generic local MCP client over stdio | नहीं | नहीं | नहीं | `local-shell-mcp --mode stdio` |
| Generic HTTP MCP client | localhost पर आमतौर पर नहीं; network पर हाँ | हाँ | localhost के बाहर अनुशंसित | Any HTTP runtime |
| VS Code extension helper flow | केवल जब ChatGPT connect करना हो | ChatGPT URL copy करते समय हाँ | ChatGPT के लिए अनुशंसित | VS Code-launched runtime |

देखें [ChatGPT connector](../getting-started/chatgpt-connector.md), [generic MCP clients](../clients/generic-mcp.md), [network connectivity](../clients/connectivity.md).

## हर runtime क्या नियंत्रित करता है

हर runtime वही server code चलाता है और enabled होने पर वही MCP tool families expose करता है:

- Shell और persistent shell sessions।
- Filesystem, search और patch tools।
- Git operations।
- Playwright से browser automation।
- Audit log और task-state tools।
- Tokenized file links।
- Optional remote-worker lifecycle और machine-routed tools।

फर्क abstract API में नहीं, उसके पीछे के **operating environment** में है।

| प्रश्न | Docker Compose | VS Code extension | Binary / Python |
|---|---|---|---|
| Commands कहाँ चलते हैं? | Container के अंदर | आमतौर पर host workspace पर | Host या VM process environment में |
| Default workspace? | Mounted `/workspace` | Current VS Code folder या configured path | `LOCAL_SHELL_MCP_WORKSPACE_ROOT` |
| Compilers/browsers preinstalled? | हाँ, व्यापक रूप से | केवल host पर installed | केवल host पर installed |
| Reset आसान? | Container और workspace volume फिर बनाएँ | Workspace पर निर्भर | Host/VM पर निर्भर |
| Arbitrary package installs के लिए ठीक? | हाँ, यदि disposable | Host पर अधिक जोखिम | VM के बाहर अधिक जोखिम |

## अनुशंसित चयन

कोई विशेष कारण न हो तो पहले **Docker Compose** उपयोग करें। यह सबसे स्पष्ट safety boundary और सबसे पूर्ण default toolchain देता है।

Workflow editor से शुरू हो और local launcher चाहिए तो **VS Code extension** उपयोग करें। यह भी runtime है। अपने आप server को ChatGPT से reachable नहीं बनाता; ChatGPT web/app के लिए tunnel या reverse proxy जोड़ें।

Docker उपलब्ध न हो लेकिन VM, container host या dedicated user account boundary देता हो तो **standalone binary** उपयोग करें।

`local-shell-mcp` के development/debugging या आसान Python-based environment management के लिए **`pipx` या source install** उपयोग करें।

केवल ऐसे local MCP clients के लिए **stdio mode** उपयोग करें जो server process spawn कर सकें। यह public deployment नहीं है और ChatGPT web/app से सीधे उपयोग नहीं होता।

## Public endpoint नियम

ChatGPT जैसे HTTP MCP clients के लिए MCP endpoint:

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` केवल origin है:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` में `/mcp` न जोड़ें।

## Runtime pages

- [Docker Compose](../installation/docker.md)
- [VS Code extension](../installation/vscode-extension.md)
- [Standalone binary](../installation/binary.md)
- [Python, `pipx`, and source install](../installation/python.md)
- [Stdio mode](../installation/stdio.md)

## Client pages

- [ChatGPT connector](../getting-started/chatgpt-connector.md)
- [Generic MCP clients](../clients/generic-mcp.md)
- [Public HTTPS exposure](../clients/connectivity.md)
