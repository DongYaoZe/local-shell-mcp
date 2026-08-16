<!-- i18n-source-sha256: 3b7d6ab07c5d6bad2bfb22f366893819ac8de8754c7c28bcb35f24ea5695979c -->
# Dostęp Git

`local-shell-mcp` używa standardowego Git CLI przez `run_shell`, `shell_start` lub `job_start`. Dedykowane Git MCP wrappery celowo nie są udostępniane: CLI jest kompletne, znane coding agentom i pozwala uniknąć duplikowania każdego podpolecenia Git na liście narzędzi.

## Typowy workflow

Gdy to możliwe, używaj ograniczonych, nieinteraktywnych poleceń:

```bash
git status --short --branch
git diff --stat
git diff
git add -- path/to/file
git commit -m "fix: concise description"
git push origin HEAD
```

Typowa sekwencja agent:

1. Sprawdź przez `run_shell(command="git status --short --branch")`.
2. Czytaj i edytuj tylko odpowiednie pliki.
3. Uruchom testy celowane.
4. Przejrzyj przez `run_shell(command="git diff --check && git diff")`.
5. Przed commit lub push uruchom `secret_scan`.
6. Wykonaj stage, commit i push jawnymi poleceniami Git CLI.

Użyj `machine` w tym samym shell tool, gdy repository znajduje się na remote worker.

## Poświadczenia

Deploymenty Docker mogą zachowywać typowe lokalizacje Git credentials pod `/persist/credentials`. Traktuj ten volume jako wrażliwy. Preferuj deploy keys ograniczone do repository, krótkotrwałe GitHub App tokens, odizolowanych automation users i ręczną review przed push.

## Higiena commitów

Utrzymuj commits skupione, pomijaj wygenerowane cache i build artifacts, zapisuj wykonane testy i nie stage’uj niepowiązanych zmian. Przy destrukcyjnych poleceniach takich jak reset, clean lub force-push najpierw sprawdź dokładny cel.

## Rozwiązywanie problemów

Gdy `git push` nie działa, sprawdź remote URL, trwałość credentials, branch protection i uprawnienia token. `gh auth status` jest przydatne, jeśli GitHub CLI jest zainstalowane.
