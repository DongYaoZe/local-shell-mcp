<!-- i18n-source-sha256: d758caead1c922385409aceebf498662f25f4cbf252a48d65b29d91f07e5a173 -->
# Link ai file

`local-shell-mcp` può esporre file dal workspace controllato tramite bearer URL ad alta entropia. È utile quando l’IA genera report, archivi, PDF, screenshots o altri artifacts che devono essere scaricati o visualizzati nella chat.

## Quando usare i link ai file

Usali per:

- PDF o report generati.
- Screenshots e browser artifacts.
- Output di build.
- Log troppo grandi da incollare.
- Archivi preparati per ispezione manuale.

Non usare link ai file per secrets, private keys, archivi di credentials o dati personali non pertinenti.

## Flusso tipico

1. Genera o individua un file sotto `/workspace`.
2. Chiama `link_create` con un TTL e un limite di download opzionale. Imposta `inline=true` quando il file deve essere visualizzato direttamente nel browser o come immagine Markdown; il valore predefinito è `false`, che forza il download come attachment.
3. Condividi l’URL restituito.
4. Revoca il link quando non serve più.

## Strumenti rilevanti

| Tool | Scopo |
|---|---|
| `link_create` | Creare un URL tokenizzato per un file del workspace. |
| `link_list` | Mostrare i link attivi. |
| `link_revoke` | Disabilitare un link prima della scadenza. |

## Controlli

Le opzioni di configurazione includono:

- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_ENABLED`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_MAX_DOWNLOADS`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_FILE_BYTES`

Usa TTL più brevi per artifacts sensibili e imposta un maximum download count quando il link è destinato a un solo destinatario.

## Note di sicurezza

I link ai file sono bearer URL. Chiunque possieda l’URL può scaricare il file finché il link non scade, raggiunge il download limit o viene revocato. Trattali come secrets temporanei. Le risposte inline includono CSP sandbox e `X-Content-Type-Options: nosniff`, impedendo ai formati attivi di accedere al LSM origin o di eseguirsi come contenuto same-origin senza sandbox.
