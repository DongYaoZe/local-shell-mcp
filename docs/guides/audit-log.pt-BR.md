<!-- i18n-source-sha256: a5b96c45536a4d18d1e09f2c47a873e568d0594539aa630ed159b4ddbf3cc25d -->
# Log de auditoria

`local-shell-mcp` grava entradas de auditoria estruturadas para ajudar a reconstruir o que um client conectado fez.

Caminho padrão:

```text
/workspace/.local-shell-mcp/audit.jsonl
```

## O que é registrado

As entradas de auditoria abrangem eventos como:

- Início/fim de tool calls.
- Metadados de execução de comandos.
- Timeouts e erros tratados.
- Registro de remote workers e atividade de jobs.
- Criação e revogação de file links.
- Eventos relacionados à autenticação, quando aplicável.

Argumentos sensíveis são ocultados quando o servidor consegue identificá-los.

## Lendo o log

Use a ferramenta MCP:

```text
audit_tail
```

Ou inspecione diretamente:

```bash
tail -n 100 /workspace/.local-shell-mcp/audit.jsonl
```

## Uso operacional

Logs de auditoria são especialmente úteis para:

- Revisar comandos que alteraram arquivos.
- Verificar se um remote worker foi usado.
- Depurar falhas inesperadas.
- Detectar exposição acidental de file links.
- Apoiar a resposta a incidentes após um erro de deployment público.

## Retenção

O `audit.jsonl` ativo é limitado por padrão a 20 MB por `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES`. Durante a manutenção de retenção, registros antigos são movidos para arquivos Zstandard autocontidos em `audit-archive/*.jsonl.zst` em vez de serem descartados; audit payloads grandes e externalizados também são incorporados ao arquivo antes de serem removidos do armazenamento ativo.

Os arquivos compactados têm um limite separado definido por `LOCAL_SHELL_MCP_MAX_AUDIT_ARCHIVE_BYTES`, 512 MB por padrão. Ao ultrapassá-lo, os arquivos mais antigos são removidos primeiro. Defina como `0` para desativar a retenção compactada de longo prazo. Consultas recentes leem apenas o hot log e acessam os arquivos somente quando precisam de histórico antigo.

## Limitações

Logs de auditoria não são um sandbox. Eles ajudam na rastreabilidade, mas não impedem que um modelo conectado aja dentro da autoridade configurada.
