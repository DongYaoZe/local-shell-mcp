<!-- i18n-source-sha256: 2ad041876ff35987d7fdd66cbcdc7ed3956f427e8d8b185f354555cdc29a1b8a -->
# موصل ChatGPT

تتناول هذه الصفحة ChatGPT بوصفه اتصال client. وهي لا تختار runtime. قبل استخدامها شغّل الخادم باستخدام Docker أو VS Code extension أو binary أو تثبيت Python.

صُمم `local-shell-mcp` لـ ChatGPT Developer Mode وعملاء MCP الكاملين. يعرض MCP endpoint مجموعة أدوات LSM العادية مباشرة.

## متطلبات runtime

اختر runtime واحدًا وشغّله أولًا:

| Runtime | الصفحة |
|---|---|
| Docker Compose | [Docker Compose runtime](../installation/docker.md) |
| VS Code extension | [VS Code extension runtime](../installation/vscode-extension.md) |
| Standalone binary | [Standalone binary runtime](../installation/binary.md) |
| Python / pipx / source | [Python runtimes](../installation/python.md) |

ثم أتح هذا runtime عبر مسار شبكي يستطيع ChatGPT الوصول إليه. راجع [network connectivity](../clients/connectivity.md).

## الرابط العام

يجب أن يصل ChatGPT إلى الخادم عبر HTTPS. MCP endpoint هو:

```text
https://your-public-host.example.com/mcp
```

تأكد من أن `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` يطابق public origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

لا تضع `/mcp` داخل `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## إعداد OAuth

الإعدادات العامة الموصى بها:

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

لا تنتهي access tokens افتراضيًا لأن جلسات البرمجة الطويلة قد تتجاوز أعمار token القصيرة. عند الحاجة، ألغِ الوصول بتدوير JWT secret أو إعادة النشر بحالة جديدة.

## إضافة الموصل

1. افتح إعدادات connector أو Developer Mode MCP في ChatGPT.
2. أضف custom MCP server.
3. أدخل MCP URL: `https://your-public-host.example.com/mcp`.
4. أكمل OAuth.
5. وافق على سطح الأدوات.

## Live Workspace MCP App

يمكن لعملاء ChatGPT الذين يدعمون MCP Apps عرض `local-shell-mcp` كـ execution workspace تفاعلي. اطلب من ChatGPT فتح Live Workspace مرة واحدة عندما تكون الرؤية الفورية أو التعاون البشري مفيدين؛ ثم يعيد التطبيق الاتصال بنفسه بدل الحاجة إلى استدعاءات `workspace_open` متكررة.

يُفصل Live Workspace عمدًا عن reasoning النموذج. وهو يعرض execution state القابل للملاحظة وresources المشتركة:

- **Activity** يعرض بدء أدوات MCP واكتمالها وفشلها وإجراءات البشر.
- **Terminal** يتصل بالـ persistent shell backend الحالي ويعرض live PTY output.
- **Files** يتصفح ملفات workspace المحلية أو البعيدة ويعاينها ويحررها وينشئها ويحذفها.
- **Diff** يعرض تغييرات Git من staged وunstaged ويمكنه إرسال diff الحالي إلى ChatGPT للمراجعة.
- **Jobs** يعرض jobs المُدارة والجلسات الدائمة.
- **Remotes** يعرض workers ويوفر إجراءات الدعوة وإعادة التسمية والإلغاء عند تفعيل الدعم البعيد.
- **Audit** يعرض سجلات تدقيق MCP المنظمة الحديثة.

Live Workspace دائمًا collaborative: يمكن لـ ChatGPT والإنسان تعديل workspace نفسه بالتزامن. يفتح كنافذة PiP عائمة إذا كان host يدعم ذلك ويمكن التبديل بين fullscreen والنافذة. لا توجد حالة observe/takeover منفصلة.

يمكن لعروض files وdiff وaudit وactivity إرسال operational context محدد إلى دورة النموذج التالية عبر MCP Apps bridge. هذا context مشترك صراحة؛ ولا تكشف UI reasoning النموذج الخاص ولا تعيد بناءه.

### الشبكة والأمان

يتصل MCP App المعروض مباشرة من sandbox إلى service origin المضبوط للحصول على terminal/event traffic منخفض الكمون. لذلك يجب أن يكون `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` هو HTTPS origin الذي يستطيع متصفح ChatGPT الوصول إليه. ويبقى MCP endpoint نفسه `https://your-public-host.example.com/mcp`.

عند فتح workspace يصدر Live Workspace bearer token عشوائي قصير العمر. يظهر token فقط في MCP result metadata المخصصة للتطبيق المعروض، ولا يدخل structured content المرئي للنموذج، ولا تقبله إلا واجهات human/live UI API. إعادة الارتباط التلقائية بنفس `live_id` تعيد استخدام credential الحالية كي لا تبطل النوافذ المعاد وصلها بعضها بعضًا؛ كما تحمل `session_id` المنطقي الحالي، مما يسمح باستعادة Session الدائمة حتى لو فُقدت حالة Live Workspace في الذاكرة. يؤدي استدعاء `workspace_open` صراحة مرة أخرى إلى تدوير credential. لا يستخدم التطبيق المضمّن browser cookies أو ambient credentials.

يمكن للعملاء الذين لا يطبقون MCP Apps تجاهل UI metadata. وتبقى جميع أدوات بيانات MCP العادية متاحة بنفس السلوك.

## أول prompt

```text
استخدم local-shell-mcp. استدعِ environment_get أولًا، ثم اعرض جذر workspace. لا تعدّل الملفات بعد.
```

يتحقق ذلك من الاتصال دون إجراء تغييرات.

## قواعد التشغيل الموصى بها

أعط النموذج قيودًا واضحة:

- العمل داخل `/workspace` ما لم يُطلب غير ذلك صراحة.
- تشغيل tests قبل commit.
- استخدام `secret_scan` قبل push.
- استخدام `link_create` فقط مع الملفات الآمنة للمشاركة.
- تفضيل persistent shell sessions للعمليات الطويلة.
- تلخيص كل الأوامر التي غيّرت ملفات.

## مشكلات اكتشاف الأدوات

إذا نجح ChatGPT في المصادقة لكنه لا يعرض الأدوات المتوقعة:

- تأكد من أن endpoint ينتهي بـ `/mcp`.
- تحقق من `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY`.
- تحقق من reverse proxy headers وحدود request body.
- افحص `docker compose logs --tail=200 local-shell-mcp`.
- تأكد من أن الخدمة في mode `mcp` أو `both`.

## ملاحظات الأمان

يجب إبقاء OAuth مفعّلًا في عمليات النشر العامة. لا تعرض أدوات MCP الكاملة دون مصادقة على الإنترنت العام. اعتبر كل أداة تمت الموافقة عليها جزءًا من السلطة الفعلية للنموذج المتصل.
