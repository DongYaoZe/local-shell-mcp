<!-- i18n-source-sha256: d758caead1c922385409aceebf498662f25f4cbf252a48d65b29d91f07e5a173 -->
# Enlaces de archivos

`local-shell-mcp` puede exponer archivos del workspace controlado mediante bearer URL de alta entropía. Es útil cuando la IA genera reportes, archivos comprimidos, PDF, screenshots u otros artifacts que deben descargarse o mostrarse en el chat.

## Cuándo usar enlaces de archivos

Use enlaces de archivos para:

- PDF o reportes generados.
- Screenshots y artifacts del navegador.
- Resultados de build.
- Logs demasiado grandes para pegarlos.
- Archivos preparados para inspección manual.

No use enlaces de archivos para secrets, private keys, almacenes de credentials ni datos personales no relacionados.

## Flujo típico

1. Genere o localice un archivo bajo `/workspace`.
2. Llame a `link_create` con un TTL y un límite de descargas opcional. Defina `inline=true` cuando el archivo deba mostrarse directamente en un navegador o como imagen Markdown; el valor predeterminado es `false`, que fuerza la descarga como attachment.
3. Comparta la URL devuelta.
4. Revoque el enlace cuando ya no sea necesario.

## Herramientas relevantes

| Tool | Propósito |
|---|---|
| `link_create` | Crear una URL tokenizada para un archivo del workspace. |
| `link_list` | Mostrar enlaces activos. |
| `link_revoke` | Deshabilitar un enlace antes de su expiración. |

## Controles

Las opciones de configuración incluyen:

- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_ENABLED`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_MAX_DOWNLOADS`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_FILE_BYTES`

Use TTL más cortos para artifacts sensibles y establezca un maximum download count cuando el enlace esté destinado a un único destinatario.

## Notas de seguridad

Los enlaces de archivos son bearer URL. Cualquier persona con la URL puede descargar el archivo hasta que expire, alcance su download limit o sea revocado. Trátelos como secrets temporales. Las respuestas inline incluyen un CSP sandbox y `X-Content-Type-Options: nosniff`, de modo que los formatos activos no puedan acceder al LSM origin ni ejecutarse como contenido same-origin sin sandbox.
