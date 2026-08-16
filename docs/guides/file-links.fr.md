<!-- i18n-source-sha256: d758caead1c922385409aceebf498662f25f4cbf252a48d65b29d91f07e5a173 -->
# Liens de fichiers

`local-shell-mcp` peut exposer des fichiers du workspace contrôlé via des bearer URL à forte entropie. C’est utile lorsque l’IA génère des rapports, archives, PDF, screenshots ou autres artifacts qui doivent être téléchargés ou affichés dans le chat.

## Quand utiliser les liens de fichiers

Utilisez-les pour :

- Les PDF ou rapports générés.
- Les screenshots et artifacts du navigateur.
- Les sorties de build.
- Les logs trop volumineux pour être collés.
- Les archives préparées pour une inspection manuelle.

N’utilisez pas les liens de fichiers pour des secrets, private keys, magasins de credentials ou données personnelles sans rapport avec la tâche.

## Flux typique

1. Générez ou localisez un fichier sous `/workspace`.
2. Appelez `link_create` avec un TTL et une limite facultative de téléchargements. Définissez `inline=true` lorsque le fichier doit être rendu directement dans un navigateur ou comme image Markdown ; la valeur par défaut est `false`, ce qui force un téléchargement en attachment.
3. Partagez l’URL renvoyée.
4. Révoquez le lien lorsqu’il n’est plus nécessaire.

## Outils concernés

| Tool | Rôle |
|---|---|
| `link_create` | Créer une URL tokenisée pour un fichier du workspace. |
| `link_list` | Afficher les liens actifs. |
| `link_revoke` | Désactiver un lien avant son expiration. |

## Contrôles

Les options de configuration comprennent :

- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_ENABLED`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_MAX_DOWNLOADS`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_FILE_BYTES`

Utilisez des TTL plus courts pour les artifacts sensibles et définissez un maximum download count lorsque le lien est destiné à un seul destinataire.

## Notes de sécurité

Les liens de fichiers sont des bearer URL. Toute personne disposant de l’URL peut télécharger le fichier jusqu’à son expiration, l’atteinte de sa download limit ou sa révocation. Traitez-les comme des secrets temporaires. Les réponses inline incluent un CSP sandbox et `X-Content-Type-Options: nosniff`, empêchant les formats actifs d’accéder au LSM origin ou de s’exécuter comme contenu same-origin non sandboxé.
