<!-- i18n-source-sha256: a3d2dc835f99feed33a73ae3dd880dabab04a37d7461b99f1fa49c33ba0506e1 -->
# Stdio runtime

Stdio mode उन local MCP client के लिए है जो `local-shell-mcp` को child process के रूप में शुरू करते हैं और standard input/output पर communicate करते हैं।

यह public HTTP deployment नहीं है। ChatGPT web/app इसे सीधे उपयोग नहीं कर सकता क्योंकि ChatGPT आपकी machine पर process spawn नहीं कर सकता।

## stdio कब उपयोग करें

Stdio mode उपयोग करें जब:

- आपका MCP client command-based server definitions support करता हो।
- Client और controlled workspace एक ही machine पर हों।
- OAuth, public HTTPS, reverse proxies या tunnels की आवश्यकता न हो।
- आप चाहते हों कि client server lifecycle manage करे।

Stdio mode उपयोग न करें जब:

- Client ChatGPT web/app हो।
- कई remote clients को वही server चाहिए।
- HTTP पर tokenized file downloads चाहिए।
- HTTP पर served remote-worker join routes चाहिए।

## Command

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

एक generic MCP client configuration में सामान्यतः यह होता है:

```json
{
  "mcpServers": {
    "local-shell-mcp": {
      "command": "local-shell-mcp",
      "args": ["--mode", "stdio"],
      "env": {
        "LOCAL_SHELL_MCP_WORKSPACE_ROOT": "/path/to/workspace"
      }
    }
  }
}
```

Schema को अपने client के अनुसार adapt करें। कुछ clients इस section को `servers`, `tools`, `mcpServers` या `contextServers` कहते हैं।

## HTTP mode से behavior differences

| Area | Stdio mode | HTTP MCP mode |
|---|---|---|
| Transport | stdin/stdout | HTTP streamable MCP endpoint |
| Endpoint | None | `/mcp` |
| OAuth | आवश्यक नहीं | Public use के लिए recommended |
| Health endpoint | None | `/healthz`, `/readyz` |
| Public ChatGPT use | No | Yes, HTTPS के पीछे |
| Server lifecycle | Client process launch करता है | आप process/runtime manage करते हैं |

अन्यथा tool surface वही server-side implementation उपयोग करती है, configuration और client support के अधीन।

## Safety notes

Stdio mode अक्सर host पर सीधे उसी user के रूप में चलता है जो MCP client चला रहा है। Narrow workspace root उपयोग करें और broad filesystem access से बचें। Full-container mode disabled रखें, जब तक stdio स्वयं disposable container या VM के भीतर न चल रहा हो।
