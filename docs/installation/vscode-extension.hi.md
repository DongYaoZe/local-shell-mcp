<!-- i18n-source-sha256: db40797f92f76326aa62db50ac4bb293edb4248791806c2fb46477a65c3e73cc -->
# VS Code extension runtime

VS Code extension उसी `local-shell-mcp` server के लिए launcher और convenience UI है। यह runtime choice है क्योंकि current editor workspace के लिए server process शुरू करती है।

यह ChatGPT connector स्वयं नहीं है। Web/app से उपयोग पर ChatGPT अभी भी public HTTPS `/mcp` endpoint से connect करता है।

## Extension क्या करती है

Extension:

- Current VS Code workspace के लिए `local-shell-mcp` शुरू करती है।
- Server stop और restart करती है।
- VS Code output channel में server output दिखाती है।
- `/healthz` check करती है।
- MCP URL copy करती है।
- Workspace और endpoint वाला ChatGPT setup prompt copy करती है।

Extension server binary bundle नहीं करती। `local-shell-mcp` अलग install करें और यदि `PATH` में नहीं है तो extension को executable path दें।

## कब उपयोग करें

यह runtime उपयोग करें जब:

- आप आमतौर पर VS Code folder से काम शुरू करते हैं।
- Manual terminal command के बजाय button/command-palette flow चाहते हैं।
- Project dependencies host पर पहले से installed हैं।
- Trusted repositories या narrow workspace पर काम करते हैं।
- Model को केवल वही workspace expose करने में सहज हैं।

Docker उपयोग करें जब:

- Repository untrusted है।
- Task arbitrary packages install करेगा।
- Broad preinstalled toolchain चाहिए।
- Container recreate करके आसान reset चाहिए।
- Host account से साफ boundary चाहिए।

## Executable install करें

एक server install method चुनें:

```bash
pipx install local-shell-mcp
```

या OS का release binary download करके `PATH` में रखें।

फिर VSIX release asset install करें:

```bash
code --install-extension local-shell-mcp-<version>.vsix
```

वैकल्पिक रूप से command palette में **Extensions: Install from VSIX...** उपयोग करें।

## Extension settings

| Setting | Purpose | Typical value |
|---|---|---|
| `local-shell-mcp.executablePath` | Server executable path | `local-shell-mcp` or an absolute binary path |
| `local-shell-mcp.host` | Local server bind address | `127.0.0.1` for local-only, `0.0.0.0` only behind a controlled network/proxy |
| `local-shell-mcp.port` | Local server port | `8765` |
| `local-shell-mcp.workspaceRoot` | MCP को exposed workspace | पहले VS Code folder के लिए empty या explicit path |
| `local-shell-mcp.authMode` | Authentication mode | `oauth` for ChatGPT, `none` only for trusted localhost testing |
| `local-shell-mcp.publicBaseUrl` | Prompts और URLs में copy होने वाला public HTTPS origin | Tunnel/proxy origin such as `https://mcp.example.com` |
| `local-shell-mcp.oauthAdminPin` | OAuth authorization PIN | Public use के लिए strong random value |
| `local-shell-mcp.allowFullContainer` | Full-container behavior flag | Direct host usage में `false` रखें |
| `local-shell-mcp.extraEnv` | Server process का extra environment | केवल project-specific safe values |

## Basic flow

1. VS Code में project folder खोलें।
2. **local-shell-mcp: Start Server** चलाएँ।
3. Available हो तो **Show Server Status** या **Check Health** चलाएँ।
4. Local MCP client के लिए **Copy MCP URL** या ChatGPT के लिए **Copy ChatGPT Setup Prompt** चलाएँ।
5. Endpoint client में जोड़ें।

Local endpoint आमतौर पर:

```text
http://127.0.0.1:8765/mcp
```

यह local clients के लिए उपयोगी है लेकिन ChatGPT web/app से reachable नहीं।

## ChatGPT के साथ उपयोग

VS Code-launched server को ChatGPT से उपयोग करने के लिए local port के आगे HTTPS tunnel या reverse proxy जोड़ें।

उदाहरण:

```text
ChatGPT
  -> https://your-public-host.example.com/mcp
  -> tunnel or reverse proxy
  -> 127.0.0.1:8765 on your machine
  -> VS Code-launched local-shell-mcp process
```

Set करें:

```text
local-shell-mcp.publicBaseUrl = https://your-public-host.example.com
local-shell-mcp.authMode = oauth
local-shell-mcp.oauthAdminPin = <strong pin>
```

ChatGPT के लिए copied URL `/mcp` पर समाप्त हो:

```text
https://your-public-host.example.com/mcp
```

## Host-runtime safety

Extension आमतौर पर आपके host user के रूप में commands चलाती है। यह disposable Docker container से महत्वपूर्ण रूप से अलग है।

अनुशंसित rules:

- केवल वही repository खोलें जिसे model से control कराना है।
- `allowFullContainer` disabled रखें।
- Workspace root को home directory न बनाएँ।
- Unrelated secrets workspace में न रखें।
- Commit/push से पहले `secret_scan` उपयोग करें।
- Unfamiliar repositories या package-install-heavy tasks में Docker प्राथमिक रखें।

## Common prompt

Setup prompt copy करने के बाद read-only task से शुरू करें:

```text
local-shell-mcp उपयोग करें। पहले environment_get और workspace पर file_tree कॉल करें। अभी files संशोधित न करें।
```

फिर bounded edit करें:

```text
इस workspace का failing test ठीक करें। पहले relevant files पढ़ें, सबसे छोटा patch बनाएँ, targeted test चलाएँ और git diff दिखाएँ। मेरी स्वीकृति से पहले commit न करें।
```

## Troubleshooting

| Symptom | Check |
|---|---|
| Extension server शुरू नहीं कर पाती | `local-shell-mcp.executablePath` मौजूद हो और terminal में `--help` चले |
| ChatGPT पहुँच नहीं पाता | Local `127.0.0.1` URL public नहीं; tunnel/proxy और `publicBaseUrl` configure करें |
| Tools गलत folder expose करते हैं | `local-shell-mcp.workspaceRoot` explicit set करें |
| Restart के बाद auth fail | `extraEnv` या runtime configuration से stable OAuth admin PIN और JWT secret set करें |
| Commands में dependencies नहीं | Host पर dependencies install करें या Docker runtime पर जाएँ |
