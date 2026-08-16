<!-- i18n-source-sha256: 91695da5acbb82a8550b150249a9b97f17470140a72b27233e2470a93305e7fb -->
# أتمتة المتصفح

تستخدم أدوات المتصفح Playwright لفحص الصفحات والتقاط الأدلة وتشغيل workflows قابلة لإعادة الإنتاج. تم إبقاء tool surface العامة صغيرة عمداً.

## الأدوات

| Tool | الغرض |
|---|---|
| `browser_session` | بدء جلسات متصفح دائمة أو عرضها أو إغلاقها أو تنظيفها، مع إمكانية إعادة استخدام profile أو storage state. |
| `browser_snapshot` | قراءة نص محدود من الصفحة وأخطاء page/network والعناصر التفاعلية ذات refs قصيرة مثل `e1`، مع إمكانية أخذ screenshot. |
| `browser_act` | تنفيذ navigation وclick وfill وselect وkey وwait وإجراءات متعددة الصفحات بصورة منظمة باستخدام snapshot refs أو CSS selectors. |
| `browser_run_script` | تشغيل Python Playwright script كامل عندما لا تكفي مجموعة الإجراءات عالية المستوى. |

تقبل جميع أدوات المتصفح وسيط `machine` اختيارياً. يجب أن تكون تبعيات المتصفح مثبتة مسبقاً على controller أو worker المحدد، ويتم التثبيت بأوامر shell عادية مثل `python -m playwright install chromium`.

## المسارات الشائعة

للعمل التفاعلي، استدعِ `browser_session(action="start", url=...)` ثم `browser_snapshot`. يعيد snapshot refs قصيرة مثل `e1` و`e2`؛ مررها مباشرة إلى `browser_act`، مثل `{"action": "click", "target": "e1"}` أو `{"action": "fill", "target": "e2", "value": "..."}`. خذ snapshot جديداً بعد navigation لأن refs العناصر مرتبطة بحالة الصفحة وليست selectors دائمة.

للفحص العادي وscreenshots، فضّل `browser_session` مع `browser_snapshot`؛ يمكن للـ snapshot إعادة نص مرئي محدود وحفظ screenshot. استخدم `browser_run_script` لتقييم JavaScript أو منطق capture/PDF مخصص أو تفاعلات لا يمثلها `browser_act`.

اجعل scripts محدودة، وحدد timeouts صريحة، واحفظ artifacts داخل workspace، وتجنب إدخال credentials ما لم تكن البيئة مخصصة للمهمة.
