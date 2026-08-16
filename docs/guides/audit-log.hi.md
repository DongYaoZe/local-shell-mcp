<!-- i18n-source-sha256: 4aec137923c38de0ed4a1b760b5dbd6ce99090d508ce3fe838d35ad44b4ba4f1 -->
# Audit log

`local-shell-mcp` structured audit entries लिखता है ताकि यह पुनर्निर्मित किया जा सके कि जुड़े हुए client ने क्या किया।

Default path:

```text
/workspace/.local-shell-mcp/audit.jsonl
```

## क्या रिकॉर्ड होता है

Audit entries में ऐसे events शामिल होते हैं:

- Tool call start/end.
- Command execution metadata.
- Timeouts और handled errors.
- Remote worker registration और job activity.
- File-link creation और revocation.
- लागू होने पर authentication-related events.

Server जिन sensitive arguments को पहचान सकता है उन्हें redact किया जाता है।

## Log पढ़ना

MCP tool उपयोग करें:

```text
audit_tail
```

या सीधे देखें:

```bash
tail -n 100 /workspace/.local-shell-mcp/audit.jsonl
```

## Operational use

Audit logs विशेष रूप से इन कार्यों में उपयोगी हैं:

- Files बदलने वाले commands की समीक्षा।
- यह जाँचना कि remote worker उपयोग हुआ या नहीं।
- Unexpected failures को debug करना।
- File links के accidental exposure का पता लगाना।
- Public deployment गलती के बाद incident response में सहायता।

## Retention

Log `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES` से bounded है। लंबे retention की आवश्यकता हो तो इसे rotate करें या बाहर export करें।

## सीमाएँ

Audit logs sandbox नहीं हैं। वे traceability में मदद करते हैं, लेकिन connected model को उसकी configured authority के भीतर actions लेने से नहीं रोकते।
