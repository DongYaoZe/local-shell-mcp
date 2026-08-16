<!-- i18n-source-sha256: 3986da6ff877609189b0d88d363aff1f5f45445f0cfe5ffa608a31929078542c -->
# Connectivité réseau

Les MCP client HTTP situés hors de la machine ont besoin d’un HTTPS origin accessible. Cette page traite du routage réseau, pas du choix du runtime.

Le client endpoint se termine normalement par `/mcp` :

```text
https://your-public-host.example.com/mcp
```

Le réglage public base URL du serveur contient uniquement l’origin :

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

N’incluez pas `/mcp` dans cette base URL.

## Options de connectivité

| Option | Quand l’utiliser |
|---|---|
| Compose tunnel sidecar | Docker Compose avec le profile `tunnel` intégré |
| Tunnel externe | Tout runtime devant être accessible hors du réseau local |
| Caddy | TLS automatique simple |
| Nginx ou Nginx Proxy Manager | Infrastructure Nginx existante |
| Traefik | Routage container-native existant |

## Chemins

Transmettez l’ensemble de l’origin au serveur en cours d’exécution. Les chemins importants comprennent :

| Chemin | Rôle |
|---|---|
| `/mcp` | MCP Streamable HTTP endpoint |
| `/healthz`, `/readyz` | Contrôles de santé |
| `/.well-known/...` | Métadonnées de découverte du client |
| `/oauth/...` | Flux d’autorisation du client |
| `/downloads/...` | Liens facultatifs vers les fichiers générés |
| `/join/...`, `/remote/...` | Flux remote-worker facultatif |

## Comportement du proxy

Le proxy doit préserver les chemins, transmettre les request bodies, prendre en charge les responses longues et éviter des timeouts trop courts.

## Vérifications

```bash
curl -i http://127.0.0.1:8765/healthz
curl -i https://your-public-host.example.com/healthz
```

## Erreurs courantes

| Erreur | Correction |
|---|---|
| Utiliser `https://host` dans ChatGPT au lieu de `https://host/mcp` | Ajouter `/mcp` uniquement au client endpoint |
| Définir `LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://host/mcp` | Définir uniquement l’origin |
| Router uniquement `/mcp` | Router tout l’origin afin que la découverte et l’autorisation fonctionnent aussi |
| Utiliser un host runtime avec un workspace trop large | Utiliser un workspace étroit ou Docker |

## Combinaisons suggérées

| Runtime | Modèle réseau |
|---|---|
| Docker Compose sur un serveur | Reverse proxy existant ou profile tunnel Compose |
| Docker Compose sur une machine domestique | Outbound tunnel |
| VS Code extension sur un portable | Tunnel temporaire pour la session |
| Binary sur une VM | Reverse proxy sur la VM ou à la périphérie du réseau |
| Serveur de développement Python/source | Généralement localhost uniquement |
| Stdio mode | Aucun chemin HTTP ; utiliser un MCP client local |
