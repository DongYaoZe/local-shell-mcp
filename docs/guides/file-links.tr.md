<!-- i18n-source-sha256: d758caead1c922385409aceebf498662f25f4cbf252a48d65b29d91f07e5a173 -->
# Dosya bağlantıları

`local-shell-mcp`, kontrollü workspace içindeki dosyaları yüksek entropili bearer URL’ler üzerinden sunabilir. AI raporlar, arşivler, PDF’ler, screenshots veya chat’ten indirilmesi ya da görüntülenmesi gereken başka artifacts oluşturduğunda yararlıdır.

## Dosya bağlantıları ne zaman kullanılır

Şunlar için kullanın:

- Oluşturulan PDF veya raporlar.
- Screenshots ve browser artifacts.
- Build çıktıları.
- Chat’e yapıştırmak için çok büyük logs.
- Elle inceleme için hazırlanmış arşivler.

Secrets, private keys, credential depoları veya ilgisiz kişisel veriler için dosya bağlantısı kullanmayın.

## Tipik akış

1. `/workspace` altında bir dosya oluşturun veya bulun.
2. TTL ve isteğe bağlı download limit ile `link_create` çağırın. Dosya tarayıcıda veya Markdown image olarak doğrudan render edilmeliyse `inline=true` ayarlayın; varsayılan `false` olup attachment download zorlar.
3. Dönen URL’yi paylaşın.
4. Artık gerekmediğinde bağlantıyı revoke edin.

## İlgili araçlar

| Tool | Amaç |
|---|---|
| `link_create` | Workspace dosyası için tokenized URL oluşturmak. |
| `link_list` | Aktif bağlantıları göstermek. |
| `link_revoke` | Süresi dolmadan bağlantıyı devre dışı bırakmak. |

## Kontroller

Yapılandırma seçenekleri şunları içerir:

- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_ENABLED`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_MAX_DOWNLOADS`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_FILE_BYTES`

Hassas artifacts için daha kısa TTL kullanın ve bağlantı tek bir alıcıya yönelikse maximum download count belirleyin.

## Güvenlik notları

Dosya bağlantıları bearer URL’lerdir. URL’ye sahip herkes dosyayı bağlantı süresi dolana, download limit’e ulaşana veya revoke edilene kadar indirebilir. Bunları geçici secrets gibi ele alın. Inline response’lar CSP sandbox ve `X-Content-Type-Options: nosniff` içerir; böylece aktif formatlar LSM origin’e erişemez veya unsandboxed same-origin content olarak çalışamaz.
