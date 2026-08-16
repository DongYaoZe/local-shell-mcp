<!-- i18n-source-sha256: db40797f92f76326aa62db50ac4bb293edb4248791806c2fb46477a65c3e73cc -->
# Runtime لإضافة VS Code

إضافة VS Code هي launcher وواجهة convenience لنفس خادم `local-shell-mcp`. وهي اختيار runtime لأنها تشغّل عملية الخادم للـ workspace الحالي في editor.

وليست هي ChatGPT connector نفسه. عند الاستخدام من web/app يظل ChatGPT يتصل بـ public HTTPS endpoint `/mcp`.

## ما الذي تفعله الإضافة

تقوم الإضافة بما يلي:

- تشغّل `local-shell-mcp` للـ VS Code workspace الحالي.
- توقف الخادم وتعيد تشغيله.
- تعرض server output في VS Code output channel.
- تفحص `/healthz`.
- تنسخ MCP URL.
- تنسخ ChatGPT setup prompt يتضمن workspace وendpoint.

لا تتضمن الإضافة server binary. ثبّت `local-shell-mcp` منفصلًا ثم وجّه الإضافة إلى executable إذا لم يكن في `PATH`.

## متى تستخدمها

استخدم هذا runtime عندما:

- تبدأ العمل عادة من مجلد VS Code.
- تريد button/command-palette flow بدل تشغيل terminal command يدويًا.
- Project dependencies مثبتة بالفعل على host.
- تعمل على repositories موثوقة أو workspace ضيق.
- تقبل عرض ذلك workspace وحده للنموذج.

استخدم Docker عندما:

- يكون repository غير موثوق.
- ستثبّت المهمة packages عشوائية.
- تحتاج toolchain واسعًا مثبتًا مسبقًا.
- تريد reset سهلًا عبر إعادة إنشاء container.
- تريد boundary أوضح من حساب host.

## تثبيت Executable

اختر طريقة واحدة لتثبيت server:

```bash
pipx install local-shell-mcp
```

أو نزّل release binary لنظامك وضعه في `PATH`.

ثم ثبّت VSIX release asset:

```bash
code --install-extension local-shell-mcp-<version>.vsix
```

أو استخدم **Extensions: Install from VSIX...** في command palette.

## إعدادات الإضافة

| Setting | الغرض | القيمة النموذجية |
|---|---|---|
| `local-shell-mcp.executablePath` | Path إلى server executable | `local-shell-mcp` or an absolute binary path |
| `local-shell-mcp.host` | Bind address للـ local server | `127.0.0.1` for local-only, `0.0.0.0` only behind a controlled network/proxy |
| `local-shell-mcp.port` | Local server port | `8765` |
| `local-shell-mcp.workspaceRoot` | Workspace المعروض لـ MCP | فارغ لأول VS Code folder أو path صريح |
| `local-shell-mcp.authMode` | Authentication mode | `oauth` for ChatGPT, `none` only for trusted localhost testing |
| `local-shell-mcp.publicBaseUrl` | Public HTTPS origin المنسوخ إلى prompts وURLs | Tunnel/proxy origin such as `https://mcp.example.com` |
| `local-shell-mcp.oauthAdminPin` | PIN لـ OAuth authorization | Strong random value للاستخدام العام |
| `local-shell-mcp.allowFullContainer` | Full-container behavior flag | أبقِ `false` عند direct host usage |
| `local-shell-mcp.extraEnv` | Extra environment لعملية server | Project-specific safe values فقط |

## الخطوات الأساسية

1. افتح project folder في VS Code.
2. شغّل **local-shell-mcp: Start Server**.
3. شغّل **Show Server Status** أو **Check Health** إذا كان متاحًا.
4. استخدم **Copy MCP URL** لـ client محلي أو **Copy ChatGPT Setup Prompt** لـ ChatGPT.
5. أضف endpoint إلى client.

Local endpoint يكون عادة:

```text
http://127.0.0.1:8765/mcp
```

يفيد clients المحليين لكنه غير قابل للوصول من ChatGPT web/app.

## الاستخدام مع ChatGPT

لاستخدام server مشغّل من VS Code مع ChatGPT، أضف HTTPS tunnel أو reverse proxy أمام local port.

شكل المثال:

```text
ChatGPT
  -> https://your-public-host.example.com/mcp
  -> tunnel or reverse proxy
  -> 127.0.0.1:8765 on your machine
  -> VS Code-launched local-shell-mcp process
```

اضبط:

```text
local-shell-mcp.publicBaseUrl = https://your-public-host.example.com
local-shell-mcp.authMode = oauth
local-shell-mcp.oauthAdminPin = <strong pin>
```

URL المنسوخ لـ ChatGPT يجب أن ينتهي بـ `/mcp`:

```text
https://your-public-host.example.com/mcp
```

## أمان Host runtime

تشغّل الإضافة commands عادة بصلاحيات host user. وهذا يختلف جوهريًا عن disposable Docker container.

قواعد موصى بها:

- افتح فقط repository الذي تريد أن يتحكم فيه النموذج.
- أبقِ `allowFullContainer` معطلًا.
- لا تجعل workspace root هو home directory.
- لا تحتفظ بـ secrets غير مرتبطة في workspace.
- استخدم `secret_scan` قبل commit وpush.
- فضّل Docker لـ repositories غير المألوفة أو tasks الثقيلة في تثبيت packages.

## Prompt شائع

بعد نسخ setup prompt ابدأ بمهمة read-only:

```text
استخدم local-shell-mcp. استدعِ environment_get وfile_tree على workspace أولًا. لا تعدّل الملفات بعد.
```

ثم انتقل إلى edit محدود:

```text
أصلح failing test في هذا workspace. اقرأ الملفات ذات الصلة أولًا، أنشئ أصغر patch، شغّل الاختبار المستهدف واعرض git diff. لا تنشئ commit حتى أوافق.
```

## استكشاف الأخطاء

| العَرَض | التحقق |
|---|---|
| الإضافة لا تستطيع تشغيل server | تأكد من وجود `local-shell-mcp.executablePath` وأن `--help` يعمل في terminal |
| ChatGPT لا يستطيع الوصول إليه | Local `127.0.0.1` URL ليس عامًا؛ اضبط tunnel/proxy و`publicBaseUrl` |
| Tools تعرض folder خاطئ | اضبط `local-shell-mcp.workspaceRoot` صراحة |
| Auth يفشل بعد restart | اضبط OAuth admin PIN وJWT secret ثابتين عبر `extraEnv` أو runtime configuration |
| Commands تفتقد dependencies | ثبّت dependencies على host أو انتقل إلى Docker runtime |
