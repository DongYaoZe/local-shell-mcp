<!-- i18n-source-sha256: a5b96c45536a4d18d1e09f2c47a873e568d0594539aa630ed159b4ddbf3cc25d -->
# Registro de auditoría

`local-shell-mcp` escribe entradas de auditoría estructuradas para ayudar a reconstruir lo que hizo un client conectado.

Ruta predeterminada:

```text
/workspace/.local-shell-mcp/audit.jsonl
```

## Qué se registra

Las entradas de auditoría cubren eventos como:

- Inicio/fin de tool calls.
- Metadatos de ejecución de comandos.
- Timeouts y errores gestionados.
- Registro de remote workers y actividad de jobs.
- Creación y revocación de file links.
- Eventos relacionados con autenticación cuando corresponda.

Los argumentos sensibles se redactan cuando el servidor puede identificarlos.

## Leer el registro

Use la herramienta MCP:

```text
audit_tail
```

O inspecciónelo directamente:

```bash
tail -n 100 /workspace/.local-shell-mcp/audit.jsonl
```

## Uso operativo

Los registros de auditoría son especialmente útiles para:

- Revisar comandos que modificaron archivos.
- Comprobar si se utilizó un remote worker.
- Depurar fallos inesperados.
- Detectar exposición accidental de file links.
- Apoyar la respuesta a incidentes tras un error en un deployment público.

## Retención

El `audit.jsonl` activo está limitado de forma predeterminada a 20 MB por `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES`. Durante el mantenimiento de retención, los registros antiguos se trasladan a archivos Zstandard autocontenidos en `audit-archive/*.jsonl.zst` en lugar de descartarse; los audit payloads grandes externalizados también se incorporan al archivo antes de podarse del almacenamiento activo.

Los archivos comprimidos tienen un límite independiente definido por `LOCAL_SHELL_MCP_MAX_AUDIT_ARCHIVE_BYTES`, 512 MB de forma predeterminada. Al superarlo se eliminan primero los archivos más antiguos. Establézcalo en `0` para desactivar la retención comprimida a largo plazo. Las consultas recientes leen solo el hot log y consultan los archivos cuando se necesita historial.

## Limitaciones

Los registros de auditoría no son un sandbox. Ayudan a la trazabilidad, pero no impiden que un modelo conectado actúe dentro de la autoridad configurada.
