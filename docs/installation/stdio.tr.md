<!-- i18n-source-sha256: a3d2dc835f99feed33a73ae3dd880dabab04a37d7461b99f1fa49c33ba0506e1 -->
# Stdio runtime

Stdio mode, `local-shell-mcp` sürecini child process olarak başlatan ve standart giriş/çıkış üzerinden iletişim kuran yerel MCP client’lar içindir.

Bu bir genel HTTP deployment değildir. ChatGPT web/app, makinenizde process başlatamadığı için bunu doğrudan kullanamaz.

## stdio ne zaman kullanılır

Şu durumlarda stdio mode kullanın:

- MCP client command-based server definitions destekliyorsa.
- Client ve kontrol edilen workspace aynı makinedeyse.
- OAuth, genel HTTPS, reverse proxy veya tunnel gerekmiyorsa.
- Server lifecycle’ı client’ın yönetmesini istiyorsanız.

Şu durumlarda stdio mode kullanmayın:

- Client ChatGPT web/app ise.
- Birden fazla remote client aynı server’a ihtiyaç duyuyorsa.
- HTTP üzerinden tokenized file download gerekiyorsa.
- HTTP üzerinden sunulan remote-worker join route gerekiyorsa.

## Komut

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Genel bir MCP client yapılandırması genellikle şunu içerir:

```json
{
  "mcpServers": {
    "local-shell-mcp": {
      "command": "local-shell-mcp",
      "args": ["--mode", "stdio"],
      "env": {
        "LOCAL_SHELL_MCP_WORKSPACE_ROOT": "/path/to/workspace"
      }
    }
  }
}
```

Schema’yı client’ınıza uyarlayın. Bazı client’lar bu bölümü `servers`, `tools`, `mcpServers` veya `contextServers` olarak adlandırır.

## HTTP mode ile davranış farkları

| Alan | Stdio mode | HTTP MCP mode |
|---|---|---|
| Transport | stdin/stdout | HTTP streamable MCP endpoint |
| Endpoint | Yok | `/mcp` |
| OAuth | Gerekmez | Genel kullanım için önerilir |
| Health endpoint | Yok | `/healthz`, `/readyz` |
| Genel ChatGPT kullanımı | Hayır | Evet, HTTPS arkasında |
| Server lifecycle | client process başlatır | process/runtime’ı siz yönetirsiniz |

Bunun dışında tool surface, configuration ve client support sınırları içinde aynı server-side implementation’ı kullanır.

## Güvenlik notları

Stdio mode çoğu zaman host üzerinde MCP client ile aynı kullanıcı olarak doğrudan çalışır. Dar bir workspace root kullanın ve geniş filesystem access’ten kaçının. stdio kendisi disposable container veya VM içinde çalışmıyorsa full-container mode kapalı kalmalıdır.
