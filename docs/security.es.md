<!-- i18n-source-sha256: 1f30fc9935125c84fb0838d17ec894d78aaa6253fe3903356414aac716ba2adc -->
# Seguridad

Utilice OAuth en despliegues públicos. Mantenga `LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN` y `LOCAL_SHELL_MCP_OAUTH_JWT_SECRET` con valores robustos y privados.

De forma predeterminada, las operaciones de rutas quedan limitadas al espacio de trabajo y se bloquean fragmentos de rutas sensibles. El modo Full-container desactiva las restricciones integradas de espacio de trabajo y de rutas, y está pensado únicamente para contenedores o máquinas virtuales desechables.

Los enlaces de descarga de archivos generados son URL bearer públicas. Se protegen mediante tokens de alta entropía, TTL, límites opcionales de número de descargas, límites opcionales de tamaño y revocación.
