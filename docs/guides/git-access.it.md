<!-- i18n-source-sha256: 3b7d6ab07c5d6bad2bfb22f366893819ac8de8754c7c28bcb35f24ea5695979c -->
# Accesso Git

`local-shell-mcp` usa l’interfaccia a riga di comando Git standard tramite `run_shell`, `shell_start` o `job_start`. I wrapper MCP dedicati a Git non vengono esposti intenzionalmente: la CLI è completa, familiare ai coding agents ed evita di duplicare ogni sottocomando Git nell’elenco degli strumenti.

## Workflow comune

Usa comandi delimitati e non interattivi quando possibile:

```bash
git status --short --branch
git diff --stat
git diff
git add -- path/to/file
git commit -m "fix: concise description"
git push origin HEAD
```

Una tipica sequenza dell’agent è:

1. Ispezionare con `run_shell(command="git status --short --branch")`.
2. Leggere e modificare solo i file rilevanti.
3. Eseguire test mirati.
4. Esaminare con `run_shell(command="git diff --check && git diff")`.
5. Eseguire `secret_scan` prima di commit o push.
6. Fare stage, commit e push usando comandi Git CLI espliciti.

Usa `machine` sullo stesso shell tool quando il repository si trova su un remote worker.

## Credenziali

I deployment Docker possono rendere persistenti le comuni posizioni delle credentials Git sotto `/persist/credentials`. Considera questo volume sensibile. Preferisci deploy key limitate al repository, token GitHub App di breve durata, utenti di automazione isolati e revisione manuale prima del push.

## Igiene dei commit

Mantieni i commit focalizzati, escludi cache generate e build artifacts, registra i test eseguiti ed evita di fare stage di modifiche non correlate. Per comandi distruttivi come reset, clean o force-push, verifica prima il target esatto.

## Risoluzione dei problemi

Quando `git push` fallisce, controlla remote URL, persistenza delle credentials, branch protection e permessi del token. `gh auth status` è utile se GitHub CLI è installato.
