<!-- i18n-source-sha256: 3b7d6ab07c5d6bad2bfb22f366893819ac8de8754c7c28bcb35f24ea5695979c -->
# Git access

`local-shell-mcp` `run_shell`, `shell_start` या `job_start` के माध्यम से standard Git CLI उपयोग करता है। Dedicated Git MCP wrappers जानबूझकर expose नहीं किए जाते: CLI पूर्ण है, coding agents को परिचित है और tool list में हर Git subcommand की नकल करने से बचाता है।

## सामान्य workflow

जहाँ संभव हो bounded, non-interactive commands उपयोग करें:

```bash
git status --short --branch
git diff --stat
git diff
git add -- path/to/file
git commit -m "fix: concise description"
git push origin HEAD
```

एक सामान्य agent sequence:

1. `run_shell(command="git status --short --branch")` से inspect करें।
2. केवल संबंधित files पढ़ें और edit करें।
3. Targeted tests चलाएँ।
4. `run_shell(command="git diff --check && git diff")` से review करें।
5. Commit या push से पहले `secret_scan` चलाएँ।
6. Explicit Git CLI commands से stage, commit और push करें।

जब repository remote worker पर हो तो उसी shell tool में `machine` उपयोग करें।

## Credentials

Docker deployments `/persist/credentials` के नीचे सामान्य Git credential locations persist कर सकते हैं। इस volume को sensitive मानें। Repository-scoped deploy keys, short-lived GitHub App tokens, isolated automation users और push से पहले manual review को प्राथमिकता दें।

## Commit hygiene

Commits को focused रखें, generated caches और build artifacts हटाएँ, चलाए गए tests दर्ज करें और unrelated changes stage न करें। Reset, clean या force-push जैसे destructive commands के लिए पहले exact target inspect करें।

## Troubleshooting

`git push` fail होने पर remote URL, credential persistence, branch protection और token permissions जाँचें। GitHub CLI installed हो तो `gh auth status` उपयोगी है।
