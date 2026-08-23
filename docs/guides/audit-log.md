# Audit log

`local-shell-mcp` writes structured audit entries to help reconstruct what a connected client did.

Default path:

```text
/workspace/.local-shell-mcp/audit.jsonl
```

## What is recorded

Audit entries cover events such as:

- Tool call start/end.
- Command execution metadata.
- Timeouts and handled errors.
- Remote worker registration and job activity.
- File-link creation and revocation.
- Authentication-related events where applicable.

Sensitive arguments are redacted where the server can identify them.

## Reading the log

Use the MCP tool:

```text
audit_tail
```

Or inspect directly:

```bash
tail -n 100 /workspace/.local-shell-mcp/audit.jsonl
```

## Operational use

Audit logs are most useful for:

- Reviewing commands that changed files.
- Checking whether a remote worker was used.
- Debugging unexpected failures.
- Detecting accidental exposure of file links.
- Supporting incident response after a public deployment mistake.

## Retention

The live `audit.jsonl` is bounded by `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES` (20 MB by default). When retention runs, older records are moved into self-contained Zstandard archives under `audit-archive/*.jsonl.zst` instead of being discarded. Large external audit payloads are embedded into the archive before their hot-store payload files are pruned.

Compressed archives are bounded separately by `LOCAL_SHELL_MCP_MAX_AUDIT_ARCHIVE_BYTES` (512 MB by default). Once that compressed budget is exceeded, the oldest archives are removed first. Set the archive budget to `0` to disable long-term compressed retention. Recent UI reads stay on the hot log; historical searches and entry-detail lookups consult archives when the requested record is no longer live.

## Limitations

Audit logs are not a sandbox. They help with traceability, but they do not prevent a connected model from taking actions within its configured authority.
