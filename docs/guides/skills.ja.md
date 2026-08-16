<!-- i18n-source-sha256: df2b62b1f847968432f0ba0309173e5de379bc9b821789715295018f72d58cf6 -->
# Agent Skills

`local-shell-mcp` は、固定された MCP tool surface を通じて、再利用可能な Markdown ベースの Agent Skills をサポートします。Skill を追加または削除しても MCP ツール一覧は変化しないため、client を再接続する必要はありません。

## Skill のソース

LSM は次のディレクトリを優先順位順に走査します。

```text
1. <workspace_root>/.agents/skills/
2. <state_dir>/agent_config/skills/
3. ${XDG_CONFIG_HOME:-~/.config}/agents/skills/
```

既定の workspace と state directory では、最初の 2 つは次のパスです。

```text
/workspace/.agents/skills
/workspace/.local-shell-mcp/agent_config/skills
```

直下の各子ディレクトリが 1 つの Skill です。ディレクトリ名が Skill 名になり、`SKILL.md` を提供する必要があります。Skill directory、`SKILL.md`、関連ファイル、関連ディレクトリは symlink でも構いません。

同じ Skill 名が複数のソースに存在する場合、project source が LSM-managed source より優先され、LSM-managed source が global source より優先されます。`skill_list` は各採用 Skill の `source` と `source_path`、および完全な優先順の `skills_dirs` 一覧を返します。

## 固定ツール

| Tool | 用途 |
|---|---|
| `skill_list` | すべてのソースを再走査し、完全な instruction を読み込まずに Skill 名、description、source、entry path、related file、非致命的 warning を一覧表示します。 |
| `skill_load` | `skill_list` が返した正確な名前を使い、完全な `SKILL.md` instruction を読み込みます。 |
| `skill_read` | `skill_load` が返した Skill-relative path を使って、関連する text file を範囲制限付きで読み取ります。 |

推奨フロー：

```text
skill_list
  -> choose the relevant Skill
  -> skill_load(name)
  -> skill_read(name, path) only when a related file is needed
  -> follow the Skill with the existing shell, Git, browser, and remote tools
```

ディスク上の変更は次の呼び出しで反映されます。Skill ごとの MCP tool は登録されません。

## Skills CLI でのインストール

project source と global source は、オープンな `skills` CLI が使用する universal directory と一致しています。

現在の LSM workspace にインストール：

```bash
cd /workspace
npx skills add owner/repository --agent universal -y
```

global にインストール：

```bash
npx skills add owner/repository --agent universal --global -y
```

特定の Skill の場合：

```bash
npx skills add XiNian-dada/Fuck_My_Shit_Mountain \
  --skill fuck-my-shit-mountain \
  --agent universal \
  -y
```

LSM-managed source は、直接 file/Git workflow を使う場合にも利用できます。

```bash
git clone https://example.com/team/my-skill.git \
  /workspace/.local-shell-mcp/agent_config/skills/my-skill
```

CLI、Git、通常の filesystem operation による update/remove は、次の Skill call で自動的に反映されます。

## 検証

registry は、不正な Skill 名と、読み取り可能な `SKILL.md` を持たない directory を skip します。File-size、Skill-count、scan-entry、related-file、path-output の各 limit は引き続き適用されます。Directory traversal string は拒否され、filesystem symlink は追跡されます。

## REST 互換性

任意の REST surface でも、同じ統合 registry を公開します。

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```
