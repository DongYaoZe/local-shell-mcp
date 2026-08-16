<!-- i18n-source-sha256: a3d2dc835f99feed33a73ae3dd880dabab04a37d7461b99f1fa49c33ba0506e1 -->
# Runtime Stdio

Le mode stdio est destiné aux MCP client locaux qui lancent `local-shell-mcp` comme child process et communiquent par entrée/sortie standard.

Il ne s’agit pas d’un deployment HTTP public. ChatGPT web/app ne peut pas l’utiliser directement, car ChatGPT ne peut pas lancer de process sur votre machine.

## Quand utiliser stdio

Utilisez stdio mode lorsque :

- Votre MCP client prend en charge les définitions de serveur basées sur une commande.
- Le client et le workspace contrôlé se trouvent sur la même machine.
- Vous n’avez pas besoin d’OAuth, de HTTPS public, de reverse proxy ni de tunnel.
- Vous voulez que le client gère le lifecycle du serveur.

N’utilisez pas stdio mode lorsque :

- Le client est ChatGPT web/app.
- Plusieurs remote clients ont besoin du même serveur.
- Vous avez besoin de téléchargements tokenisés via HTTP.
- Vous avez besoin de routes d’inscription remote-worker servies via HTTP.

## Commande

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Une configuration MCP client générique contient généralement :

```json
{
  "mcpServers": {
    "local-shell-mcp": {
      "command": "local-shell-mcp",
      "args": ["--mode", "stdio"],
      "env": {
        "LOCAL_SHELL_MCP_WORKSPACE_ROOT": "/path/to/workspace"
      }
    }
  }
}
```

Adaptez le schema à votre client. Certains appellent cette section `servers`, `tools`, `mcpServers` ou `contextServers`.

## Différences avec HTTP mode

| Domaine | Stdio mode | HTTP MCP mode |
|---|---|---|
| Transport | stdin/stdout | HTTP streamable MCP endpoint |
| Endpoint | Aucun | `/mcp` |
| OAuth | Inutile | Recommandé pour un usage public |
| Health endpoint | Aucun | `/healthz`, `/readyz` |
| Utilisation publique par ChatGPT | Non | Oui, derrière HTTPS |
| Server lifecycle | Le client lance le process | Vous gérez le process/runtime |

La tool surface utilise sinon la même implémentation server-side, sous réserve de la configuration et du support du client.

## Notes de sécurité

Stdio mode s’exécute souvent directement sur l’hôte avec le même utilisateur que le MCP client. Utilisez un workspace root limité et évitez un accès large au filesystem. Gardez full-container mode désactivé sauf si stdio s’exécute lui-même dans un container ou une VM jetable.
