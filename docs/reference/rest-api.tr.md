<!-- i18n-source-sha256: 87dd7fb66311534dcd5a7217bba8c809f71fe6189e8c39b3e265da923cc82d22 -->
# REST API

Birincil interface `/mcp` üzerindeki MCP’dir. Health check, file link ve seçili service operation’lar için REST surface de vardır.

## Sağlık

```http
GET /healthz
```

Sunucu sağlığını ve temel durum bilgisini döndürür.

## MCP

```http
POST /mcp
```

ChatGPT ve diğer MCP client’ların kullandığı Streamable HTTP MCP endpoint.

## REST üzerinden araç çağrıları

REST araç çağrıları tutarlı başarı/hata envelopes kullanır. Doğrulama hataları ham framework istisnaları yerine yapılandırılmış `ok: false` payload döndürür.

## Agent Skills

Sabit Skills registry REST üzerinden de kullanılabilir:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```

Skill dizinlerindeki değişiklikler bir sonraki çağrıda görünür ve MCP araç listesini değiştirmez.

## Dosya bağlantıları

Token’lı dosya indirmeleri yerleşik HTTP uygulaması tarafından sunulur. Bağlantılar TTL, isteğe bağlı azami indirme sayısı ve iptal desteğine sahip bearer URL’lerdir.

## Kimlik doğrulama

Genel kullanıma açık dağıtımlarda OAuth kullanılmalıdır. Geliştirme için localhost bypass etkinleştirilebilir, ancak kimlik doğrulamasız genel erişim güvenli değildir.
