<!-- i18n-source-sha256: 4aec137923c38de0ed4a1b760b5dbd6ce99090d508ce3fe838d35ad44b4ba4f1 -->
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

O log é limitado por `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES`. Faça rotação ou exporte-o externamente se precisar de retenção longa.

## Limitações

Logs de auditoria não são um sandbox. Eles ajudam na rastreabilidade, mas não impedem que um modelo conectado aja dentro da autoridade configurada.
