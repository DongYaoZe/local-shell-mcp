<!-- i18n-source-sha256: 87dd7fb66311534dcd5a7217bba8c809f71fe6189e8c39b3e265da923cc82d22 -->
# API REST

La interfaz principal es MCP en `/mcp`. También hay una superficie REST para health checks, file links y operaciones de servicio seleccionadas.

## Salud

```http
GET /healthz
```

Devuelve la salud del servidor y su estado básico.

## MCP

```http
POST /mcp
```

Endpoint MCP Streamable HTTP utilizado por ChatGPT y otros MCP client.

## Llamadas de herramientas mediante REST

Las llamadas REST de herramientas usan envelopes coherentes para éxito y error. Los errores de validación devuelven payloads estructurados con `ok: false` en lugar de excepciones sin procesar del framework.

## Agent Skills

El registro fijo de Skills también está disponible mediante REST:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```

Los cambios en los directorios de Skill se ven en la siguiente llamada y no modifican la lista de herramientas MCP.

## Enlaces de archivos

Las descargas de archivos tokenizadas se sirven mediante la aplicación HTTP integrada. Los enlaces son bearer URL con TTL, límite máximo de descargas opcional y soporte de revocación.

## Autenticación

Los despliegues públicos deben usar OAuth. Se puede habilitar el bypass de localhost para desarrollo, pero el acceso público sin autenticar no es seguro.
