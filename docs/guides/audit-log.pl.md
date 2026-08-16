<!-- i18n-source-sha256: 4aec137923c38de0ed4a1b760b5dbd6ce99090d508ce3fe838d35ad44b4ba4f1 -->
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

Rozmiar dziennika ogranicza `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES`. Jeśli potrzebujesz dłuższej retencji, rotuj go lub eksportuj na zewnątrz.

## Ograniczenia

Dziennik audytu nie jest sandboxem. Pomaga w śledzeniu działań, ale nie zapobiega wykonywaniu przez podłączony model operacji w granicach skonfigurowanych uprawnień.
