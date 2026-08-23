<!-- i18n-source-sha256: a5b96c45536a4d18d1e09f2c47a873e568d0594539aa630ed159b4ddbf3cc25d -->
# Dziennik audytu

`local-shell-mcp` zapisuje ustrukturyzowane wpisy audytu, aby ułatwić odtworzenie działań podłączonego client.

Domyślna ścieżka:

```text
/workspace/.local-shell-mcp/audit.jsonl
```

## Co jest rejestrowane

Wpisy audytu obejmują zdarzenia takie jak:

- Początek/koniec tool call.
- Metadane wykonywania poleceń.
- Timeouty i obsłużone błędy.
- Rejestracja remote worker i aktywność jobów.
- Tworzenie i unieważnianie file links.
- Zdarzenia związane z uwierzytelnianiem, gdy ma to zastosowanie.

Wrażliwe argumenty są redagowane, jeśli serwer potrafi je rozpoznać.

## Odczyt dziennika

Użyj narzędzia MCP:

```text
audit_tail
```

Lub sprawdź plik bezpośrednio:

```bash
tail -n 100 /workspace/.local-shell-mcp/audit.jsonl
```

## Zastosowanie operacyjne

Dzienniki audytu są szczególnie przydatne do:

- Przeglądania poleceń, które zmieniły pliki.
- Sprawdzania, czy użyto remote worker.
- Diagnozowania nieoczekiwanych awarii.
- Wykrywania przypadkowego ujawnienia file links.
- Wspierania incident response po błędzie publicznego deployment.

## Retencja

Aktywny `audit.jsonl` jest domyślnie ograniczony do 20 MB przez `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES`. Podczas obsługi retention starsze rekordy są przenoszone do samodzielnych archiwów Zstandard `audit-archive/*.jsonl.zst` zamiast usuwane; duże zewnętrzne audit payloads są również dołączane do archiwum przed usunięciem z hot store.

Skompresowane archiwa mają osobny limit `LOCAL_SHELL_MCP_MAX_AUDIT_ARCHIVE_BYTES`, domyślnie 512 MB. Po jego przekroczeniu najstarsze archiwa są usuwane jako pierwsze. Wartość `0` wyłącza długoterminową kompresowaną retencję. Zwykłe zapytania o najnowsze dane czytają tylko hot log, a archiwa są otwierane dopiero dla starszej historii.

## Ograniczenia

Dziennik audytu nie jest sandboxem. Pomaga w śledzeniu działań, ale nie zapobiega wykonywaniu przez podłączony model operacji w granicach skonfigurowanych uprawnień.
