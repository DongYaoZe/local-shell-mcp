<!-- i18n-source-sha256: 2ad041876ff35987d7fdd66cbcdc7ed3956f427e8d8b185f354555cdc29a1b8a -->
# ChatGPT 连接器

本页说明如何把 ChatGPT 作为客户端接入。它不负责选择运行时。使用本页前，先通过 Docker、VS Code 扩展、独立二进制或 Python 安装方式启动 `local-shell-mcp` 服务。

`local-shell-mcp` 面向 ChatGPT Developer Mode 和完整 MCP 客户端设计。MCP 端点会直接暴露正常的 LSM 工具集。

## 运行时前置条件

先选择并启动一个运行时：

| 运行时 | 页面 |
|---|---|
| Docker Compose | [Docker Compose 运行时](../installation/docker.md) |
| VS Code 扩展 | [VS Code 扩展运行时](../installation/vscode-extension.md) |
| 独立二进制 | [独立二进制运行时](../installation/binary.md) |
| Python / pipx / 源码 | [Python 运行时](../installation/python.md) |

然后通过 ChatGPT 可访问的网络路径暴露这个运行时。网络入口与反向代理要求见 [网络连通性](../clients/connectivity.md)。

## 公共 URL

ChatGPT 必须通过 HTTPS 访问服务。MCP 端点是：

```text
https://your-public-host.example.com/mcp
```

确保 `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` 只填写公开源站地址：

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

不要在 `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` 后面追加 `/mcp`。

## OAuth 设置

公开部署建议使用以下配置：

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

访问令牌默认不会自动过期，因为较长的编程会话可能超过短令牌寿命。需要撤销访问时，可以轮换 JWT secret，或使用全新的状态重新部署。

## 添加连接器

1. 打开 ChatGPT 的连接器设置或 Developer Mode 的 MCP 设置。
2. 添加自定义 MCP 服务器。
3. 输入 MCP URL：`https://your-public-host.example.com/mcp`。
4. 完成 OAuth 授权。
5. 审核并批准工具列表。

## Live Workspace MCP App

支持 MCP Apps 的 ChatGPT 客户端可以渲染 `local-shell-mcp` 的交互式执行工作区。需要实时观察或人机协作时，只需让 ChatGPT 为当前任务打开一次 Live Workspace；此后 App 会自行重连，不需要反复调用 `workspace_open`。

Live Workspace 只展示可观察的执行状态和共享资源，不展示模型的私有推理过程：

- **Activity**：显示 MCP 工具的开始、完成、失败以及人类操作。
- **Terminal**：连接现有持久 shell 后端，并实时显示 PTY 输出。
- **Files**：浏览、预览、编辑、新建和删除本地或远端工作区文件。
- **Diff**：显示 Git 已暂存和未暂存修改，并可把当前 diff 发回 ChatGPT 审查。
- **Jobs**：显示托管 job 和持久 session。
- **Remotes**：显示远端 worker；启用远端支持时可创建邀请、重命名或撤销 worker。
- **Audit**：查看最近的结构化 MCP 审计记录。

Live Workspace 始终采用协作模式：ChatGPT 与人类可以并行修改同一个工作区。宿主支持时默认以悬浮窗（PiP）打开，并可在悬浮窗与全屏之间来回切换；不再提供 Observe / Take over 状态。

Files、Diff、Audit 和 Activity 视图可以通过 MCP Apps bridge 把选中的操作上下文发送到下一轮模型上下文。这些内容属于显式共享的上下文；UI 不会暴露或尝试重建模型的私有推理。

### 网络与安全

为了让终端和事件流保持低延迟，渲染后的 MCP App 会从 sandbox 直接连接到配置的服务源站。因此，`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` 必须是 ChatGPT 浏览器可以访问的 HTTPS 源站地址。MCP 端点仍然是 `https://your-public-host.example.com/mcp`。

打开工作区时会签发随机、短生命周期的 Live Workspace bearer token。该 token 只放在供渲染 App 使用的 MCP result metadata 中，不进入模型可见的 structured content，并且只会被 human/live UI API 接受。App 使用同一个 `live_id` 自动重附着时会复用当前凭据，避免重连中的视图互相使 token 失效；重连时还会携带当前 logical `session_id`，即使内存中的 Live Workspace 状态已经丢失，也能恢复对应的持久 Session。显式再次调用 `workspace_open` 时会轮换凭据。嵌入式 App 不使用浏览器 cookie 或环境中的隐式凭据。

不支持 MCP Apps 的客户端可以忽略这些 UI metadata。所有普通 MCP 数据工具仍然可用，行为保持不变。

## 第一次提示词

```text
使用 local-shell-mcp。先调用 environment_get，然后列出工作区根目录。暂时不要修改文件。
```

这个提示只验证连通性，不会主动修改文件。

## 推荐操作规则

给模型明确边界：

- 除非另有说明，只在 `/workspace` 内工作。
- 提交前先运行测试。
- 推送前使用 `secret_scan`。
- 只对可以分享的文件使用 `link_create`。
- 长时间进程优先使用持久 shell session。
- 汇总所有修改过文件的命令。

## 工具发现问题

如果 ChatGPT 能完成认证，但没有显示预期工具：

- 确认端点以 `/mcp` 结尾。
- 检查 `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY`。
- 检查反向代理请求头与请求体大小限制。
- 查看 `docker compose logs --tail=200 local-shell-mcp`。
- 确认服务运行在 `mcp` 或 `both` 模式。

## 安全说明

公开部署应保持 OAuth 开启。不要在公网暴露未认证的完整 MCP 工具。每个被批准的工具都应视为已接入模型实际权限的一部分。
