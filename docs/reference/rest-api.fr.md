<!-- i18n-source-sha256: 87dd7fb66311534dcd5a7217bba8c809f71fe6189e8c39b3e265da923cc82d22 -->
# API REST

L’interface principale est MCP sur `/mcp`. Une surface REST est aussi disponible pour les health checks, file links et certaines opérations de service.

## Santé

```http
GET /healthz
```

Renvoie l’état de santé du serveur et son statut de base.

## MCP

```http
POST /mcp
```

Endpoint MCP Streamable HTTP utilisé par ChatGPT et les autres MCP client.

## Appels d’outils via REST

Les appels d’outils REST utilisent des envelopes cohérentes pour les succès et les erreurs. Les erreurs de validation renvoient des payloads structurés `ok: false` au lieu d’exceptions brutes du framework.

## Agent Skills

Le registre fixe des Skills est également disponible via REST :

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```

Les modifications des répertoires de Skill sont visibles dès l’appel suivant et ne modifient pas la liste des outils MCP.

## Liens de fichiers

Les téléchargements tokenisés sont servis par l’application HTTP intégrée. Les liens sont des bearer URL avec TTL, limite maximale facultative de téléchargements et prise en charge de la révocation.

## Authentification

Les déploiements publics doivent utiliser OAuth. Le bypass localhost peut être activé pour le développement, mais un accès public non authentifié est dangereux.
