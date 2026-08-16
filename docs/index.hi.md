<!-- i18n-source-sha256: b999ae6985930651e74b974b12109889360442811d6eeb306e6fa39754dbc173 -->
<div class="hero-shell" markdown>
<span class="hero-eyebrow">ChatGPT-compatible MCP control plane</span>

# local-shell-mcp

Chat छोड़े बिना अपने AI assistant को नियंत्रित shell, वास्तविक workspace, Git, browser automation, file sharing और remote-worker access दें।

<div class="hero-actions" markdown>
[शुरू करें](getting-started/quickstart.md){ .hero-action .hero-action--primary }
[Runtime चुनें](guides/deployment.md){ .hero-action .hero-action--secondary }
[Tools reference](reference/tools.md){ .hero-action .hero-action--secondary }
</div>
</div>

<div class="feature-grid" markdown>
<div class="feature-card" markdown>
### वास्तविक coding environment
एक MCP endpoint से tests चलाएँ, repositories inspect करें, files patch करें, Git operate करें और audit trail रखें।
</div>

<div class="feature-card" markdown>
### Runtime और client layers
Docker, VS Code extension, binary, Python या stdio जैसे runtime चुनें, फिर ChatGPT या अन्य MCP client अलग से connect करें।
</div>

<div class="feature-card" markdown>
### Remote machine control
SSH ports खोले बिना outbound worker connections से NAT, firewall या HPC machines जोड़ें।
</div>
</div>

## क्या प्रदान करता है

`local-shell-mcp` ChatGPT और अन्य MCP clients को नियंत्रित local/container workspace देता है। यह OAuth-सक्षम ChatGPT-compatible MCP server के जरिए shell, persistent shell, filesystem, search, patch, Git, Playwright, audit, optional Goal Plans वाली durable logical Sessions, tokenized file links और remote-worker tools देता है।

जब AI को repository inspect करना, tests चलाना, files edit करना, Git operate करना, browser evidence इकट्ठा करना, downloadable artifacts बनाना या केवल control server की ओर outbound connect कर सकने वाली remote machine को control करना हो, तब इसका उपयोग करें।

## Architecture

```text
Runtime layer: Docker / VS Code extension / binary / Python / stdio
Exposure layer: localhost / HTTPS proxy / tunnel / stdio pipe
Client layer: ChatGPT / generic MCP client / editor helper
Controlled workspace: /workspace or configured workspace root
Optional remote workers: outbound machine connections
```

इच्छित isolation boundary service चलाने वाला container या VM है।

## Scenario के अनुसार शुरुआत

| Scenario | यहाँ से शुरू करें | क्यों |
|---|---|---|
| पहला public ChatGPT deployment | [Quickstart](getting-started/quickstart.md) | OAuth और `/mcp` setup सहित Docker Compose path |
| runtime layer चुनना | [Runtime choices](guides/deployment.md) | Docker, VS Code, binary, Python और stdio को अलग runtime options के रूप में समझाता है |
| ChatGPT को client के रूप में जोड़ना | [ChatGPT connector](getting-started/chatgpt-connector.md) | Endpoint, OAuth, पहला safe prompt, tool discovery |
| LSM को DeepSeek Harness में जोड़ना | [DeepSeek Harness plugin](clients/deepseek-harness.md) | इस repository को DSH bundle के रूप में install करें और पूर्ण LSM tool/remote-worker surface बनाए रखें |
| VS Code से चलाना | [VS Code extension runtime](installation/vscode-extension.md) | Editor-launched runtime और host safety notes |
| toolset operate करना सीखना | [Usage patterns](guides/usage-patterns.md) | Prompt templates और tool-choice guidance |
| हर tool समझना | [Tools reference](reference/tools.md) | हर tool का purpose, inputs, returns, combinations और notes |
| HPC, NPU/GPU या server node जोड़ना | [Remote workers](guides/remote-workers.md) | Outbound worker join flow और remote tool usage |
| Generated files share करना | [File links](guides/file-links.md) | TTL और revocation वाले tokenized download URLs |
| Deployment harden करना | [Security](security.md) | Isolation, OAuth, workspace scope और audit logs |

## मुख्य tool families

| Family | Examples | उपयोग |
|---|---|---|
| Shell and Python | `run_shell`, `run_python`, `shell_start` | Builds, tests, scripts, long-running processes |
| Files and search | `file_tree`, `file_grep`, `file_read`, `file_patch` | Repository inspection और precise edits |
| Git | `run_shell`, `run_shell`, `run_shell`, `run_shell` | Reviewable source-control workflows |
| Sessions और goals | `session_manage`, `plan_manage` | Durable task handoff, progress reports और optional Goal mode |
| Browser | `browser_session`, `browser_snapshot`, `browser_act`, `browser_run_script` | Persistent interaction, UI checks, screenshots, rendered docs और page text |
| File links | `link_create`, `link_revoke` | Chat से generated artifacts download करना |
| Remote workers | `remote_manage`, `run_shell`, `remote_transfer` | NAT, firewalls या cluster login flows के पीछे machines |

## Typical workflows

### ChatGPT के साथ coding

1. Dedicated workspace में Docker Compose, VS Code extension, binary या Python जैसा runtime शुरू करें।
2. यदि ChatGPT को network access चाहिए तो HTTP runtime expose करें।
3. Public `/mcp` endpoint ChatGPT में जोड़ें।
4. पहले repository inspect करने और read-only checks चलाने को कहें।
5. Approval के बाद files patch, tests, diff review, commit और push करने दें।
6. File links या remote systems वाले tasks में audit log review करें।

### Remote HPC या accelerator host

1. One-time remote worker invite बनाएँ।
2. Generated command remote host पर paste करें।
3. Normal tools में `machine` उपयोग करें; Git के लिए `run_shell` और transfer के लिए `remote_transfer`।
4. Task के बाद worker revoke करें।

### Artifact generation

1. AI से `/workspace` के नीचे file generate कराएँ।
2. TTL/download limits वाला tokenized file link बनाएँ।
3. Link chat में share करें।
4. पूरा होने पर revoke करें।

## Language

यह site native MkDocs i18n plugin से build होती है। Header के language selector से English और translated pages के बीच बदलें। बिना translation वाली pages English पर fallback करती हैं।
