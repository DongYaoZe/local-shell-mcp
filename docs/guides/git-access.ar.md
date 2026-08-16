<!-- i18n-source-sha256: 3b7d6ab07c5d6bad2bfb22f366893819ac8de8754c7c28bcb35f24ea5695979c -->
# الوصول إلى Git

يستخدم `local-shell-mcp` واجهة Git CLI القياسية عبر `run_shell` أو `shell_start` أو `job_start`. لا يتم كشف Git MCP wrappers مخصصة عمداً: فالـ CLI كامل ومألوف لـ coding agents ويجنب تكرار كل أمر فرعي من Git في قائمة الأدوات.

## workflow شائع

استخدم أوامر محدودة وغير تفاعلية متى أمكن:

```bash
git status --short --branch
git diff --stat
git diff
git add -- path/to/file
git commit -m "fix: concise description"
git push origin HEAD
```

تسلسل agent نموذجي:

1. الفحص باستخدام `run_shell(command="git status --short --branch")`.
2. قراءة وتعديل الملفات ذات الصلة فقط.
3. تشغيل الاختبارات المستهدفة.
4. المراجعة باستخدام `run_shell(command="git diff --check && git diff")`.
5. تشغيل `secret_scan` قبل commit أو push.
6. تنفيذ stage وcommit وpush بأوامر Git CLI صريحة.

استخدم `machine` في shell tool نفسه عندما يكون repository على remote worker.

## بيانات الاعتماد

يمكن لـ Docker deployments حفظ مواقع Git credentials الشائعة تحت `/persist/credentials`. تعامل مع هذا volume على أنه حساس. فضّل deploy keys محدودة بالـ repository، وGitHub App tokens قصيرة العمر، ومستخدمي automation معزولين، ومراجعة يدوية قبل push.

## نظافة commits

اجعل commits مركزة، واستبعد caches المولدة وbuild artifacts، وسجّل الاختبارات التي تم تشغيلها، وتجنب stage لتغييرات غير مرتبطة. بالنسبة لأوامر مدمرة مثل reset أو clean أو force-push، افحص الهدف الدقيق أولاً.

## استكشاف الأخطاء

عند فشل `git push`، افحص remote URL واستمرارية credentials وbranch protection وصلاحيات token. يكون `gh auth status` مفيداً عند تثبيت GitHub CLI.
