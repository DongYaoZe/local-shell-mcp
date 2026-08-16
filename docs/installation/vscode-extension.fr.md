<!-- i18n-source-sha256: db40797f92f76326aa62db50ac4bb293edb4248791806c2fb46477a65c3e73cc -->
# Runtime extension VS Code

L’extension VS Code est un launcher et une UI pratique pour le même serveur `local-shell-mcp`. C’est un choix de runtime car elle démarre le processus serveur pour le workspace actuel de l’éditeur.

Ce n’est pas le connecteur ChatGPT lui-même. ChatGPT se connecte toujours à un endpoint HTTPS public `/mcp` depuis web/app.

## Ce que fait l’extension

L’extension :

- Démarre `local-shell-mcp` pour le workspace VS Code courant.
- Arrête et redémarre le serveur.
- Affiche le output serveur dans un canal de sortie VS Code.
- Vérifie `/healthz`.
- Copie l’URL MCP.
- Copie un prompt de setup ChatGPT contenant workspace et endpoint.

L’extension n’embarque pas le binary serveur. Installez `local-shell-mcp` séparément puis indiquez son executable à l’extension s’il n’est pas dans `PATH`.

## Quand l’utiliser

Utilisez ce runtime lorsque :

- Vous commencez habituellement dans un dossier VS Code.
- Vous voulez un flux bouton/command palette plutôt qu’une commande terminal manuelle.
- Le projet a déjà ses dépendances installées sur le host.
- Vous travaillez sur des repositories de confiance ou un workspace limité.
- Vous acceptez d’exposer uniquement ce workspace au modèle.

Utilisez Docker lorsque :

- Le repository n’est pas fiable.
- La tâche installera des packages arbitraires.
- La tâche a besoin d’un large toolchain préinstallé.
- Vous voulez pouvoir reset facilement en recréant un container.
- Vous voulez une boundary plus propre que votre compte host.

## Installer l’executable

Choisissez une méthode d’installation du serveur :

```bash
pipx install local-shell-mcp
```

ou téléchargez le release binary pour votre OS et placez-le dans `PATH`.

Installez ensuite l’asset VSIX de release :

```bash
code --install-extension local-shell-mcp-<version>.vsix
```

Vous pouvez aussi utiliser **Extensions: Install from VSIX...** dans la command palette.

## Réglages de l’extension

| Réglage | Rôle | Valeur typique |
|---|---|---|
| `local-shell-mcp.executablePath` | Path vers l’executable serveur | `local-shell-mcp` or an absolute binary path |
| `local-shell-mcp.host` | Adresse bind du serveur local | `127.0.0.1` for local-only, `0.0.0.0` only behind a controlled network/proxy |
| `local-shell-mcp.port` | Port local du serveur | `8765` |
| `local-shell-mcp.workspaceRoot` | Workspace exposé à MCP | Vide pour le premier dossier VS Code ou path explicite |
| `local-shell-mcp.authMode` | Mode d’authentification | `oauth` for ChatGPT, `none` only for trusted localhost testing |
| `local-shell-mcp.publicBaseUrl` | Origin HTTPS public copié dans prompts et URLs | Tunnel/proxy origin such as `https://mcp.example.com` |
| `local-shell-mcp.oauthAdminPin` | PIN d’autorisation OAuth | Valeur aléatoire forte pour usage public |
| `local-shell-mcp.allowFullContainer` | Flag de comportement full-container | Garder `false` en utilisation directe sur host |
| `local-shell-mcp.extraEnv` | Environment supplémentaire du processus serveur | Uniquement valeurs sûres propres au projet |

## Flux de base

1. Ouvrez un dossier projet dans VS Code.
2. Exécutez **local-shell-mcp: Start Server**.
3. Exécutez **Show Server Status** ou **Check Health** si disponible.
4. Utilisez **Copy MCP URL** pour un client local ou **Copy ChatGPT Setup Prompt** pour ChatGPT.
5. Ajoutez l’endpoint à votre client.

L’endpoint local ressemble généralement à :

```text
http://127.0.0.1:8765/mcp
```

Il est utile aux clients locaux mais inaccessible depuis ChatGPT web/app.

## Utilisation avec ChatGPT

Pour utiliser depuis ChatGPT un serveur lancé par VS Code, ajoutez un tunnel HTTPS ou reverse proxy devant le port local.

Exemple :

```text
ChatGPT
  -> https://your-public-host.example.com/mcp
  -> tunnel or reverse proxy
  -> 127.0.0.1:8765 on your machine
  -> VS Code-launched local-shell-mcp process
```

Définissez :

```text
local-shell-mcp.publicBaseUrl = https://your-public-host.example.com
local-shell-mcp.authMode = oauth
local-shell-mcp.oauthAdminPin = <strong pin>
```

L’URL copiée pour ChatGPT doit finir par `/mcp` :

```text
https://your-public-host.example.com/mcp
```

## Sécurité du runtime host

L’extension exécute généralement les commandes en tant qu’utilisateur host. C’est matériellement différent d’un container Docker jetable.

Règles recommandées :

- Ouvrez seulement le repository que le modèle doit contrôler.
- Gardez `allowFullContainer` désactivé.
- Ne définissez pas workspace root sur votre home directory.
- Ne gardez pas de secrets sans rapport dans le workspace.
- Utilisez `secret_scan` avant commits et pushes.
- Préférez Docker pour les repositories inconnus ou tâches lourdes en installation de packages.

## Prompt courant

Après avoir copié le setup prompt, commencez par une tâche read-only :

```text
Utilise local-shell-mcp. Appelle d’abord environment_get et file_tree sur le workspace. Ne modifie pas encore les fichiers.
```

Passez ensuite à une modification bornée :

```text
Corrige le test en échec dans ce workspace. Lis d’abord les fichiers concernés, fais le patch minimal, exécute le test ciblé et montre git diff. Ne commit pas avant mon approbation.
```

## Dépannage

| Symptôme | Vérifier |
|---|---|
| L’extension ne démarre pas le serveur | Confirmez que `local-shell-mcp.executablePath` existe et exécute `--help` dans un terminal |
| ChatGPT ne peut pas l’atteindre | Une URL locale `127.0.0.1` n’est pas publique ; configurez tunnel/proxy et `publicBaseUrl` |
| Les tools exposent le mauvais dossier | Définissez explicitement `local-shell-mcp.workspaceRoot` |
| Auth échoue après redémarrage | Définissez OAuth admin PIN et JWT secret stables via `extraEnv` ou configuration runtime |
| Les commandes manquent de dépendances | Installez les dépendances sur le host ou passez au runtime Docker |
