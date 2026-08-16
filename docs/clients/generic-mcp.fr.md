<!-- i18n-source-sha256: 6e76d0746c53eeef3e770417742a44e122c6484afd0d91ddf6a4995387085c74 -->
# MCP client génériques

`local-shell-mcp` peut être utilisé par ChatGPT et par d’autres MCP client. Le client choisit de se connecter en HTTP ou de lancer le serveur via stdio.

## MCP client HTTP

Utilisez HTTP mode lorsque le serveur est déjà en cours d’exécution :

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode mcp
```

Endpoint local :

```text
http://127.0.0.1:8765/mcp
```

Endpoint réseau :

```text
https://your-public-host.example.com/mcp
```

Utilisez OAuth pour tout endpoint accessible au-delà d’un localhost de confiance.

## MCP client stdio

Utilisez stdio mode lorsque le client lance lui-même le processus serveur :

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Forme typique de configuration du client :

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

Les schemas varient selon les clients. Certains appellent cette section `mcpServers`, d’autres utilisent un nom différent.

## Première vérification sûre

Pour un client nouvellement connecté, commencez par :

```text
Call environment_get, then file_tree on the workspace root. Do not modify files yet.
```

Exécutez ensuite une tâche bornée avec des règles explicites concernant les modifications, les tests et Git.
