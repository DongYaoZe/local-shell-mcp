<!-- i18n-source-sha256: a5b96c45536a4d18d1e09f2c47a873e568d0594539aa630ed159b4ddbf3cc25d -->
# Denetim günlüğü

`local-shell-mcp`, bağlı bir client’ın ne yaptığını yeniden oluşturmayı kolaylaştırmak için yapılandırılmış denetim kayıtları yazar.

Varsayılan yol:

```text
/workspace/.local-shell-mcp/audit.jsonl
```

## Kaydedilenler

Denetim kayıtları şunlar gibi olayları kapsar:

- Tool call başlangıcı/bitişi.
- Komut yürütme meta verileri.
- Timeout’lar ve işlenmiş hatalar.
- Remote worker kaydı ve job etkinliği.
- File link oluşturma ve iptal.
- Uygun olduğunda kimlik doğrulamayla ilgili olaylar.

Sunucunun tanımlayabildiği hassas argümanlar maskelenir.

## Günlüğü okuma

MCP aracını kullanın:

```text
audit_tail
```

Veya doğrudan inceleyin:

```bash
tail -n 100 /workspace/.local-shell-mcp/audit.jsonl
```

## Operasyonel kullanım

Denetim günlükleri özellikle şunlar için yararlıdır:

- Dosyaları değiştiren komutları incelemek.
- Remote worker kullanılıp kullanılmadığını kontrol etmek.
- Beklenmedik hataları ayıklamak.
- File link’lerin yanlışlıkla açığa çıkmasını tespit etmek.
- Genel deployment hatasından sonra incident response’u desteklemek.

## Saklama

Etkin `audit.jsonl`, varsayılan olarak `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES` ile 20 MB ile sınırlandırılır. Retention bakımı sırasında eski kayıtlar silinmek yerine kendi kendine yeterli Zstandard arşivleri olan `audit-archive/*.jsonl.zst` dosyalarına taşınır; dışarı alınmış büyük audit payloads da hot store’dan temizlenmeden önce arşive eklenir.

Sıkıştırılmış arşivler için ayrı `LOCAL_SHELL_MCP_MAX_AUDIT_ARCHIVE_BYTES` sınırı vardır ve varsayılanı 512 MB’dir. Sınır aşılırsa en eski arşivler önce silinir. `0` değeri uzun süreli sıkıştırılmış saklamayı kapatır. Güncel sorgular yalnızca hot log’u okur, eski geçmiş gerektiğinde arşivlere başvurur.

## Sınırlamalar

Denetim günlükleri sandbox değildir. İzlenebilirliğe yardımcı olur ancak bağlı modelin yapılandırılmış yetkisi içinde işlem yapmasını engellemez.
