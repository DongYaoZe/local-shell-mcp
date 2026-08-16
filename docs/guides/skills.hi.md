<!-- i18n-source-sha256: df2b62b1f847968432f0ba0309173e5de379bc9b821789715295018f72d58cf6 -->
# Agent Skills

`local-shell-mcp` एक fixed MCP tool surface के माध्यम से reusable Markdown-based Agent Skills support करता है। Skill install या remove करने से MCP tool list नहीं बदलती, इसलिए clients को reconnect करने की आवश्यकता नहीं होती।

## Skill sources

LSM इन directories को priority order में scan करता है:

```text
1. <workspace_root>/.agents/skills/
2. <state_dir>/agent_config/skills/
3. ${XDG_CONFIG_HOME:-~/.config}/agents/skills/
```

Default workspace और state directory के साथ पहले दो paths हैं:

```text
/workspace/.agents/skills
/workspace/.local-shell-mcp/agent_config/skills
```

हर immediate child directory एक Skill है। Directory name ही Skill name है और उसमें `SKILL.md` होना चाहिए। Skill directories, `SKILL.md`, related files और related directories symlinks हो सकते हैं।

जब एक ही Skill name कई sources में हो, project source LSM-managed source पर और LSM-managed source global source पर प्राथमिकता पाता है। `skill_list` हर accepted Skill का `source`, `source_path` और पूरा ordered `skills_dirs` list report करता है।

## Fixed tools

| Tool | उद्देश्य |
|---|---|
| `skill_list` | सभी sources को rescan करके full instructions load किए बिना Skill names, descriptions, sources, entry paths, related files और non-fatal warnings list करना। |
| `skill_load` | `skill_list` से मिले exact name के लिए पूरा `SKILL.md` instructions load करना। |
| `skill_read` | `skill_load` से मिले Skill-relative path का उपयोग कर bounded related text file पढ़ना। |

Recommended flow:

```text
skill_list
  -> choose the relevant Skill
  -> skill_load(name)
  -> skill_read(name, path) only when a related file is needed
  -> follow the Skill with the existing shell, Git, browser, and remote tools
```

Disk changes अगली call पर दिखाई देते हैं। Per-Skill MCP tools register नहीं किए जाते।

## Skills CLI से installation

Project और global sources खुले `skills` CLI द्वारा उपयोग किए जाने वाले universal directories से मेल खाते हैं।

Current LSM workspace में install करें:

```bash
cd /workspace
npx skills add owner/repository --agent universal -y
```

Global install:

```bash
npx skills add owner/repository --agent universal --global -y
```

किसी specific Skill के लिए:

```bash
npx skills add XiNian-dada/Fuck_My_Shit_Mountain \
  --skill fuck-my-shit-mountain \
  --agent universal \
  -y
```

LSM-managed source direct file या Git workflows के लिए उपलब्ध रहता है:

```bash
git clone https://example.com/team/my-skill.git \
  /workspace/.local-shell-mcp/agent_config/skills/my-skill
```

CLI, Git या सामान्य filesystem operations से किए updates/removals अगली Skill call पर अपने आप pick up होते हैं।

## Validation

Registry malformed Skill names और readable `SKILL.md` के बिना directories skip करता है। File-size, Skill-count, scan-entry, related-file और path-output limits लागू रहते हैं। Directory traversal strings reject होते हैं, जबकि filesystem symlinks follow किए जाते हैं।

## REST compatibility

Optional REST surface वही merged registry expose करती है:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```
