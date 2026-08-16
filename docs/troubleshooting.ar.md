<!-- i18n-source-sha256: ed71ed496e65545264c76f97a154e8e0758faf58be0ba74c24c82f3b860ff4f2 -->
# استكشاف الأخطاء وإصلاحها

تحقق من صحة الخدمة:

```bash
curl -i http://127.0.0.1:8765/healthz
```

تحقق من السجلات:

```bash
docker compose logs --tail=100 local-shell-mcp
```

إذا تعذّر على ChatGPT الاتصال، فتحقق من أن `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` يطابق تماماً HTTPS origin العام، وأن `/mcp` وبيانات OAuth الوصفية و`/healthz` يمكن الوصول إليها عبر tunnel أو الوكيل العكسي.

إذا لم تظهر workers البعيدة، فتأكد من تفعيل وضع remote، ومن أن الدعوة لم تنتهِ صلاحيتها، وأن الجهاز البعيد يستطيع إرسال طلبات HTTPS صادرة إلى خادم التحكم.
