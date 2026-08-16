<!-- i18n-source-sha256: 4aec137923c38de0ed4a1b760b5dbd6ce99090d508ce3fe838d35ad44b4ba4f1 -->
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

Il log è limitato da `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES`. Effettua la rotazione o esportalo esternamente se serve una conservazione prolungata.

## Limitazioni

I log di audit non sono una sandbox. Aiutano la tracciabilità, ma non impediscono a un modello connesso di agire entro l’autorità configurata.
