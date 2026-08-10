# ChatGPT connector

This page covers ChatGPT as a client connection. It does not choose the runtime. Before using this page, run the server with Docker, the VS Code extension, a binary, or a Python install.

`local-shell-mcp` is designed for ChatGPT Developer Mode and full MCP clients. It also exposes read-only connector-style `search` and `fetch` tools for connector discovery.

## Runtime prerequisites

Pick and start one runtime first:

| Runtime | Page |
|---|---|
| Docker Compose | [Docker Compose runtime](../installation/docker.md) |
| VS Code extension | [VS Code extension runtime](../installation/vscode-extension.md) |
| Standalone binary | [Standalone binary runtime](../installation/binary.md) |
| Python / pipx / source | [Python runtimes](../installation/python.md) |

Then expose that runtime through a network path ChatGPT can reach. See [network connectivity](../clients/connectivity.md).

## Public URL

ChatGPT must reach the server over HTTPS. The MCP endpoint is:

```text
https://your-public-host.example.com/mcp
```

Make sure `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` matches the public origin:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

Do not include `/mcp` in `LOCAL_SHELL_MCP_PUBLIC_BASE_URL`.

## OAuth setup

Recommended public settings:

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

Access tokens do not expire by default because long coding sessions can exceed short token lifetimes. Revoke access by rotating the JWT secret or redeploying with a fresh state when needed.

## Adding the connector

1. Open ChatGPT connector or Developer Mode MCP settings.
2. Add a custom MCP server.
3. Enter the MCP URL: `https://your-public-host.example.com/mcp`.
4. Complete OAuth.
5. Approve the tool surface.

## Live Workspace MCP App

ChatGPT clients with MCP Apps support can render `local-shell-mcp` as an interactive execution workspace. Ask ChatGPT to open the Live Workspace once when real-time visibility or human collaboration would help; the app then reconnects itself instead of requiring repeated `open_live_workspace` calls.

The Live Workspace is intentionally separate from the model's reasoning. It shows observable execution state and shared resources:

- **Activity** shows MCP tool starts, completions, failures, and human actions.
- **Terminal** attaches to the existing persistent shell backend with live PTY output.
- **Files** browses, previews, edits, creates, and deletes local or remote workspace files.
- **Diff** shows staged and unstaged Git changes and can send the current diff back to ChatGPT for review.
- **Jobs** shows managed jobs and persistent sessions.
- **Remotes** shows workers and provides invitation, rename, and revoke actions when remote support is enabled.
- **Audit** exposes recent structured MCP audit records.

The Live Workspace is always collaborative: ChatGPT and the human can modify the same workspace concurrently. It opens as a floating PiP-style window when the host supports it and can be toggled to fullscreen and back. There is no separate observe/takeover state.

File, diff, audit, and activity views can send selected operational context to the next model turn through the MCP Apps bridge. This is explicit shared context; the UI does not expose or reconstruct private model reasoning.

### Networking and security

The rendered MCP App connects directly from its sandbox to the configured service origin for low-latency terminal and event traffic. Therefore `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` must be the HTTPS origin that the ChatGPT browser can reach. The MCP endpoint itself remains `https://your-public-host.example.com/mcp`.

Opening the workspace issues a random, short-lived Live Workspace bearer token. The token is returned only in MCP result metadata intended for the rendered app, is not included in model-visible structured content, and is accepted only by the human/live UI API surfaces. Automatic app reattachment to the same `live_id` reuses the current credential so reconnecting views cannot invalidate one another; it also carries the current logical `session_id`, allowing the view to recover its durable Session even if in-memory Live Workspace state was lost. An explicit new `open_live_workspace` call rotates the credential. The embedded app does not use browser cookies or ambient credentials.

Clients that do not implement MCP Apps can ignore the UI metadata. All normal MCP data tools remain available and keep the same behavior.

## First prompt

```text
Use local-shell-mcp. First call environment_info, then list the workspace root. Do not modify files yet.
```

This verifies connectivity without making changes.

## Recommended operating rules

Give the model clear constraints:

- Work inside `/workspace` unless explicitly told otherwise.
- Run tests before committing.
- Use `secret_scan` before pushing.
- Use `create_file_link` only for files that are safe to share.
- Prefer persistent shell sessions for long-running processes.
- Summarize all commands that changed files.

## Tool discovery issues

If ChatGPT can authenticate but does not show expected tools:

- Confirm the endpoint ends in `/mcp`.
- Check `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY`.
- Check reverse proxy headers and request body limits.
- Inspect `docker compose logs --tail=200 local-shell-mcp`.
- Confirm the service is in `mcp` or `both` mode.

## Safety notes

Public deployments must keep OAuth enabled. Do not expose unauthenticated full MCP tools on the public internet. Treat every approved tool as part of the connected model's effective authority.
