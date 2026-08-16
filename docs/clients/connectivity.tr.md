<!-- i18n-source-sha256: 3986da6ff877609189b0d88d363aff1f5f45445f0cfe5ffa608a31929078542c -->
# Ağ bağlantısı

Makine dışındaki HTTP MCP client’ların erişilebilir bir HTTPS origin’e ihtiyacı vardır. Bu sayfa ağ yönlendirmesini açıklar; hangi runtime’ın seçileceğini değil.

client endpoint normalde `/mcp` ile biter:

```text
https://your-public-host.example.com/mcp
```

Sunucunun public base URL ayarı yalnızca origin’i içerir:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Bu base URL’ye `/mcp` eklemeyin.

## Bağlantı seçenekleri

| Seçenek | Ne zaman kullanılır |
|---|---|
| Compose tunnel sidecar | Yerleşik `tunnel` profile ile Docker Compose |
| Harici tunnel | Yerel ağ dışından erişilmesi gereken herhangi bir runtime |
| Caddy | Basit otomatik TLS |
| Nginx veya Nginx Proxy Manager | Mevcut Nginx altyapısı |
| Traefik | Mevcut container-native yönlendirme |

## Yollar

Tüm origin’i çalışan sunucuya iletin. Önemli yollar şunlardır:

| Yol | Amaç |
|---|---|
| `/mcp` | MCP Streamable HTTP endpoint |
| `/healthz`, `/readyz` | Sağlık kontrolleri |
| `/.well-known/...` | Client discovery meta verileri |
| `/oauth/...` | Client yetkilendirme akışı |
| `/downloads/...` | İsteğe bağlı oluşturulan dosya bağlantıları |
| `/join/...`, `/remote/...` | İsteğe bağlı remote-worker akışı |

## Proxy davranışı

Proxy yolları korumalı, request body’leri iletmeli, uzun response’ları desteklemeli ve çok kısa timeout’lardan kaçınmalıdır.

## Kontroller

```bash
curl -i http://127.0.0.1:8765/healthz
curl -i https://your-public-host.example.com/healthz
```

## Yaygın hatalar

| Hata | Düzeltme |
|---|---|
| ChatGPT’de `https://host/mcp` yerine `https://host` kullanmak | `/mcp` yalnızca client endpoint’e eklenir |
| `LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://host/mcp` ayarlamak | Yalnızca origin’i ayarlayın |
| Yalnızca `/mcp` yolunu yönlendirmek | Discovery ve yetkilendirme yolları da çalışsın diye tüm origin’i yönlendirin |
| Host runtime’ı çok geniş bir workspace ile çalıştırmak | Dar workspace veya Docker kullanın |

## Önerilen eşleşmeler

| Runtime | Ağ deseni |
|---|---|
| Sunucuda Docker Compose | Mevcut reverse proxy veya Compose tunnel profile |
| Ev makinesinde Docker Compose | Outbound tunnel |
| Dizüstünde VS Code extension | Oturum için geçici tunnel |
| VM’de binary | VM veya ağ sınırında reverse proxy |
| Python/source dev server | Genellikle yalnızca localhost |
| Stdio mode | HTTP ağı yok; yerel MCP client kullanın |
