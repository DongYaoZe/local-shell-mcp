<!-- i18n-source-sha256: 2ad041876ff35987d7fdd66cbcdc7ed3956f427e8d8b185f354555cdc29a1b8a -->
# Connecteur ChatGPT

Cette page traite de ChatGPT comme connexion client. Elle ne choisit pas le runtime. Avant de l’utiliser, démarrez le serveur avec Docker, VS Code extension, un binary ou une installation Python.

`local-shell-mcp` est conçu pour ChatGPT Developer Mode et les clients MCP complets. L’endpoint MCP expose directement la surface d’outils LSM normale.

## Prérequis du runtime

Choisissez et démarrez d’abord un runtime :

| Runtime | Page |
|---|---|
| Docker Compose | [Docker Compose runtime](../installation/docker.md) |
| VS Code extension | [VS Code extension runtime](../installation/vscode-extension.md) |
| Standalone binary | [Standalone binary runtime](../installation/binary.md) |
| Python / pipx / source | [Python runtimes](../installation/python.md) |

Exposez ensuite ce runtime via un chemin réseau accessible à ChatGPT. Voir [network connectivity](../clients/connectivity.md).

## URL publique

ChatGPT doit joindre le serveur en HTTPS. L’endpoint MCP est :

```text
https://your-public-host.example.com/mcp
```

Vérifiez que `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` correspond au public origin :

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

N’incluez pas `/mcp` dans `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## Configuration OAuth

Réglages publics recommandés :

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

Les access tokens n’expirent pas par défaut, car les longues sessions de code peuvent dépasser une durée de token courte. Révoquez l’accès en faisant tourner le JWT secret ou en redéployant avec un état neuf lorsque nécessaire.

## Ajouter le connecteur

1. Ouvrez les réglages du connecteur ChatGPT ou Developer Mode MCP.
2. Ajoutez un custom MCP server.
3. Saisissez l’URL MCP : `https://your-public-host.example.com/mcp`.
4. Terminez OAuth.
5. Approuvez la surface des outils.

## Live Workspace MCP App

Les clients ChatGPT prenant en charge MCP Apps peuvent afficher `local-shell-mcp` comme execution workspace interactif. Demandez à ChatGPT d’ouvrir Live Workspace une fois lorsque la visibilité temps réel ou la collaboration humaine est utile ; l’app se reconnecte ensuite seule, sans appels répétés à `workspace_open`.

Live Workspace est volontairement séparé du reasoning du modèle. Il montre l’execution state observable et les resources partagées :

- **Activity** affiche les démarrages, fins et échecs des outils MCP ainsi que les actions humaines.
- **Terminal** s’attache au backend de shell persistant existant et affiche la sortie PTY en direct.
- **Files** permet de parcourir, prévisualiser, éditer, créer et supprimer des fichiers de workspace locaux ou distants.
- **Diff** montre les changements Git staged/unstaged et peut renvoyer le diff courant à ChatGPT pour revue.
- **Jobs** montre les jobs gérés et les sessions persistantes.
- **Remotes** montre les workers et propose invitation, renommage et révocation lorsque le support distant est actif.
- **Audit** expose les récents enregistrements structurés d’audit MCP.

Live Workspace est toujours collaboratif : ChatGPT et l’humain peuvent modifier le même workspace simultanément. Il s’ouvre en fenêtre flottante de type PiP lorsque le host le permet et peut basculer entre fullscreen et fenêtre. Il n’existe pas d’état observe/takeover séparé.

Les vues files, diff, audit et activity peuvent envoyer un operational context sélectionné au prochain tour du modèle via le pont MCP Apps. Ce contexte est partagé explicitement ; l’UI n’expose ni ne reconstruit le reasoning privé du modèle.

### Réseau et sécurité

La MCP App rendue se connecte directement depuis son sandbox au service origin configuré pour le trafic terminal et événements à faible latence. `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` doit donc être l’origin HTTPS accessible au navigateur ChatGPT. L’endpoint MCP reste `https://your-public-host.example.com/mcp`.

L’ouverture du workspace émet un bearer token Live Workspace aléatoire et de courte durée. Le token n’apparaît que dans les metadata du résultat MCP destinées à l’app rendue, n’entre pas dans le structured content visible par le modèle et n’est accepté que par les API human/live UI. Le rattachement automatique au même `live_id` réutilise la credential actuelle afin que les vues qui se reconnectent ne s’invalident pas mutuellement ; il transporte aussi le `session_id` logique courant, ce qui permet de retrouver la Session durable même si l’état Live Workspace en mémoire a été perdu. Un nouvel appel explicite à `workspace_open` fait tourner la credential. L’app embarquée n’utilise ni cookies navigateur ni credentials ambiantes.

Les clients sans MCP Apps peuvent ignorer les metadata UI. Tous les outils de données MCP normaux restent disponibles et conservent le même comportement.

## Premier prompt

```text
Utilise local-shell-mcp. Appelle d’abord environment_get, puis liste la racine du workspace. Ne modifie pas encore les fichiers.
```

Cela vérifie la connectivité sans changement.

## Règles opérationnelles recommandées

Donnez au modèle des contraintes claires :

- Travailler dans `/workspace` sauf instruction explicite contraire.
- Exécuter les tests avant commit.
- Utiliser `secret_scan` avant push.
- Utiliser `link_create` uniquement pour des fichiers sûrs à partager.
- Préférer les sessions shell persistantes pour les processus longs.
- Résumer toutes les commandes ayant modifié des fichiers.

## Problèmes de découverte des outils

Si ChatGPT s’authentifie mais n’affiche pas les outils attendus :

- Confirmez que l’endpoint se termine par `/mcp`.
- Vérifiez `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY`.
- Vérifiez les headers du reverse proxy et les limites de request body.
- Inspectez `docker compose logs --tail=200 local-shell-mcp`.
- Confirmez que le service est en mode `mcp` ou `both`.

## Notes de sécurité

Les déploiements publics doivent garder OAuth activé. N’exposez pas les outils MCP complets sans authentification sur Internet public. Considérez chaque outil approuvé comme faisant partie de l’autorité effective du modèle connecté.
