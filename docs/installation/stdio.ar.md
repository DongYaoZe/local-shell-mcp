<!-- i18n-source-sha256: a3d2dc835f99feed33a73ae3dd880dabab04a37d7461b99f1fa49c33ba0506e1 -->
# Stdio runtime

وضع stdio مخصص لـ MCP client المحلية التي تشغّل `local-shell-mcp` كـ child process وتتواصل عبر الإدخال/الإخراج القياسي.

هذا ليس deployment HTTP عاماً. لا يمكن لـ ChatGPT web/app استخدامه مباشرة لأن ChatGPT لا يستطيع تشغيل process على جهازك.

## متى تستخدم stdio

استخدم stdio mode عندما:

- يدعم MCP client تعريفات server المعتمدة على command.
- يكون client وworkspace المتحكم به على الجهاز نفسه.
- لا تحتاج OAuth أو HTTPS عام أو reverse proxy أو tunnel.
- تريد أن يدير client ‏server lifecycle.

لا تستخدم stdio mode عندما:

- يكون client هو ChatGPT web/app.
- تحتاج عدة remote clients إلى server نفسه.
- تحتاج tokenized file downloads عبر HTTP.
- تحتاج remote-worker join routes مقدمة عبر HTTP.

## الأمر

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

عادة ما يحتوي إعداد MCP client عام على:

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

كيّف schema مع client. تسمي بعض clients هذا القسم `servers` أو `tools` أو `mcpServers` أو `contextServers`.

## اختلاف السلوك عن HTTP mode

| المجال | Stdio mode | HTTP MCP mode |
|---|---|---|
| Transport | stdin/stdout | HTTP streamable MCP endpoint |
| Endpoint | لا يوجد | `/mcp` |
| OAuth | غير مطلوب | موصى به للاستخدام العام |
| Health endpoint | لا يوجد | `/healthz`, `/readyz` |
| الاستخدام العام من ChatGPT | لا | نعم، خلف HTTPS |
| Server lifecycle | client يشغّل process | أنت تدير process/runtime |

فيما عدا ذلك تستخدم tool surface نفس server-side implementation، وفقاً لـ configuration ودعم client.

## ملاحظات الأمان

غالباً ما يعمل stdio mode مباشرة على host بنفس مستخدم MCP client. استخدم workspace root ضيقاً وتجنب الوصول الواسع إلى filesystem. أبقِ full-container mode معطلاً ما لم يكن stdio نفسه يعمل داخل container أو VM قابلة للتخلص منها.
