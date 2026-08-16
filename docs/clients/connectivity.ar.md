<!-- i18n-source-sha256: 3986da6ff877609189b0d88d363aff1f5f45445f0cfe5ffa608a31929078542c -->
# الاتصال بالشبكة

تحتاج MCP client عبر HTTP الموجودة خارج الجهاز إلى HTTPS origin يمكن الوصول إليه. تتناول هذه الصفحة توجيه الشبكة، وليس اختيار runtime.

ينتهي client endpoint عادةً بـ `/mcp`:

```text
https://your-public-host.example.com/mcp
```

إعداد public base URL للخادم هو الـ origin فقط:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

لا تضف `/mcp` إلى هذا base URL.

## خيارات الاتصال

| الخيار | متى يُستخدم |
|---|---|
| Compose tunnel sidecar | Docker Compose مع profile `tunnel` المدمج |
| Tunnel خارجي | أي runtime يجب الوصول إليه من خارج الشبكة المحلية |
| Caddy | TLS تلقائي وبسيط |
| Nginx أو Nginx Proxy Manager | بنية Nginx موجودة |
| Traefik | توجيه container-native موجود |

## المسارات

مرّر الـ origin بالكامل إلى الخادم العامل. تشمل المسارات المهمة:

| المسار | الغرض |
|---|---|
| `/mcp` | MCP Streamable HTTP endpoint |
| `/healthz`, `/readyz` | فحوص الصحة |
| `/.well-known/...` | بيانات client discovery الوصفية |
| `/oauth/...` | مسار تفويض client |
| `/downloads/...` | روابط اختيارية للملفات المُنشأة |
| `/join/...`, `/remote/...` | مسار remote-worker اختياري |

## سلوك الوكيل

يجب أن يحافظ الوكيل على المسارات، ويمرر request bodies، ويدعم responses الطويلة، ويتجنب timeouts القصيرة جداً.

## الفحوص

```bash
curl -i http://127.0.0.1:8765/healthz
curl -i https://your-public-host.example.com/healthz
```

## أخطاء شائعة

| الخطأ | الإصلاح |
|---|---|
| استخدام `https://host` في ChatGPT بدلاً من `https://host/mcp` | أضف `/mcp` فقط إلى client endpoint |
| ضبط `LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://host/mcp` | اضبط الـ origin فقط |
| توجيه `/mcp` فقط | وجّه الـ origin بالكامل حتى تعمل discovery والتفويض أيضاً |
| تشغيل host runtime مع workspace واسع | استخدم workspace ضيقاً أو Docker |

## الاقتران المقترح

| Runtime | نمط الشبكة |
|---|---|
| Docker Compose على خادم | Reverse proxy موجود أو Compose tunnel profile |
| Docker Compose على جهاز منزلي | Outbound tunnel |
| VS Code extension على حاسوب محمول | Tunnel مؤقت للجلسة |
| Binary على VM | Reverse proxy على VM أو حافة الشبكة |
| خادم تطوير Python/source | عادةً localhost فقط |
| Stdio mode | لا يوجد مسار HTTP؛ استخدم MCP client محلياً |
