<!-- i18n-source-sha256: 6e76d0746c53eeef3e770417742a44e122c6484afd0d91ddf6a4995387085c74 -->
# सामान्य MCP client

`local-shell-mcp` का उपयोग ChatGPT और अन्य MCP client कर सकते हैं। Client तय करता है कि HTTP से connect करना है या stdio के माध्यम से server शुरू करना है।

## HTTP MCP client

जब server पहले से चल रहा हो तब HTTP mode उपयोग करें:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode mcp
```

Local endpoint:

```text
http://127.0.0.1:8765/mcp
```

Network endpoint:

```text
https://your-public-host.example.com/mcp
```

Trusted localhost से बाहर पहुँच योग्य किसी भी endpoint के लिए OAuth उपयोग करें।

## Stdio MCP client

जब client स्वयं server process शुरू करता हो तब stdio mode उपयोग करें:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

सामान्य client configuration का रूप:

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

Client schemas अलग-अलग होते हैं। कुछ इस section को `mcpServers` कहते हैं; अन्य कोई दूसरा नाम उपयोग करते हैं।

## पहली सुरक्षित जाँच

नए जुड़े client पर इससे शुरू करें:

```text
Call environment_get, then file_tree on the workspace root. Do not modify files yet.
```

इसके बाद स्पष्ट edit, test और Git नियमों के साथ सीमित task चलाएँ।
