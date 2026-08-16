<!-- i18n-source-sha256: 8b4e2e48e58e65721bf5ebf9f7b1d8aedf34d62d5a7948d36d6b9102ee1f6cc3 -->
# خيارات Runtime ونموذج النشر

لدى `local-shell-mcp` قراران مستقلان:

1. **Runtime**: كيفية تشغيل عملية الخادم وما الـ workspace الذي تتحكم فيه.
2. **Client connection**: كيفية وصول ChatGPT أو أي MCP client آخر إلى ذلك الخادم.

لا تعتبر ChatGPT طريقة نشر. ChatGPT هو client. Docker وVS Code extension وrelease binaries وتثبيتات Python وstdio mode هي خيارات runtime.

```text
Runtime layer                      Exposure layer                 Client layer
-------------------------------    ---------------------------    ----------------------
Docker Compose                     local HTTP only                ChatGPT custom MCP
VS Code extension                  HTTPS reverse proxy/tunnel     Generic MCP client
Standalone binary                  stdio process pipe             VS Code extension UI
pipx / source checkout             remote-worker outbound join    REST-style diagnostics
```

إعداد عام شائع:

```text
ChatGPT
  -> https://mcp.example.com/mcp
  -> reverse proxy or tunnel
  -> local-shell-mcp runtime
  -> controlled workspace
```

يمكن أن يكون إعداد MCP client محلي أبسط:

```text
Local MCP client
  -> starts local-shell-mcp --mode stdio
  -> controlled workspace
```

## مصفوفة اختيار Runtime

| Runtime | الأنسب لـ | حد العزل | مصدر toolchain | وصول ChatGPT العام | الصفحة |
|---|---|---|---|---|---|
| Docker Compose | معظم أعباء coding-agent وworkspaces القابلة لإعادة الإنتاج | Container | Project image يتضمن toolchain افتراضيًا واسعًا | أضف HTTPS proxy أو tunnel | [Docker Compose](../installation/docker.md) |
| Docker Compose + tunnel sidecar | نشر عام في stack واحدة مع Cloudflare Tunnel | Container | Project image | مدمج في profile Compose `tunnel` | [Docker Compose](../installation/docker.md#cloudflare-tunnel-sidecar) |
| VS Code extension | بدء/إيقاف server من editor workspace | عادة process على host | أدوات host مع executable مضبوط | أضف HTTPS tunnel/proxy خارجيًا لـ ChatGPT | [VS Code extension](../installation/vscode-extension.md) |
| Standalone binary | Hosts أو VM بدون Docker | Host or VM | أدوات host مع executable مضبوط | أضف HTTPS proxy أو tunnel | [Standalone binary](../installation/binary.md) |
| `pipx` / source install | استخدام Python-native وdebugging وdevelopment | Host virtualenv or VM | Python package مع أدوات host | أضف HTTPS proxy أو tunnel | [Python install](../installation/python.md) |
| Stdio mode | MCP clients محليون يشغّلون العمليات مباشرة | Client process boundary | أدوات host مع executable مضبوط | غير قابل للاستخدام مع ChatGPT web/app | [Stdio mode](../installation/stdio.md) |

## مصفوفة اتصال Client

| مسار Client | يتطلب HTTPS عامًا | يستخدم `/mcp` | يتطلب OAuth | Runtime نموذجي |
|---|---:|---:|---:|---|
| ChatGPT custom MCP connector | نعم | نعم | نعم للاستخدام العام | Docker, VS Code extension, binary, or Python |
| Generic local MCP client over stdio | لا | لا | لا | `local-shell-mcp --mode stdio` |
| Generic HTTP MCP client | غالبًا لا على localhost؛ نعم عبر الشبكات | نعم | موصى به خارج localhost | Any HTTP runtime |
| VS Code extension helper flow | فقط إذا كان ChatGPT سيتصل | نعم عند نسخ ChatGPT URL | موصى به لـ ChatGPT | VS Code-launched runtime |

راجع [ChatGPT connector](../getting-started/chatgpt-connector.md), [generic MCP clients](../clients/generic-mcp.md), [network connectivity](../clients/connectivity.md).

## ما الذي يتحكم فيه كل Runtime

يشغّل كل runtime نفس server code ويعرض عائلات MCP tools نفسها عند تفعيلها:

- Shell وpersistent shell sessions.
- Filesystem وsearch وpatch tools.
- عمليات Git.
- Browser automation عبر Playwright.
- Audit log وtask-state tools.
- Tokenized file links.
- Optional remote-worker lifecycle وmachine-routed tools.

الاختلاف ليس في API المجردة بل في **operating environment** خلفها.

| السؤال | Docker Compose | VS Code extension | Binary / Python |
|---|---|---|---|
| أين تعمل الأوامر؟ | داخل container | عادة في host workspace | في process environment على host أو VM |
| Default workspace؟ | Mounted `/workspace` | مجلد VS Code الحالي أو path مضبوط | `LOCAL_SHELL_MCP_WORKSPACE_ROOT` |
| هل compilers/browsers مثبّتة؟ | نعم، على نطاق واسع | فقط ما هو مثبت على host | فقط ما هو مثبت على host |
| هل reset سهل؟ | أعد إنشاء container وworkspace volume | يعتمد على workspace | يعتمد على host/VM |
| مناسب لتثبيت packages عشوائية؟ | نعم إذا كان disposable | أكثر خطورة على host | أكثر خطورة خارج VM |

## الاختيار الموصى به

استخدم **Docker Compose** أولًا ما لم يكن لديك سبب يمنع ذلك. فهو يوفر أوضح safety boundary وأكمل toolchain افتراضي.

استخدم **VS Code extension** عندما يبدأ workflow من editor وتريد launcher محليًا. وهو يظل runtime. لا يجعل server قابلًا للوصول من ChatGPT بمفرده؛ أضف tunnel أو reverse proxy لـ ChatGPT web/app.

استخدم **standalone binary** عندما لا يتوفر Docker لكن VM أو container host أو dedicated user account يوفر boundary بالفعل.

استخدم **`pipx` أو source install** لتطوير/debugging `local-shell-mcp` نفسه أو عندما تكون بيئة Python أسهل في الإدارة.

استخدم **stdio mode** فقط مع MCP clients محليين يمكنهم spawn server process. فهو ليس public deployment ولا يستخدم مباشرة من ChatGPT web/app.

## قاعدة Public endpoint

لعملاء HTTP MCP مثل ChatGPT يكون MCP endpoint:

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` هو origin فقط:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

لا تضف `/mcp` إلى `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## صفحات Runtime

- [Docker Compose](../installation/docker.md)
- [VS Code extension](../installation/vscode-extension.md)
- [Standalone binary](../installation/binary.md)
- [Python, `pipx`, and source install](../installation/python.md)
- [Stdio mode](../installation/stdio.md)

## صفحات Client

- [ChatGPT connector](../getting-started/chatgpt-connector.md)
- [Generic MCP clients](../clients/generic-mcp.md)
- [Public HTTPS exposure](../clients/connectivity.md)
