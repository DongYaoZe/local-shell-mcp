<!-- i18n-source-sha256: 6e76d0746c53eeef3e770417742a44e122c6484afd0d91ddf6a4995387085c74 -->
# MCP client عامة

يمكن استخدام `local-shell-mcp` من ChatGPT ومن MCP client أخرى. يقرر الـ client ما إذا كان سيتصل عبر HTTP أو سيشغّل الخادم عبر stdio.

## MCP client عبر HTTP

استخدم HTTP mode عندما يكون الخادم قيد التشغيل بالفعل:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode mcp
```

Endpoint محلي:

```text
http://127.0.0.1:8765/mcp
```

Endpoint على الشبكة:

```text
https://your-public-host.example.com/mcp
```

استخدم OAuth لأي endpoint يمكن الوصول إليه خارج localhost الموثوق.

## MCP client عبر stdio

استخدم stdio mode عندما يشغّل الـ client عملية الخادم بنفسه:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

شكل نموذجي لإعداد client:

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

تختلف schemas بين clients. يسمي بعضها هذا القسم `mcpServers` بينما يستخدم بعضها اسماً آخر.

## أول فحص آمن

ابدأ مع client جديد الاتصال بما يلي:

```text
Call environment_get, then file_tree on the workspace root. Do not modify files yet.
```

ثم نفّذ مهمة محدودة بقواعد واضحة للتحرير والاختبارات وGit.
