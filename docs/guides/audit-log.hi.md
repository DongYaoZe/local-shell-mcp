<!-- i18n-source-sha256: 25bb55459e83ee02b923876bad8d288c7a2055c4474f2098d58ce1e4a5e72605 -->
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

सक्रिय `audit.jsonl` को डिफ़ॉल्ट रूप से `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES` द्वारा 20 MB तक सीमित रखा जाता है। retention maintenance के दौरान पुराने records हटाए नहीं जाते, बल्कि self-contained Zstandard archives `audit-archive/*.jsonl.zst` में भेजे जाते हैं; external बड़े audit payloads भी hot store से prune होने से पहले archive में शामिल किए जाते हैं।

Compressed archives के लिए अलग `LOCAL_SHELL_MCP_MAX_AUDIT_ARCHIVE_BYTES` सीमा है, जिसका डिफ़ॉल्ट 512 MB है। सीमा पार होने पर सबसे पुराने archives पहले हटते हैं। `0` सेट करने पर long-term compressed retention बंद हो जाता है। Web UI, Activity/Audit queries और `audit_tail` केवल सक्रिय hot log पढ़ते हैं। Compressed archives retention या export के लिए cold storage हैं और सामान्य UI queries उन्हें अपने-आप decompress नहीं करतीं।

## सीमाएँ

Audit logs sandbox नहीं हैं। वे traceability में मदद करते हैं, लेकिन connected model को उसकी configured authority के भीतर actions लेने से नहीं रोकते।
