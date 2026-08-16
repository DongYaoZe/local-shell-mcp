<!-- i18n-source-sha256: df2b62b1f847968432f0ba0309173e5de379bc9b821789715295018f72d58cf6 -->
# Agent Skills

`local-shell-mcp`는 고정된 MCP tool surface를 통해 재사용 가능한 Markdown 기반 Agent Skills를 지원합니다. Skill을 설치하거나 제거해도 MCP 도구 목록은 변하지 않으므로 client를 다시 연결할 필요가 없습니다.

## Skill 소스

LSM은 다음 디렉터리를 우선순위 순으로 스캔합니다.

```text
1. <workspace_root>/.agents/skills/
2. <state_dir>/agent_config/skills/
3. ${XDG_CONFIG_HOME:-~/.config}/agents/skills/
```

기본 workspace와 state directory를 사용할 때 처음 두 경로는 다음과 같습니다.

```text
/workspace/.agents/skills
/workspace/.local-shell-mcp/agent_config/skills
```

각 바로 아래 child directory가 하나의 Skill입니다. Directory 이름이 Skill 이름이며 `SKILL.md`를 제공해야 합니다. Skill directory, `SKILL.md`, related file 및 related directory는 symlink일 수 있습니다.

같은 Skill 이름이 여러 source에 있으면 project source가 LSM-managed source보다 우선하고, LSM-managed source가 global source보다 우선합니다. `skill_list`는 채택된 각 Skill의 `source`, `source_path`와 전체 우선순위 `skills_dirs` 목록을 보고합니다.

## 고정 도구

| Tool | 용도 |
|---|---|
| `skill_list` | 모든 source를 다시 스캔하고 전체 instruction을 로드하지 않은 채 Skill 이름, description, source, entry path, related file 및 치명적이지 않은 warning을 나열합니다. |
| `skill_load` | `skill_list`가 반환한 정확한 이름으로 전체 `SKILL.md` instruction을 로드합니다. |
| `skill_read` | `skill_load`가 반환한 Skill-relative path를 사용해 related text file 하나를 범위 제한으로 읽습니다. |

권장 흐름:

```text
skill_list
  -> choose the relevant Skill
  -> skill_load(name)
  -> skill_read(name, path) only when a related file is needed
  -> follow the Skill with the existing shell, Git, browser, and remote tools
```

디스크 변경은 다음 호출에서 반영됩니다. Skill별 MCP tool은 등록되지 않습니다.

## Skills CLI로 설치

project 및 global source는 공개 `skills` CLI가 사용하는 universal directory와 일치합니다.

현재 LSM workspace에 설치:

```bash
cd /workspace
npx skills add owner/repository --agent universal -y
```

global 설치:

```bash
npx skills add owner/repository --agent universal --global -y
```

특정 Skill 설치:

```bash
npx skills add XiNian-dada/Fuck_My_Shit_Mountain \
  --skill fuck-my-shit-mountain \
  --agent universal \
  -y
```

LSM-managed source는 직접 file/Git workflow에서도 사용할 수 있습니다.

```bash
git clone https://example.com/team/my-skill.git \
  /workspace/.local-shell-mcp/agent_config/skills/my-skill
```

CLI, Git 또는 일반 filesystem operation으로 수행한 update/remove는 다음 Skill call에서 자동으로 반영됩니다.

## 검증

registry는 잘못된 Skill 이름과 읽을 수 있는 `SKILL.md`가 없는 directory를 건너뜁니다. File-size, Skill-count, scan-entry, related-file, path-output limit은 계속 적용됩니다. Directory traversal string은 거부되고 filesystem symlink는 따라갑니다.

## REST 호환성

선택적 REST surface도 동일한 병합 registry를 제공합니다.

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```
