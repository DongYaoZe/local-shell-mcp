<!-- i18n-source-sha256: d758caead1c922385409aceebf498662f25f4cbf252a48d65b29d91f07e5a173 -->
# روابط الملفات

يمكن لـ `local-shell-mcp` كشف ملفات من workspace المتحكم به عبر bearer URL عالية العشوائية. يفيد ذلك عندما ينشئ الذكاء الاصطناعي تقارير أو أرشيفات أو PDF أو screenshots أو artifacts أخرى يجب تنزيلها من المحادثة أو عرضها فيها.

## متى تستخدم روابط الملفات

استخدم روابط الملفات من أجل:

- ملفات PDF أو تقارير مُنشأة.
- Screenshots وbrowser artifacts.
- مخرجات build.
- Logs أكبر من أن تُلصق في المحادثة.
- أرشيفات معدّة للفحص اليدوي.

لا تستخدم روابط الملفات مع secrets أو private keys أو مخازن credentials أو بيانات شخصية غير مرتبطة بالمهمة.

## المسار المعتاد

1. أنشئ ملفاً أو اعثر عليه تحت `/workspace`.
2. استدعِ `link_create` مع TTL وحد اختياري للتنزيل. اضبط `inline=true` عندما ينبغي عرض الملف مباشرة في المتصفح أو كصورة Markdown؛ القيمة الافتراضية هي `false` وتفرض attachment download.
3. شارك URL المعاد.
4. ألغِ الرابط عندما لا يعود مطلوباً.

## الأدوات ذات الصلة

| Tool | الغرض |
|---|---|
| `link_create` | إنشاء URL مرمّز لملف workspace. |
| `link_list` | عرض الروابط النشطة. |
| `link_revoke` | تعطيل رابط قبل انتهاء صلاحيته. |

## عناصر التحكم

تشمل خيارات الإعداد:

- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_ENABLED`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_MAX_DOWNLOADS`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_FILE_BYTES`

استخدم TTL أقصر مع artifacts الحساسة واضبط maximum download count عندما يكون الرابط مخصصاً لمستلم واحد.

## ملاحظات الأمان

روابط الملفات هي bearer URL. يمكن لأي شخص يملك URL تنزيل الملف حتى تنتهي صلاحيته أو يصل إلى download limit أو يتم إلغاؤه. تعامل معها كـ secrets مؤقتة. تتضمن inline responses ‏CSP sandbox و`X-Content-Type-Options: nosniff` حتى لا تتمكن التنسيقات النشطة من الوصول إلى LSM origin أو التنفيذ كمحتوى same-origin غير معزول.
