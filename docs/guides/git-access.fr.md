<!-- i18n-source-sha256: 3b7d6ab07c5d6bad2bfb22f366893819ac8de8754c7c28bcb35f24ea5695979c -->
# Accès Git

`local-shell-mcp` utilise l’interface en ligne de commande Git standard via `run_shell`, `shell_start` ou `job_start`. Les wrappers MCP dédiés à Git ne sont volontairement pas exposés : la CLI est complète, familière aux coding agents et évite de dupliquer chaque sous-commande Git dans la liste des outils.

## Workflow courant

Utilisez autant que possible des commandes non interactives et bornées :

```bash
git status --short --branch
git diff --stat
git diff
git add -- path/to/file
git commit -m "fix: concise description"
git push origin HEAD
```

Une séquence d’agent typique :

1. Inspecter avec `run_shell(command="git status --short --branch")`.
2. Lire et modifier uniquement les fichiers concernés.
3. Exécuter les tests ciblés.
4. Examiner avec `run_shell(command="git diff --check && git diff")`.
5. Exécuter `secret_scan` avant commit ou push.
6. Stage, commit et push avec des commandes Git CLI explicites.

Utilisez `machine` sur le même shell tool lorsque le repository se trouve sur un remote worker.

## Identifiants

Les deployments Docker peuvent conserver les emplacements courants de credentials Git sous `/persist/credentials`. Traitez ce volume comme sensible. Préférez des deploy keys limitées au repository, des tokens GitHub App à courte durée de vie, des utilisateurs d’automatisation isolés et une revue manuelle avant push.

## Hygiène des commits

Gardez les commits ciblés, excluez les caches générés et build artifacts, consignez les tests exécutés et n’ajoutez pas de modifications sans rapport. Pour les commandes destructives comme reset, clean ou force-push, inspectez d’abord la cible exacte.

## Dépannage

Si `git push` échoue, vérifiez la remote URL, la persistance des credentials, la branch protection et les permissions du token. `gh auth status` est utile lorsque GitHub CLI est installé.
