<!-- i18n-source-sha256: 1f30fc9935125c84fb0838d17ec894d78aaa6253fe3903356414aac716ba2adc -->
# Segurança

Use OAuth em implantações públicas. Mantenha `LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN` e `LOCAL_SHELL_MCP_OAUTH_JWT_SECRET` fortes e privados.

Por padrão, as operações de caminho ficam restritas ao workspace e fragmentos de caminhos sensíveis são bloqueados. O modo Full-container desativa as restrições internas de workspace e de caminhos e deve ser usado apenas em contêineres ou VMs descartáveis.

Os links gerados para download de arquivos são URLs bearer públicas. Eles dependem de tokens de alta entropia, TTLs, limites opcionais de quantidade de downloads, limites opcionais de tamanho e revogação.
