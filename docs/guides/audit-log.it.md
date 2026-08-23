<!-- i18n-source-sha256: 25bb55459e83ee02b923876bad8d288c7a2055c4474f2098d58ce1e4a5e72605 -->
# Log di audit

`local-shell-mcp` scrive voci di audit strutturate per aiutare a ricostruire ciò che ha fatto un client connesso.

Percorso predefinito:

```text
/workspace/.local-shell-mcp/audit.jsonl
```

## Cosa viene registrato

Le voci di audit coprono eventi quali:

- Inizio/fine delle tool call.
- Metadati di esecuzione dei comandi.
- Timeout ed errori gestiti.
- Registrazione dei remote worker e attività dei job.
- Creazione e revoca dei file link.
- Eventi di autenticazione quando applicabili.

Gli argomenti sensibili vengono oscurati quando il server è in grado di identificarli.

## Lettura del log

Usa lo strumento MCP:

```text
audit_tail
```

Oppure ispezionalo direttamente:

```bash
tail -n 100 /workspace/.local-shell-mcp/audit.jsonl
```

## Uso operativo

I log di audit sono particolarmente utili per:

- Esaminare i comandi che hanno modificato file.
- Verificare se è stato usato un remote worker.
- Diagnosticare errori inattesi.
- Rilevare l’esposizione accidentale di file link.
- Supportare l’incident response dopo un errore di deployment pubblico.

## Conservazione

Il file `audit.jsonl` attivo è limitato per impostazione predefinita a 20 MB da `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES`. Durante la manutenzione della retention, i record più vecchi vengono spostati in archivi Zstandard autosufficienti `audit-archive/*.jsonl.zst` invece di essere eliminati; anche i grandi audit payload esternalizzati vengono inclusi nell’archivio prima della pulizia dello storage attivo.

Gli archivi compressi hanno un limite separato definito da `LOCAL_SHELL_MCP_MAX_AUDIT_ARCHIVE_BYTES`, pari a 512 MB per impostazione predefinita. Superato il limite, vengono eliminati prima gli archivi più vecchi. Impostare `0` per disabilitare la conservazione compressa a lungo termine. La Web UI, le query Activity/Audit e `audit_tail` leggono solo l’hot log attivo. Gli archivi compressi sono cold storage per conservazione o esportazione e non vengono decompressi automaticamente dalle normali query della UI.

## Limitazioni

I log di audit non sono una sandbox. Aiutano la tracciabilità, ma non impediscono a un modello connesso di agire entro l’autorità configurata.
