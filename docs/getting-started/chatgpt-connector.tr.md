<!-- i18n-source-sha256: 2ad041876ff35987d7fdd66cbcdc7ed3956f427e8d8b185f354555cdc29a1b8a -->
# ChatGPT bağlayıcısı

Bu sayfa ChatGPT’yi bir client bağlantısı olarak ele alır. Runtime seçmez. Bu sayfayı kullanmadan önce sunucuyu Docker, VS Code extension, binary veya Python kurulumu ile çalıştırın.

`local-shell-mcp`, ChatGPT Developer Mode ve tam MCP istemcileri için tasarlanmıştır. MCP endpoint normal LSM araç yüzeyini doğrudan sunar.

## Runtime önkoşulları

Önce bir runtime seçip başlatın:

| Runtime | Sayfa |
|---|---|
| Docker Compose | [Docker Compose runtime](../installation/docker.md) |
| VS Code extension | [VS Code extension runtime](../installation/vscode-extension.md) |
| Standalone binary | [Standalone binary runtime](../installation/binary.md) |
| Python / pipx / source | [Python runtimes](../installation/python.md) |

Ardından bu runtime’ı ChatGPT’nin ulaşabildiği bir network path üzerinden yayınlayın. Bkz. [network connectivity](../clients/connectivity.md).

## Genel URL

ChatGPT sunucuya HTTPS üzerinden ulaşmalıdır. MCP endpoint:

```text
https://your-public-host.example.com/mcp
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` değerinin public origin ile eşleştiğinden emin olun:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` içine `/mcp` eklemeyin.

## OAuth kurulumu

Önerilen genel ayarlar:

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

Uzun coding session’ları kısa token lifetime sürelerini aşabildiği için access token’lar varsayılan olarak sona ermez. Gerektiğinde JWT secret’ı döndürerek veya yeni state ile redeploy ederek erişimi revoke edin.

## Bağlayıcı ekleme

1. ChatGPT connector veya Developer Mode MCP ayarlarını açın.
2. Custom MCP server ekleyin.
3. MCP URL girin: `https://your-public-host.example.com/mcp`.
4. OAuth işlemini tamamlayın.
5. Tool surface’i onaylayın.

## Live Workspace MCP App

MCP Apps destekleyen ChatGPT client’ları `local-shell-mcp`yi etkileşimli execution workspace olarak render edebilir. Gerçek zamanlı görünürlük veya insan iş birliği yararlı olduğunda ChatGPT’den Live Workspace’i bir kez açmasını isteyin; ardından app tekrarlanan `workspace_open` çağrıları olmadan kendi kendine reconnect olur.

Live Workspace model reasoning’den özellikle ayrıdır. Gözlemlenebilir execution state ve paylaşılan resources gösterir:

- **Activity** MCP tool başlangıçlarını, tamamlanmalarını, hataları ve insan eylemlerini gösterir.
- **Terminal** mevcut persistent shell backend’e bağlanıp live PTY output gösterir.
- **Files** local veya remote workspace file’larını tarar, önizler, düzenler, oluşturur ve siler.
- **Diff** staged/unstaged Git changes gösterir ve current diff’i inceleme için ChatGPT’ye geri gönderebilir.
- **Jobs** managed jobs ve persistent sessions gösterir.
- **Remotes** workers gösterir ve remote support etkin olduğunda invite, rename ve revoke eylemleri sağlar.
- **Audit** son structured MCP audit records gösterir.

Live Workspace her zaman collaborative’dir: ChatGPT ve insan aynı workspace’i eşzamanlı değiştirebilir. Host desteklediğinde floating PiP-style window olarak açılır ve fullscreen ile windowed arasında geçebilir. Ayrı observe/takeover state yoktur.

Files, diff, audit ve activity view’ları seçili operational context’i MCP Apps bridge üzerinden sonraki model turn’e gönderebilir. Bu açıkça paylaşılan context’tir; UI private model reasoning’i açığa çıkarmaz veya yeniden oluşturmaz.

### Ağ ve güvenlik

Render edilen MCP App düşük gecikmeli terminal/event traffic için sandbox içinden yapılandırılmış service origin’e doğrudan bağlanır. Bu nedenle `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`, ChatGPT browser’ın ulaşabildiği HTTPS origin olmalıdır. MCP endpoint `https://your-public-host.example.com/mcp` olarak kalır.

Workspace açıldığında rastgele, kısa ömürlü bir Live Workspace bearer token üretilir. Token yalnızca render edilen app için MCP result metadata içinde döner, model-visible structured content içine girmez ve yalnız human/live UI API’leri tarafından kabul edilir. Aynı `live_id` için otomatik yeniden bağlanma mevcut credential’ı yeniden kullanır; böylece reconnect eden view’lar birbirini geçersiz kılmaz. Ayrıca güncel mantıksal `session_id` taşınır; bu sayede in-memory Live Workspace state kaybolsa bile kalıcı Session geri alınabilir. Açıkça yapılan yeni bir `workspace_open` çağrısı credential’ı döndürür. Gömülü app browser cookie veya ambient credential kullanmaz.

MCP Apps uygulamayan client’lar UI metadata’yı yok sayabilir. Tüm normal MCP data tools kullanılabilir kalır ve davranışı değişmez.

## İlk prompt

```text
local-shell-mcp kullan. Önce environment_get çağır, sonra workspace root’u listele. Henüz dosyaları değiştirme.
```

Bu, değişiklik yapmadan bağlantıyı doğrular.

## Önerilen çalışma kuralları

Modele açık sınırlar verin:

- Açıkça aksi söylenmedikçe `/workspace` içinde çalış.
- Commit öncesi tests çalıştır.
- Push öncesi `secret_scan` kullan.
- `link_create` yalnızca paylaşılması güvenli dosyalarda kullan.
- Uzun süreçler için persistent shell sessions tercih et.
- Dosya değiştiren tüm komutları özetle.

## Tool discovery sorunları

ChatGPT authenticate oluyor ancak beklenen tools görünmüyorsa:

- Endpoint’in `/mcp` ile bittiğini doğrulayın.
- `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY` ayarını kontrol edin.
- Reverse proxy headers ve request body limits değerlerini kontrol edin.
- `docker compose logs --tail=200 local-shell-mcp` çıktısını inceleyin.
- Service’in `mcp` veya `both` mode’da olduğunu doğrulayın.

## Güvenlik notları

Genel deployment’larda OAuth etkin kalmalıdır. Kimlik doğrulamasız tam MCP tools’u açık İnternet’e sunmayın. Onaylanan her tool’u bağlı modelin etkin yetkisinin bir parçası sayın.
