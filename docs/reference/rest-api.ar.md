<!-- i18n-source-sha256: 87dd7fb66311534dcd5a7217bba8c809f71fe6189e8c39b3e265da923cc82d22 -->
# REST API

الواجهة الأساسية هي MCP على `/mcp`. تتوفر أيضًا REST surface لفحوصات الصحة وروابط الملفات وبعض عمليات الخدمة.

## الصحة

```http
GET /healthz
```

يعيد حالة صحة الخادم ومعلومات الحالة الأساسية.

## MCP

```http
POST /mcp
```

نقطة Streamable HTTP MCP endpoint يستخدمها ChatGPT وغيره من MCP client.

## استدعاءات الأدوات عبر REST

تستخدم استدعاءات أدوات REST envelopes موحّدة للنجاح والأخطاء. تعيد أخطاء التحقق payloads منظمة تحتوي `ok: false` بدلاً من استثناءات framework الخام.

## Agent Skills

يتوفر سجل Skills الثابت أيضاً عبر REST:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```

تظهر تغييرات مجلدات Skill في الاستدعاء التالي ولا تغيّر قائمة أدوات MCP.

## روابط الملفات

يقدّم تطبيق HTTP المدمج تنزيلات الملفات المرمّزة. الروابط هي bearer URL مع TTL وحد أقصى اختياري لعدد التنزيلات ودعم الإلغاء.

## المصادقة

ينبغي استخدام OAuth في عمليات النشر العامة. يمكن تفعيل localhost bypass للتطوير، لكن الوصول العام دون مصادقة غير آمن.
