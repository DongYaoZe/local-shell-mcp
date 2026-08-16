<!-- i18n-source-sha256: 6e76d0746c53eeef3e770417742a44e122c6484afd0d91ddf6a4995387085c74 -->
# Genel MCP client’lar

`local-shell-mcp`, ChatGPT ve diğer MCP client’lar tarafından kullanılabilir. Client, HTTP üzerinden bağlanmayı veya sunucuyu stdio üzerinden başlatmayı seçer.

## HTTP MCP client

Sunucu zaten çalışıyorsa HTTP mode kullanın:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode mcp
```

Yerel endpoint:

```text
http://127.0.0.1:8765/mcp
```

Ağ endpoint’i:

```text
https://your-public-host.example.com/mcp
```

Güvenilir localhost dışından erişilebilen tüm endpoint’lerde OAuth kullanın.

## Stdio MCP client

Client sunucu sürecini kendisi başlatıyorsa stdio mode kullanın:

```bash
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/path/to/workspace local-shell-mcp --mode stdio
```

Tipik client yapılandırması:

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

Client schema’ları değişir. Bazıları bu bölümü `mcpServers` olarak adlandırır, bazıları başka bir ad kullanır.

## İlk güvenli kontrol

Yeni bağlanan bir client için şununla başlayın:

```text
Call environment_get, then file_tree on the workspace root. Do not modify files yet.
```

Ardından açık düzenleme, test ve Git kuralları olan sınırlandırılmış bir görev çalıştırın.
