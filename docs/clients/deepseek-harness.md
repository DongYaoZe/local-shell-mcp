# DeepSeek Harness (DSH)

`local-shell-mcp` can be installed directly as a DeepSeek Harness plugin bundle. The bundle uses DSH's official `@deepseek-ai/dsh-mcp-client` and connects to the normal LSM Streamable HTTP endpoint, so LSM remains the authority for its workspace, remote workers, browser sessions, dynamic MCP registry, file links, and audit state.

## Install

Run an LSM service first. A same-host service using the default port works without extra DSH configuration:

```bash
local-shell-mcp --mode mcp
```

Then install this repository into the DSH profile:

```bash
dsh plugin --profile web add 'github:fwerkor/local-shell-mcp#main'
```

For production, pin the Git spec to a reviewed release tag or commit instead of tracking `main`. For development from a checkout, use:

```bash
dsh plugin --profile web add .
```

DSH loads the repository's `cordis.patch.yml`, connects to `http://127.0.0.1:8765/mcp` by default, and registers the LSM tools under DSH's normal MCP namespace:

```text
mcp__lsm__run_shell_tool
mcp__lsm__remote_manage
mcp__lsm__remote_transfer
mcp__lsm__browser_session
mcp__lsm__mcp_tool_search
...
```

The bundle deliberately keeps the complete LSM MCP tool catalog. This includes remote-worker administration and remote execution because those are first-class LSM capabilities. If a particular DSH deployment wants a smaller model-facing surface, apply a DSH-side `ctx.tools.restrict()` policy in a later profile layer instead of changing the LSM bundle.

## Remote workers

Use the HTTP/MCP service mode rather than spawning LSM over stdio when DSH needs remote workers. Remote workers poll the LSM controller's `/remote/*` service plane, which is hosted by the same LSM process as `/mcp`.

If workers connect from outside the controller host, configure LSM's public URL and expose the service as usual. DSH may still connect locally to `127.0.0.1:8765/mcp`; the public URL is for workers and other external clients.

## Custom endpoint and authentication

The bundle accepts these DSH Host environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `DSH_LSM_MCP_URL` | `http://127.0.0.1:8765/mcp` | LSM Streamable HTTP MCP endpoint. |
| `DSH_LSM_AUTHORIZATION` | unset | Optional complete `Authorization` header value, for example `Bearer ...`. |
| `DSH_LSM_TOOL_CALL_TIMEOUT_MS` | `120000` | Per-tool-call timeout used by DSH's MCP client. |

Same-host deployments normally need no authorization header because LSM permits its configured localhost auth bypass by default. Do not expose an unauthenticated LSM endpoint on a public network.

For a different host:

```bash
export DSH_LSM_MCP_URL='https://lsm.example.com/mcp'
export DSH_LSM_AUTHORIZATION='Bearer <token>'
dsh web
```

DSH's current MCP client accepts fixed request headers; it does not perform an interactive OAuth authorization/refresh flow for an upstream MCP server. Prefer a private same-host/private-network connection where possible.

## Lifecycle

The DSH bundle does not launch a second LSM instance. This avoids splitting remote-worker state, browser sessions, jobs, and dynamic MCP configuration between two controllers. DSH can start before LSM: the MCP client is configured to tolerate an unavailable initial endpoint and reconnect later.

Removing the plugin only removes the DSH-side bridge:

```bash
dsh plugin --profile web remove local-shell-mcp-dsh
```

It does not stop or modify the LSM service.
