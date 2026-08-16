<!-- i18n-source-sha256: 8b4e2e48e58e65721bf5ebf9f7b1d8aedf34d62d5a7948d36d6b9102ee1f6cc3 -->
# Choix du runtime et modèle de déploiement

`local-shell-mcp` implique deux décisions indépendantes :

1. **Runtime**: comment le processus serveur s’exécute et quel workspace il contrôle.
2. **Client connection**: comment ChatGPT ou un autre MCP client atteint ce serveur.

Ne considérez pas ChatGPT comme une méthode de déploiement. ChatGPT est un client. Docker, VS Code extension, release binaries, installations Python et stdio mode sont des choix de runtime.

```text
Runtime layer                      Exposure layer                 Client layer
-------------------------------    ---------------------------    ----------------------
Docker Compose                     local HTTP only                ChatGPT custom MCP
VS Code extension                  HTTPS reverse proxy/tunnel     Generic MCP client
Standalone binary                  stdio process pipe             VS Code extension UI
pipx / source checkout             remote-worker outbound join    REST-style diagnostics
```

Une configuration publique courante est :

```text
ChatGPT
  -> https://mcp.example.com/mcp
  -> reverse proxy or tunnel
  -> local-shell-mcp runtime
  -> controlled workspace
```

Une configuration avec MCP client local peut être plus simple :

```text
Local MCP client
  -> starts local-shell-mcp --mode stdio
  -> controlled workspace
```

## Matrice de choix du runtime

| Runtime | Idéal pour | Limite d’isolation | Source du toolchain | Accès public ChatGPT | Page |
|---|---|---|---|---|---|
| Docker Compose | La plupart des charges coding-agent et workspaces reproductibles | Container | L’image projet inclut un toolchain par défaut étendu | Ajouter proxy HTTPS ou tunnel | [Docker Compose](../installation/docker.md) |
| Docker Compose + tunnel sidecar | Déploiement public monobloc avec Cloudflare Tunnel | Container | Project image | Intégré au profil Compose `tunnel` | [Docker Compose](../installation/docker.md#cloudflare-tunnel-sidecar) |
| VS Code extension | Démarrer/arrêter le serveur depuis un workspace éditeur | Généralement processus host | Outils host plus executable configuré | Ajouter tunnel/proxy HTTPS externe pour ChatGPT | [VS Code extension](../installation/vscode-extension.md) |
| Standalone binary | Hosts ou VM sans Docker | Host or VM | Outils host plus executable configuré | Ajouter proxy HTTPS ou tunnel | [Standalone binary](../installation/binary.md) |
| `pipx` / source install | Usage Python-native, debugging, développement | Host virtualenv or VM | Package Python plus outils host | Ajouter proxy HTTPS ou tunnel | [Python install](../installation/python.md) |
| Stdio mode | MCP clients locaux lançant directement des processus | Client process boundary | Outils host plus executable configuré | Inutilisable par ChatGPT web/app | [Stdio mode](../installation/stdio.md) |

## Matrice de connexion client

| Chemin client | HTTPS public requis | Utilise `/mcp` | OAuth requis | Runtime typique |
|---|---:|---:|---:|---|
| ChatGPT custom MCP connector | Oui | Oui | Oui pour usage public | Docker, VS Code extension, binary, or Python |
| Generic local MCP client over stdio | Non | Non | Non | `local-shell-mcp --mode stdio` |
| Generic HTTP MCP client | Généralement non en localhost ; oui entre réseaux | Oui | Recommandé hors localhost | Any HTTP runtime |
| VS Code extension helper flow | Seulement si ChatGPT doit se connecter | Oui lors de la copie URL ChatGPT | Recommandé pour ChatGPT | VS Code-launched runtime |

Voir [ChatGPT connector](../getting-started/chatgpt-connector.md), [generic MCP clients](../clients/generic-mcp.md), [network connectivity](../clients/connectivity.md).

## Ce que contrôle chaque runtime

Chaque runtime lance le même code serveur et expose les mêmes familles d’outils MCP lorsqu’elles sont activées :

- Shell et persistent shell sessions.
- Filesystem, search et patch tools.
- Opérations Git.
- Browser automation via Playwright.
- Audit log et task-state tools.
- Tokenized file links.
- Optional remote-worker lifecycle et machine-routed tools.

La différence ne porte pas sur l’API abstraite mais sur l’**operating environment** derrière elle.

| Question | Docker Compose | VS Code extension | Binary / Python |
|---|---|---|---|
| Où s’exécutent les commandes ? | Dans le container | Généralement sur le workspace host | Dans l’environnement process host ou VM |
| Workspace par défaut ? | Mounted `/workspace` | Dossier VS Code actuel ou path configuré | `LOCAL_SHELL_MCP_WORKSPACE_ROOT` |
| Compilers/browsers préinstallés ? | Oui, largement | Seulement si installés sur le host | Seulement si installés sur le host |
| Reset facile ? | Recréer container et volume workspace | Dépend du workspace | Dépend du host/VM |
| Install arbitraire adaptée ? | Oui si jetable | Plus risqué sur host | Plus risqué hors VM |

## Sélection recommandée

Utilisez d’abord **Docker Compose** sauf raison contraire. Il fournit la limite de sécurité la plus claire et le toolchain par défaut le plus complet.

Utilisez **VS Code extension** lorsque le workflow commence dans l’éditeur et qu’un launcher local est souhaité. Cela reste un runtime. Il ne rend pas le serveur accessible à ChatGPT à lui seul ; ajoutez tunnel ou reverse proxy pour ChatGPT web/app.

Utilisez **standalone binary** lorsque Docker est indisponible mais qu’une VM, container host ou compte dédié fournit déjà la limite.

Utilisez **`pipx` ou source install** pour développer/debugger `local-shell-mcp` ou lorsqu’un environnement Python est plus simple à maintenir.

Utilisez **stdio mode** uniquement avec des MCP clients locaux capables de lancer le processus serveur. Ce n’est pas un déploiement public et ChatGPT web/app ne peut pas l’utiliser directement.

## Règle de l’endpoint public

Pour les MCP clients HTTP comme ChatGPT, l’endpoint MCP est :

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` contient uniquement l’origin :

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

N’ajoutez pas `/mcp` à `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## Pages runtime

- [Docker Compose](../installation/docker.md)
- [VS Code extension](../installation/vscode-extension.md)
- [Standalone binary](../installation/binary.md)
- [Python, `pipx`, and source install](../installation/python.md)
- [Stdio mode](../installation/stdio.md)

## Pages client

- [ChatGPT connector](../getting-started/chatgpt-connector.md)
- [Generic MCP clients](../clients/generic-mcp.md)
- [Public HTTPS exposure](../clients/connectivity.md)
