<!-- i18n-source-sha256: d758caead1c922385409aceebf498662f25f4cbf252a48d65b29d91f07e5a173 -->
# Linki do plików

`local-shell-mcp` może udostępniać pliki z kontrolowanego workspace za pomocą bearer URL o wysokiej entropii. Jest to przydatne, gdy AI tworzy raporty, archiwa, PDF-y, screenshots lub inne artifacts, które trzeba pobrać z chatu albo w nim wyświetlić.

## Kiedy używać linków do plików

Używaj ich do:

- Wygenerowanych PDF-ów lub raportów.
- Screenshots i browser artifacts.
- Wyników build.
- Logów zbyt dużych do wklejenia.
- Archiwów przygotowanych do ręcznej inspekcji.

Nie używaj linków do plików dla secrets, private keys, magazynów credentials ani niezwiązanych danych osobowych.

## Typowy przebieg

1. Wygeneruj lub znajdź plik pod `/workspace`.
2. Wywołaj `link_create` z TTL i opcjonalnym limitem pobrań. Ustaw `inline=true`, gdy plik ma renderować się bezpośrednio w przeglądarce lub jako obraz Markdown; domyślnie jest `false`, co wymusza attachment download.
3. Udostępnij zwrócony URL.
4. Unieważnij link, gdy przestanie być potrzebny.

## Powiązane narzędzia

| Tool | Zastosowanie |
|---|---|
| `link_create` | Utworzyć tokenizowany URL dla pliku workspace. |
| `link_list` | Pokazać aktywne linki. |
| `link_revoke` | Wyłączyć link przed wygaśnięciem. |

## Kontrole

Opcje konfiguracji obejmują:

- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_ENABLED`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_MAX_DOWNLOADS`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_FILE_BYTES`

Dla wrażliwych artifacts używaj krótszych TTL i ustaw maximum download count, gdy link jest przeznaczony dla jednego odbiorcy.

## Uwagi o bezpieczeństwie

Linki do plików są bearer URL. Każdy, kto ma URL, może pobrać plik do czasu wygaśnięcia linku, osiągnięcia download limit lub jego unieważnienia. Traktuj je jak tymczasowe secrets. Inline responses zawierają CSP sandbox i `X-Content-Type-Options: nosniff`, więc aktywne formaty nie mogą uzyskać dostępu do LSM origin ani wykonać się jako unsandboxed same-origin content.
