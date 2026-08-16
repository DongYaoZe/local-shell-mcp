<!-- i18n-source-sha256: 1f30fc9935125c84fb0838d17ec894d78aaa6253fe3903356414aac716ba2adc -->
# Sicurezza

Usa OAuth per le distribuzioni pubbliche. Imposta valori robusti per `LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN` e `LOCAL_SHELL_MCP_OAUTH_JWT_SECRET` e mantienili privati.

Per impostazione predefinita, le operazioni sui percorsi sono limitate al workspace e i frammenti di percorso sensibili vengono bloccati. La modalità Full-container disattiva le restrizioni integrate su workspace e percorsi ed è destinata esclusivamente a container o VM usa e getta.

I link di download generati sono URL bearer pubblici. La protezione si basa su token ad alta entropia, TTL, limiti opzionali al numero di download, limiti opzionali alle dimensioni e revoca.
