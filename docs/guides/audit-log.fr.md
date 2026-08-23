<!-- i18n-source-sha256: 25bb55459e83ee02b923876bad8d288c7a2055c4474f2098d58ce1e4a5e72605 -->
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

Le fichier `audit.jsonl` actif est limité par défaut à 20 MB via `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES`. Lors de la maintenance de rétention, les anciens enregistrements sont déplacés vers des archives Zstandard autonomes `audit-archive/*.jsonl.zst` au lieu d’être supprimés ; les gros audit payloads externalisés sont aussi intégrés à l’archive avant leur suppression du stockage actif.

Les archives compressées ont une limite distincte définie par `LOCAL_SHELL_MCP_MAX_AUDIT_ARCHIVE_BYTES`, 512 MB par défaut. Au-delà, les archives les plus anciennes sont supprimées en premier. La valeur `0` désactive la rétention compressée à long terme. La Web UI, les requêtes Activity/Audit et `audit_tail` lisent uniquement le hot log actif. Les archives compressées servent de stockage froid pour la rétention ou l’export et ne sont pas décompressées automatiquement par les requêtes UI normales.

## Limites

Les journaux d’audit ne constituent pas un sandbox. Ils améliorent la traçabilité, mais n’empêchent pas un modèle connecté d’agir dans les limites de son autorité configurée.
