# DeepSeek Harness（DSH）

`local-shell-mcp` 可以直接安装到 DeepSeek Harness Web profile。仓库内置一层面向 DSH 的桥接：保留完整 LSM 工具面，把每个 DSH Session 稳定映射到 PR 162 的 Logical Session，并把 **Live Workspace** 作为 DSH 原生 `conversation.view` 页面挂入会话。

执行状态仍由 LSM 负责：本机/远程机器、Logical Session 与 Goal Plan、持久终端、Jobs、Browser Session、Dynamic MCP、文件链接、Audit 和 Live Workspace timeline 都只有 LSM controller 这一份权威状态。

## 推荐部署结构

推荐 DSH 和 LSM 直接运行在同一台机器：

```text
DSH Web
  |
  | 每个 DSH Session 一条独立 LSM MCP 连接
  | 127.0.0.1:8765/mcp
  v
local-shell-mcp :8765
  |-- local 执行 = 运行 LSM 的这台环境
  |-- /mcp
  |-- /remote/*
  |-- /ui
  |-- Live Workspace / audit / browser / jobs / links
  |
  +--> Remote Workers
```

这种部署下，**运行 LSM 的环境就是 LSM 的 `local`**。如果 LSM 自己运行在 Docker 容器中，那么 `local` 指该容器，而不会自动变成宿主机上的 DSH 环境。

LSM 默认监听 `0.0.0.0:8765`，而 DSH bundle 默认通过 `127.0.0.1:8765/mcp` 连接。配置好网络、防火墙、公开 URL 和认证后，同一个 LSM controller 仍可供 Remote Worker 和其它外部客户端访问。

## 安装

先启动 LSM：

```bash
local-shell-mcp --mode mcp
```

然后安装本仓库到 DSH Web profile：

```bash
dsh plugin --profile web add 'github:fwerkor/local-shell-mcp#main'
```

生产环境建议固定到经过审查的 release tag 或 commit。本地开发 checkout 可直接：

```bash
dsh plugin --profile web add .
```

bundle 会从 `cordis.patch.yml` 加载 `local-shell-mcp-dsh`。模型看到的 LSM 工具使用 DSH 常规 MCP 命名，例如：

```text
mcp__lsm__run_shell
mcp__lsm__file_read
mcp__lsm__remote_manage
mcp__lsm__remote_transfer
mcp__lsm__browser_session
mcp__lsm__mcp_tool_search
mcp__lsm__session_manage
mcp__lsm__plan_manage
...
```

该 bridge **不会主动裁剪 LSM 的模型工具面**，Remote Worker 能力也完整保留。内部的 `live_workspace_reconnect` 是 app-only 工具，只由 bridge 使用，不暴露给模型。如果某个 DSH 部署希望减少模型可见工具，应在更后的 DSH layer 使用 `ctx.tools.restrict()`，而不是修改 LSM bundle。

## DSH Session 如何绑定 PR 162 Logical Session

实现直接建立在 PR 162 的 Logical Session runtime 上。每个 DSH Session 都拥有独立的上游 Streamable HTTP MCP client，同时 bridge 会根据 DSH Session id 计算一个不透明、稳定的 session-affinity 值发送给 LSM。

因此身份链是：

```text
DSH Session A
  -> 稳定 affinity A
  -> PR 162 MCP session key A
  -> LSM Logical Session / active run A
  -> Live Workspace A

DSH Session B
  -> 稳定 affinity B
  -> PR 162 MCP session key B
  -> LSM Logical Session / active run B
  -> Live Workspace B
```

因此多个 DSH 会话的工具 Activity 不会混到同一个 Live Workspace timeline。即使重启 DSH，新建的 MCP transport 仍使用相同 affinity；只要 LSM controller 仍持有该 Logical Session，原来的 Logical Session 和 active run 会继续绑定，不需要用户额外手动接管。

bridge 还会定期 ping 活跃的 MCP client，避免 LSM 正常的 MCP idle-session 清理破坏长时间闲置的 DSH 会话。

## DSH 内的 Live Workspace

浏览器侧插件会给 `conversation.view` 增加 **Live Workspace** 页面。它直接复用 PR 162 已有的 Live Workspace 实现，不复制第二套 UI 状态系统。

页面按当前 DSH Session 隔离，能看到对应的 LSM Logical Session、Plan/Goal、Activity、Terminal、Files、Diff、Jobs、Remotes 和 Audit。Live Workspace 中的 **Ask** 以及 Goal 自动续跑消息，也会回到当前这一个 DSH conversation。

Live Workspace 凭据由 DSH Host 使用该 Session 自己的 LSM MCP 连接在服务端获取；token 不进入 DSH 对话，也不会作为模型可见工具结果暴露。

## 为什么使用 HTTP，而不是 stdio

Remote Worker 不只有 MCP 工具调用。它还需要 controller 的 `/remote/*` HTTP 路由完成注册、轮询、心跳、结果回传和文件传输。仅启动一个 stdio LSM 子进程既无法保留这些服务，又会产生第二份 controller 状态。

连接已经运行的 LSM HTTP 服务，可以让 Remote Worker、Browser 状态、Jobs、Dynamic MCP、Audit、文件链接、Logical Session 和 Live Workspace 始终只有一个权威 controller。

## 配置

DSH Host bridge 支持以下环境变量：

| 变量 | 默认值 | 用途 |
|---|---|---|
| `DSH_LSM_MCP_URL` | `http://127.0.0.1:8765/mcp` | DSH Host 使用的 LSM Streamable HTTP MCP 地址 |
| `DSH_LSM_AUTHORIZATION` | 未设置 | 可选的完整 `Authorization` 请求头，例如 `Bearer ...` |
| `DSH_LSM_TOOL_CALL_TIMEOUT_MS` | `120000` | 单次工具调用超时，单位毫秒 |
| `DSH_LSM_KEEPALIVE_INTERVAL_MS` | `30000` | 保持每个 Session MCP identity 的 ping 周期；最小 5000 ms |
| `DSH_LSM_BROWSER_URL` | 未设置 | 当浏览器访问 LSM 的地址与 DSH Host 连接 MCP 的地址不同，用它指定浏览器可访问的 LSM origin |

同机部署一般不需要额外认证头，因为 LSM 默认允许配置范围内的 localhost auth bypass。不要把未认证的 LSM 服务直接暴露到公网。

连接受保护的远程 LSM 时：

```bash
export DSH_LSM_MCP_URL='https://lsm.example.com/mcp'
export DSH_LSM_AUTHORIZATION='Bearer <token>'
dsh --profile web
```

bridge 可以发送固定的上游请求头，但不会代替 DSH 运行交互式 OAuth 授权和 refresh token 流程。

### DSH Web 运行在远程机器时

`DSH_LSM_MCP_URL` 是 **DSH Host 进程**访问的地址；Live Workspace 的 API 请求则由用户浏览器发起。如果 DSH 部署在远端，而 LSM 返回的 `127.0.0.1` 对用户浏览器不可达，应显式配置：

```bash
export DSH_LSM_BROWSER_URL='https://lsm.example.com'
```

浏览器请求仍使用 Live Workspace token 做授权。

## Remote Workers

Remote Worker 能力在 DSH 中完整保留。`mcp__lsm__remote_manage`、`mcp__lsm__remote_transfer`，以及带 `machine` 参数的普通 LSM 工具，都会使用同一个 controller 和同一份 Remote Worker 状态。

如果 worker 从 controller 外部连接，只需照普通 LSM 部署配置 public URL 和网络暴露；DSH 自己仍然可以继续走 `127.0.0.1:8765/mcp`。

## 生命周期与故障语义

bundle 不会启动第二个 LSM。DSH 可以在 LSM 尚未上线时启动：catalog connection 会按退避策略重连，LSM 可用后再同步工具目录。

对于一次结果不确定的 transport failure，bridge **不会自动重放模型工具调用**。原因是 Shell、文件或 Remote 操作可能已经执行成功，盲目重放会造成二次执行。稳定 session-affinity 和 keepalive 负责处理正常的 MCP transport 重建与长时间空闲，而真正替换整个 LSM controller 时，则按该部署本身的 Durable Session 恢复规则处理。

移除插件只会删除 DSH 一侧的集成：

```bash
dsh plugin --profile web remove local-shell-mcp-dsh
```

不会停止 LSM。

## 验证安装

先检查 DSH 合成配置：

```bash
dsh --profile web --dump-config
```

应看到类似：

```text
id: local-shell-mcp
name: local-shell-mcp-dsh
url: http://127.0.0.1:8765/mcp
```

LSM 在线后，DSH 应出现 `mcp__lsm__*` 工具，例如：

```text
mcp__lsm__run_shell
mcp__lsm__remote_manage
mcp__lsm__remote_transfer
mcp__lsm__browser_session
mcp__lsm__session_manage
```

DSH Web 中，只要 conversation 已进入正常会话页面，还会出现 **Live Workspace** view。若工具整体不存在，检查 `DSH_LSM_MCP_URL`、LSM `/healthz`、`/mcp` 和 DSH Host 日志；如果只有嵌入页面无法连接，再检查 `DSH_LSM_BROWSER_URL`。
