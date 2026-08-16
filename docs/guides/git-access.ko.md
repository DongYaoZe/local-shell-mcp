<!-- i18n-source-sha256: 3b7d6ab07c5d6bad2bfb22f366893819ac8de8754c7c28bcb35f24ea5695979c -->
# Git 접근

`local-shell-mcp`는 `run_shell`, `shell_start`, `job_start`를 통해 표준 Git CLI를 사용합니다. 전용 Git MCP wrapper는 의도적으로 제공하지 않습니다. CLI는 완전하고 coding agent에게 익숙하며, 모든 Git subcommand를 도구 목록에 중복 구현하지 않아도 되기 때문입니다.

## 일반 워크플로

가능하면 범위가 제한된 비대화형 명령을 사용하십시오.

```bash
git status --short --branch
git diff --stat
git diff
git add -- path/to/file
git commit -m "fix: concise description"
git push origin HEAD
```

일반적인 agent 순서:

1. `run_shell(command="git status --short --branch")`로 상태를 확인합니다.
2. 관련 파일만 읽고 수정합니다.
3. 대상 테스트를 실행합니다.
4. `run_shell(command="git diff --check && git diff")`로 변경을 검토합니다.
5. commit 또는 push 전에 `secret_scan`을 실행합니다.
6. 명시적인 Git CLI 명령으로 stage, commit, push합니다.

repository가 remote worker에 있으면 같은 shell tool에 `machine`을 사용하십시오.

## Credential

Docker deployment는 일반적인 Git credential 위치를 `/persist/credentials` 아래에 지속적으로 저장할 수 있습니다. 이 volume은 민감하게 취급하십시오. repository-scoped deploy key, 수명이 짧은 GitHub App token, 격리된 automation user를 우선 사용하고 push 전에 수동 검토를 수행하십시오.

## Commit 관리

commit을 하나의 논리 변경에 집중시키고, 생성 cache와 build artifact를 제외하며, 실행한 test를 기록하고, 관련 없는 변경을 stage하지 마십시오. reset, clean, force-push 같은 파괴적 명령은 정확한 대상을 먼저 확인하십시오.

## 문제 해결

`git push`가 실패하면 remote URL, credential persistence, branch protection, token permission을 확인하십시오. GitHub CLI가 설치되어 있다면 `gh auth status`가 유용합니다.
