<!-- i18n-source-sha256: 3b7d6ab07c5d6bad2bfb22f366893819ac8de8754c7c28bcb35f24ea5695979c -->
# Git-Zugriff

`local-shell-mcp` verwendet die normale Git-Kommandozeile über `run_shell`, `shell_start` oder `job_start`. Dedizierte Git-MCP-Wrapper werden bewusst nicht angeboten: Die CLI ist vollständig, Coding Agents vertraut und vermeidet, jeden Git-Unterbefehl in der Tool-Liste zu duplizieren.

## Üblicher Ablauf

Verwenden Sie nach Möglichkeit begrenzte, nicht interaktive Befehle:

```bash
git status --short --branch
git diff --stat
git diff
git add -- path/to/file
git commit -m "fix: concise description"
git push origin HEAD
```

Eine typische Agent-Sequenz:

1. Mit `run_shell(command="git status --short --branch")` prüfen.
2. Nur relevante Dateien lesen und bearbeiten.
3. Zielgerichtete Tests ausführen.
4. Mit `run_shell(command="git diff --check && git diff")` überprüfen.
5. Vor Commit oder Push `secret_scan` ausführen.
6. Mit expliziten Git-CLI-Befehlen stagen, committen und pushen.

Verwenden Sie `machine` am selben Shell-Tool, wenn das Repository auf einem Remote Worker liegt.

## Zugangsdaten

Docker-Bereitstellungen können übliche Git-Credential-Pfade unter `/persist/credentials` dauerhaft speichern. Behandeln Sie dieses Volume als sensibel. Bevorzugen Sie repository-begrenzte Deploy Keys, kurzlebige GitHub-App-Tokens, isolierte Automatisierungsbenutzer und manuelle Prüfung vor dem Push.

## Commit-Hygiene

Halten Sie Commits fokussiert, lassen Sie generierte Caches und Build-Artefakte weg, dokumentieren Sie ausgeführte Tests und stagen Sie keine unzusammenhängenden Änderungen. Prüfen Sie bei destruktiven Befehlen wie reset, clean oder force-push zuerst das genaue Ziel.

## Fehlerbehebung

Wenn `git push` fehlschlägt, prüfen Sie Remote-URL, Credential-Persistenz, Branch Protection und Token-Berechtigungen. `gh auth status` ist nützlich, wenn GitHub CLI installiert ist.
