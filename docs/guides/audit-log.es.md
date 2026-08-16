<!-- i18n-source-sha256: 4aec137923c38de0ed4a1b760b5dbd6ce99090d508ce3fe838d35ad44b4ba4f1 -->
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

El registro está limitado por `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES`. Rótelo o expórtelo externamente si necesita conservarlo durante más tiempo.

## Limitaciones

Los registros de auditoría no son un sandbox. Ayudan a la trazabilidad, pero no impiden que un modelo conectado actúe dentro de la autoridad configurada.
