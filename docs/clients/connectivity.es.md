<!-- i18n-source-sha256: 3986da6ff877609189b0d88d363aff1f5f45445f0cfe5ffa608a31929078542c -->
# Conectividad de red

Los MCP client HTTP que estén fuera de la máquina necesitan un HTTPS origin accesible. Esta página trata del enrutamiento de red, no de qué runtime elegir.

El client endpoint normalmente termina en `/mcp`:

```text
https://your-public-host.example.com/mcp
```

La configuración de public base URL del servidor contiene solo el origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

No incluya `/mcp` en esa base URL.

## Opciones de conectividad

| Opción | Cuándo usarla |
|---|---|
| Compose tunnel sidecar | Docker Compose con el profile `tunnel` integrado |
| Tunnel externo | Cualquier runtime que deba ser accesible desde fuera de la red local |
| Caddy | TLS automático sencillo |
| Nginx o Nginx Proxy Manager | Infraestructura Nginx existente |
| Traefik | Enrutamiento container-native existente |

## Rutas

Reenvíe todo el origin al servidor en ejecución. Entre las rutas importantes se incluyen:

| Ruta | Propósito |
|---|---|
| `/mcp` | MCP Streamable HTTP endpoint |
| `/healthz`, `/readyz` | Comprobaciones de salud |
| `/.well-known/...` | Metadatos de descubrimiento del client |
| `/oauth/...` | Flujo de autorización del client |
| `/downloads/...` | Enlaces opcionales a archivos generados |
| `/join/...`, `/remote/...` | Flujo opcional de remote-worker |

## Comportamiento del proxy

El proxy debe conservar las rutas, reenviar los request bodies, admitir responses largas y evitar timeouts demasiado cortos.

## Comprobaciones

```bash
curl -i http://127.0.0.1:8765/healthz
curl -i https://your-public-host.example.com/healthz
```

## Errores frecuentes

| Error | Solución |
|---|---|
| Usar `https://host` en ChatGPT en vez de `https://host/mcp` | Añadir `/mcp` solo al client endpoint |
| Definir `LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://host/mcp` | Definir solo el origin |
| Enrutar únicamente `/mcp` | Enrutar todo el origin para que también funcionen el descubrimiento y la autorización |
| Ejecutar un host runtime con un workspace demasiado amplio | Usar un workspace limitado o Docker |

## Combinaciones sugeridas

| Runtime | Patrón de red |
|---|---|
| Docker Compose en un servidor | Reverse proxy existente o profile tunnel de Compose |
| Docker Compose en una máquina doméstica | Outbound tunnel |
| VS Code extension en un portátil | Tunnel temporal para la sesión |
| Binary en una VM | Reverse proxy en la VM o en el borde de red |
| Servidor de desarrollo Python/source | Normalmente solo localhost |
| Stdio mode | Sin ruta HTTP; usar un MCP client local |
