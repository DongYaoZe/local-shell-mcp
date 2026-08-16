<!-- i18n-source-sha256: df2b62b1f847968432f0ba0309173e5de379bc9b821789715295018f72d58cf6 -->
# Agent Skills

يدعم `local-shell-mcp` ‏Agent Skills قابلة لإعادة الاستخدام ومبنية على Markdown عبر MCP tool surface ثابتة. لا يغيّر تثبيت Skill أو إزالتها قائمة أدوات MCP أبداً، لذلك لا تحتاج clients إلى إعادة الاتصال.

## مصادر Skills

يفحص LSM المجلدات التالية حسب ترتيب الأولوية:

```text
1. <workspace_root>/.agents/skills/
2. <state_dir>/agent_config/skills/
3. ${XDG_CONFIG_HOME:-~/.config}/agents/skills/
```

مع workspace وstate directory الافتراضيين، أول مسارين هما:

```text
/workspace/.agents/skills
/workspace/.local-shell-mcp/agent_config/skills
```

كل مجلد فرعي مباشر يمثل Skill واحدة. اسم المجلد هو اسم Skill ويجب أن يوفر `SKILL.md`. يمكن أن تكون مجلدات Skill و`SKILL.md` والملفات والمجلدات المرتبطة symlinks.

عندما يظهر اسم Skill نفسه في عدة مصادر، تكون أولوية project source أعلى من LSM-managed source، وهذه أعلى من global source. يعرض `skill_list` قيمتي `source` و`source_path` لكل Skill مقبولة، إضافة إلى قائمة `skills_dirs` الكاملة والمرتبة.

## الأدوات الثابتة

| Tool | الغرض |
|---|---|
| `skill_list` | إعادة فحص جميع المصادر وعرض أسماء Skills وdescriptions وsources وentry paths والملفات المرتبطة وwarnings غير القاتلة دون تحميل التعليمات الكاملة. |
| `skill_load` | تحميل تعليمات `SKILL.md` الكاملة لاسم دقيق أعاده `skill_list`. |
| `skill_read` | قراءة ملف نصي مرتبط ومحدود باستخدام Skill-relative path أعاده `skill_load`. |

المسار الموصى به:

```text
skill_list
  -> choose the relevant Skill
  -> skill_load(name)
  -> skill_read(name, path) only when a related file is needed
  -> follow the Skill with the existing shell, Git, browser, and remote tools
```

تظهر تغييرات القرص في الاستدعاء التالي. لا يتم تسجيل أدوات MCP منفصلة لكل Skill.

## التثبيت باستخدام Skills CLI

يتطابق project source وglobal source مع المجلدات universal التي تستخدمها CLI المفتوحة `skills`.

التثبيت في LSM workspace الحالي:

```bash
cd /workspace
npx skills add owner/repository --agent universal -y
```

التثبيت global:

```bash
npx skills add owner/repository --agent universal --global -y
```

لـ Skill محددة:

```bash
npx skills add XiNian-dada/Fuck_My_Shit_Mountain \
  --skill fuck-my-shit-mountain \
  --agent universal \
  -y
```

يبقى LSM-managed source متاحاً أيضاً لـ workflows المباشرة باستخدام file أو Git:

```bash
git clone https://example.com/team/my-skill.git \
  /workspace/.local-shell-mcp/agent_config/skills/my-skill
```

يتم التقاط updates وremovals التي تجريها CLI أو Git أو عمليات filesystem العادية تلقائياً عند استدعاء Skill التالي.

## التحقق

يتخطى registry أسماء Skill غير الصالحة والمجلدات التي لا تحتوي `SKILL.md` قابلاً للقراءة. تبقى حدود file-size وSkill-count وscan-entry وrelated-file وpath-output مطبقة. تُرفض سلاسل directory traversal بينما يتم اتباع symlinks في filesystem.

## توافق REST

تعرض REST surface الاختيارية registry المدمج نفسه:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```
