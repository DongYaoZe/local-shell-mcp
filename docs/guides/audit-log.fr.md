<!-- i18n-source-sha256: 4aec137923c38de0ed4a1b760b5dbd6ce99090d508ce3fe838d35ad44b4ba4f1 -->
# Journal d’audit

`local-shell-mcp` écrit des entrées d’audit structurées afin d’aider à reconstruire les actions effectuées par un client connecté.

Chemin par défaut :

```text
/workspace/.local-shell-mcp/audit.jsonl
```

## Éléments enregistrés

Les entrées d’audit couvrent notamment :

- Début/fin des tool calls.
- Métadonnées d’exécution des commandes.
- Timeouts et erreurs gérées.
- Enregistrement des remote workers et activité des jobs.
- Création et révocation des file links.
- Événements liés à l’authentification lorsque cela s’applique.

Les arguments sensibles sont masqués lorsque le serveur sait les identifier.

## Lecture du journal

Utilisez l’outil MCP :

```text
audit_tail
```

Ou inspectez-le directement :

```bash
tail -n 100 /workspace/.local-shell-mcp/audit.jsonl
```

## Usage opérationnel

Les journaux d’audit sont particulièrement utiles pour :

- Examiner les commandes ayant modifié des fichiers.
- Vérifier si un remote worker a été utilisé.
- Déboguer des échecs inattendus.
- Détecter une exposition accidentelle de file links.
- Aider à la réponse à incident après une erreur de deployment public.

## Rétention

La taille du journal est bornée par `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES`. Effectuez une rotation ou exportez-le vers un stockage externe si vous avez besoin d’une rétention longue.

## Limites

Les journaux d’audit ne constituent pas un sandbox. Ils améliorent la traçabilité, mais n’empêchent pas un modèle connecté d’agir dans les limites de son autorité configurée.
