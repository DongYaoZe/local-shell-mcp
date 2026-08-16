<!-- i18n-source-sha256: 4aec137923c38de0ed4a1b760b5dbd6ce99090d508ce3fe838d35ad44b4ba4f1 -->
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

Günlük `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES` ile sınırlandırılır. Uzun süre saklama gerekiyorsa rotate edin veya dışarı export edin.

## Sınırlamalar

Denetim günlükleri sandbox değildir. İzlenebilirliğe yardımcı olur ancak bağlı modelin yapılandırılmış yetkisi içinde işlem yapmasını engellemez.
