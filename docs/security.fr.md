<!-- i18n-source-sha256: 1f30fc9935125c84fb0838d17ec894d78aaa6253fe3903356414aac716ba2adc -->
# Sécurité

Utilisez OAuth pour les déploiements publics. Choisissez des valeurs robustes pour `LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN` et `LOCAL_SHELL_MCP_OAUTH_JWT_SECRET` et gardez-les privées.

Par défaut, les opérations sur les chemins sont limitées à l’espace de travail et les fragments de chemins sensibles sont bloqués. Le mode Full-container désactive les restrictions intégrées sur l’espace de travail et les chemins ; il est réservé aux conteneurs ou VM jetables.

Les liens de téléchargement générés sont des URL bearer publiques. Ils reposent sur des jetons à forte entropie, des TTL, des limites facultatives du nombre de téléchargements, des limites facultatives de taille et la révocation.
