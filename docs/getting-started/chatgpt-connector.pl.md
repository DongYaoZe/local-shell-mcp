<!-- i18n-source-sha256: 2ad041876ff35987d7fdd66cbcdc7ed3956f427e8d8b185f354555cdc29a1b8a -->
# Łącznik ChatGPT

Ta strona opisuje ChatGPT jako połączenie client. Nie wybiera runtime. Przed użyciem uruchom serwer przez Docker, VS Code extension, binary lub instalację Python.

`local-shell-mcp` jest przeznaczony dla ChatGPT Developer Mode i pełnych klientów MCP. Endpoint MCP bezpośrednio udostępnia normalny zestaw narzędzi LSM.

## Wymagania runtime

Najpierw wybierz i uruchom jeden runtime:

| Runtime | Strona |
|---|---|
| Docker Compose | [Docker Compose runtime](../installation/docker.md) |
| VS Code extension | [VS Code extension runtime](../installation/vscode-extension.md) |
| Standalone binary | [Standalone binary runtime](../installation/binary.md) |
| Python / pipx / source | [Python runtimes](../installation/python.md) |

Następnie udostępnij ten runtime przez ścieżkę sieciową osiągalną dla ChatGPT. Zobacz [network connectivity](../clients/connectivity.md).

## Publiczny URL

ChatGPT musi osiągać serwer przez HTTPS. MCP endpoint to:

```text
https://your-public-host.example.com/mcp
```

Upewnij się, że `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` odpowiada public origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Nie dodawaj `/mcp` do `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## Konfiguracja OAuth

Zalecane ustawienia publiczne:

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

Access tokens domyślnie nie wygasają, ponieważ długie coding sessions mogą przekraczać krótkie lifetime tokenów. W razie potrzeby revoke dostęp przez rotację JWT secret albo redeploy z nowym state.

## Dodawanie connectora

1. Otwórz ustawienia connectora ChatGPT lub Developer Mode MCP.
2. Dodaj custom MCP server.
3. Wprowadź MCP URL: `https://your-public-host.example.com/mcp`.
4. Ukończ OAuth.
5. Zatwierdź tool surface.

## Live Workspace MCP App

Clienty ChatGPT z obsługą MCP Apps mogą renderować `local-shell-mcp` jako interaktywny execution workspace. Poproś ChatGPT o jednorazowe otwarcie Live Workspace, gdy przydaje się widoczność w czasie rzeczywistym lub współpraca z człowiekiem; później app sam reconnectuje bez powtarzanych wywołań `workspace_open`.

Live Workspace jest celowo oddzielony od reasoning modelu. Pokazuje obserwowalny execution state i wspólne resources:

- **Activity** pokazuje starty, zakończenia i błędy MCP tools oraz działania człowieka.
- **Terminal** podłącza się do istniejącego persistent shell backend i pokazuje live PTY output.
- **Files** przegląda, preview, edit, create i delete lokalne lub zdalne workspace files.
- **Diff** pokazuje staged/unstaged Git changes i może odesłać current diff do ChatGPT do review.
- **Jobs** pokazuje managed jobs i persistent sessions.
- **Remotes** pokazuje workers oraz invite, rename i revoke, gdy remote support jest aktywny.
- **Audit** udostępnia ostatnie structured MCP audit records.

Live Workspace zawsze jest collaborative: ChatGPT i człowiek mogą jednocześnie zmieniać ten sam workspace. Gdy host wspiera tę funkcję, otwiera się jako floating PiP-style window i przełącza między fullscreen a windowed. Nie ma osobnego state observe/takeover.

Views files, diff, audit i activity mogą przekazać wybrany operational context do następnego model turn przez MCP Apps bridge. Jest to jawnie współdzielony context; UI nie ujawnia ani nie rekonstruuje private model reasoning.

### Sieć i bezpieczeństwo

Renderowana MCP App łączy się bezpośrednio ze swojego sandbox do skonfigurowanego service origin dla terminal/event traffic o małym opóźnieniu. Dlatego `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` musi być HTTPS origin osiągalnym przez browser ChatGPT. MCP endpoint pozostaje `https://your-public-host.example.com/mcp`.

Otwarcie workspace powoduje wydanie losowego, krótkotrwałego bearer tokenu Live Workspace. Token jest zwracany wyłącznie w metadata wyniku MCP przeznaczonej dla renderowanej aplikacji, nie trafia do structured content widocznego dla modelu i jest akceptowany tylko przez API human/live UI. Automatyczne ponowne dołączenie do tego samego `live_id` ponownie wykorzystuje bieżącą credential, dzięki czemu reconnecting views nie unieważniają się wzajemnie; przenosi również bieżący logiczny `session_id`, co pozwala odtworzyć trwałą Session nawet po utracie in-memory stanu Live Workspace. Jawne nowe wywołanie `workspace_open` rotuje credential. Osadzona aplikacja nie korzysta z browser cookies ani ambient credentials.

Clienty bez MCP Apps mogą ignorować UI metadata. Wszystkie normalne MCP data tools pozostają dostępne i zachowują to samo działanie.

## Pierwszy prompt

```text
Użyj local-shell-mcp. Najpierw wywołaj environment_get, potem wylistuj root workspace. Jeszcze nie modyfikuj plików.
```

To sprawdza łączność bez zmian.

## Zalecane reguły pracy

Daj modelowi jasne ograniczenia:

- Pracuj wewnątrz `/workspace`, chyba że wyraźnie wskazano inaczej.
- Uruchamiaj tests przed commit.
- Użyj `secret_scan` przed push.
- Używaj `link_create` tylko dla plików bezpiecznych do udostępnienia.
- Dla długich procesów preferuj persistent shell sessions.
- Podsumuj wszystkie polecenia, które zmieniły pliki.

## Problemy z tool discovery

Jeśli ChatGPT uwierzytelnia się, ale nie pokazuje oczekiwanych tools:

- Potwierdź, że endpoint kończy się na `/mcp`.
- Sprawdź `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY`.
- Sprawdź reverse proxy headers i request body limits.
- Przejrzyj `docker compose logs --tail=200 local-shell-mcp`.
- Potwierdź, że service działa w mode `mcp` lub `both`.

## Uwagi bezpieczeństwa

Publiczne deploymenty muszą mieć włączone OAuth. Nie udostępniaj pełnych MCP tools bez uwierzytelnienia w publicznym Internecie. Traktuj każde zatwierdzone tool jako część faktycznych uprawnień podłączonego modelu.
