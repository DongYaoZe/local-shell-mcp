# 配置

仓库只提供一份可直接复制的起始配置：[`.env.example`](https://github.com/fwerkor/local-shell-mcp/blob/main/.env.example)。Docker Compose 会自动读取复制后的 `.env`，其他运行方式也可以使用相同的 `LOCAL_SHELL_MCP_` 环境变量。YAML 仅作为二进制或源码部署的可选高级输入；需要时自行创建文件，并通过 `LOCAL_SHELL_MCP_CONFIG` 或 `--config` 显式指定。环境变量会覆盖 YAML 值，因此除非有意覆盖，否则不要在两处重复定义同一设置。YAML key 使用下表中的字段名。

## 优先级

1. `Settings` 内置默认值。
2. 由 `LOCAL_SHELL_MCP_CONFIG` 或 `--config` 选择的 YAML 配置。
3. 带 `LOCAL_SHELL_MCP_` 前缀的环境变量。
4. `--mode`、`--config`、`--remote`、`--no-remote` 等 CLI 参数；这些参数会在加载 settings 前设置对应环境值。

## 最小公开配置

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=change-me-long-random-pin
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=change-me-long-random-secret
```

仅本地测试时，`auth_bypass_localhost` 默认启用。不要在公网暴露未认证的完整 MCP 工具。

## 设置参考

### 服务与工作区

| YAML key | 环境变量 | 默认值 | 说明 |
|---|---|---|---|
| `host` | `LOCAL_SHELL_MCP_HOST` | `'0.0.0.0'` | 服务绑定地址。 |
| `port` | `LOCAL_SHELL_MCP_PORT` | `8765` | 服务监听端口。 |
| `mode` | `LOCAL_SHELL_MCP_MODE` | `'mcp'` | `mcp`、`http`、`stdio`，或保留值 `both`。 |
| `workspace_root` | `LOCAL_SHELL_MCP_WORKSPACE_ROOT` | `PosixPath('/workspace')` | 工具默认控制的工作区根目录。 |
| `state_dir` | `LOCAL_SHELL_MCP_STATE_DIR` | `PosixPath('/workspace/.local-shell-mcp')` | 运行时状态目录。 |
| `audit_log_path` | `LOCAL_SHELL_MCP_AUDIT_LOG_PATH` | `PosixPath('/workspace/.local-shell-mcp/audit.jsonl')` | 审计日志路径。 |
| `agent_config_dir` | `LOCAL_SHELL_MCP_AGENT_CONFIG_DIR` | `PosixPath('/workspace/.local-shell-mcp/agent_config')` | agent 配置目录。 |
| `allow_full_container` | `LOCAL_SHELL_MCP_ALLOW_FULL_CONTAINER` | `False` | 为 true 时禁用工作区 / 路径限制；只在一次性边界内使用。 |
| `disable_local` | `LOCAL_SHELL_MCP_DISABLE_LOCAL` | `False` | 禁用控制器主机作为 shell / 文件 / 浏览器执行目标；远程 worker 与控制平面服务仍可使用。 |
| `stateless_controller` | `LOCAL_SHELL_MCP_STATELESS_CONTROLLER` | `False` | 面向临时实例/serverless 的无状态控制器模式；隐含 `disable_local`，默认使用内存状态后端。使用默认的 `auth_mode=oauth` 时，需要显式配置强 `oauth_jwt_secret`。 |
| `state_backend` | `LOCAL_SHELL_MCP_STATE_BACKEND` | `'file'` | `file`、`memory` 或 `redis`；serverless 冷启动后需要保留状态时使用 Redis。 |
| `state_backend_url` | `LOCAL_SHELL_MCP_STATE_BACKEND_URL` | `None` | `state_backend=redis` 时的 Redis URL；诊断输出会隐藏。 |
| `state_backend_prefix` | `LOCAL_SHELL_MCP_STATE_BACKEND_PREFIX` | `'local-shell-mcp'` | 内存/Redis 控制面状态的命名空间。 |

### 限制

| YAML key | 环境变量 | 默认值 | 说明 |
|---|---|---|---|
| `default_timeout_s` | `LOCAL_SHELL_MCP_DEFAULT_TIMEOUT_S` | `60` | 默认命令超时时间，单位秒。 |
| `max_timeout_s` | `LOCAL_SHELL_MCP_MAX_TIMEOUT_S` | `3600` | 允许配置的最大超时时间。 |
| `max_output_bytes` | `LOCAL_SHELL_MCP_MAX_OUTPUT_BYTES` | `200000` | 单次工具输出最大字节数。 |
| `max_file_read_bytes` | `LOCAL_SHELL_MCP_MAX_FILE_READ_BYTES` | `512000` | 单文件读取最大字节数。 |
| `max_file_write_bytes` | `LOCAL_SHELL_MCP_MAX_FILE_WRITE_BYTES` | `5000000` | 单文件写入最大字节数。 |
| `max_grep_results` | `LOCAL_SHELL_MCP_MAX_GREP_RESULTS` | `200` | grep 搜索最大结果数。 |
| `max_directory_entries` | `LOCAL_SHELL_MCP_MAX_DIRECTORY_ENTRIES` | `5000` | 目录列表最大条目数。 |
| `max_glob_results` | `LOCAL_SHELL_MCP_MAX_GLOB_RESULTS` | `5000` | glob 搜索最大结果数。 |
| `max_tree_entries` | `LOCAL_SHELL_MCP_MAX_TREE_ENTRIES` | `5000` | tree 视图最大条目数。 |
| `max_skills` | `LOCAL_SHELL_MCP_MAX_SKILLS` | `256` | 单次注册表扫描最多返回的 Skill 目录数。 |
| `max_skill_related_files` | `LOCAL_SHELL_MCP_MAX_SKILL_RELATED_FILES` | `1000` | 单个 Skill 最多返回的关联文件数。 |
| `max_skill_scan_entries` | `LOCAL_SHELL_MCP_MAX_SKILL_SCAN_ENTRIES` | `5000` | 单次 `skills_list` 注册表扫描或单次指定 Skill 加载最多检查的文件系统条目数。 |
| `max_skill_path_bytes` | `LOCAL_SHELL_MCP_MAX_SKILL_PATH_BYTES` | `200000` | 返回的关联文件路径可占用的最大 UTF-8 字节数。 |
| `max_read_many_files` | `LOCAL_SHELL_MCP_MAX_READ_MANY_FILES` | `100` | 批量读取最大文件数。 |
| `max_read_many_total_bytes` | `LOCAL_SHELL_MCP_MAX_READ_MANY_TOTAL_BYTES` | `5000000` | 批量读取总字节上限。 |
| `max_todos` | `LOCAL_SHELL_MCP_MAX_TODOS` | `1000` | todo 记录最大数量。 |
| `max_todo_bytes` | `LOCAL_SHELL_MCP_MAX_TODO_BYTES` | `1000000` | todo 数据最大字节数。 |
| `max_http_request_bytes` | `LOCAL_SHELL_MCP_MAX_HTTP_REQUEST_BYTES` | `16000000` | MCP、REST、OAuth、UI 与远程 worker 端点允许缓冲的最大 HTTP 请求体字节数。 |
| `max_job_log_bytes` | `LOCAL_SHELL_MCP_MAX_JOB_LOG_BYTES` | `10000000` | 每次长任务运行保留的最大输出字节数。 |
| `max_jobs` | `LOCAL_SHELL_MCP_MAX_JOBS` | `1000` | 最多保留的长任务记录数；运行中的任务不会被清理。 |
| `max_audit_tail_bytes` | `LOCAL_SHELL_MCP_MAX_AUDIT_TAIL_BYTES` | `1000000` | `audit_tail` 最大返回字节数。 |
| `max_audit_log_bytes` | `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES` | `20000000` | 审计日志文件大小上限。 |
| `max_tmp_files` | `LOCAL_SHELL_MCP_MAX_TMP_FILES` | `500` | 临时文件最大数量。 |
| `max_tmp_bytes` | `LOCAL_SHELL_MCP_MAX_TMP_BYTES` | `50000000` | 临时文件总字节上限。 |
| `max_transfer_archive_entries` | `LOCAL_SHELL_MCP_MAX_TRANSFER_ARCHIVE_ENTRIES` | `100000` | 解包目录传输归档时允许的最大成员数量。 |
| `max_transfer_unpacked_bytes` | `LOCAL_SHELL_MCP_MAX_TRANSFER_UNPACKED_BYTES` | `10000000000` | 目录传输归档允许声明的最大解压后总字节数。 |
| `max_concurrent_commands` | `LOCAL_SHELL_MCP_MAX_CONCURRENT_COMMANDS` | `4` | 并发命令数量上限。 |
| `max_tmux_sessions` | `LOCAL_SHELL_MCP_MAX_TMUX_SESSIONS` | `16` | tmux、ConPTY 与 native fallback 共用的持久 shell session 数量上限。 |

### 文件链接

| YAML key | 环境变量 | 默认值 | 说明 |
|---|---|---|---|
| `file_download_enabled` | `LOCAL_SHELL_MCP_FILE_DOWNLOAD_ENABLED` | `True` | 是否启用文件下载链接。 |
| `file_download_default_ttl_s` | `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_TTL_S` | `3600` | 默认链接 TTL，单位秒。 |
| `file_download_max_ttl_s` | `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_TTL_S` | `604800` | 最大链接 TTL。 |
| `file_download_default_max_downloads` | `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_MAX_DOWNLOADS` | `0` | `0` 表示默认不限制下载次数。 |
| `file_download_max_file_bytes` | `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_FILE_BYTES` | `0` | `0` 表示下载链接无配置层文件大小上限。 |

### 远程 worker

| YAML key | 环境变量 | 默认值 | 说明 |
|---|---|---|---|
| `remote_enabled` | `LOCAL_SHELL_MCP_REMOTE_ENABLED` | `True` | 控制 `/join`、`/remote/*` 和 `remote_*` MCP 工具。 |
| `remote_invite_ttl_s` | `LOCAL_SHELL_MCP_REMOTE_INVITE_TTL_S` | `600` | 远程邀请默认 TTL。 |
| `remote_poll_timeout_s` | `LOCAL_SHELL_MCP_REMOTE_POLL_TIMEOUT_S` | `25` | 远程轮询超时。 |
| `remote_job_timeout_s` | `LOCAL_SHELL_MCP_REMOTE_JOB_TIMEOUT_S` | `3600` | 远程 job 默认超时。 |
| `remote_max_pending_jobs` | `LOCAL_SHELL_MCP_REMOTE_MAX_PENDING_JOBS` | `256` | 每个 worker 最多排队或等待完成的 job 数。 |
| `remote_cancelled_job_ttl_s` | `LOCAL_SHELL_MCP_REMOTE_CANCELLED_JOB_TTL_S` | `3600` | 用于跳过已超时排队任务的取消标记保留时间。 |
| `remote_transfer_strategy` | `LOCAL_SHELL_MCP_REMOTE_TRANSFER_STRATEGY` | `'auto'` | `auto`、`relay`、`direct` 或 `object_store`；`auto` 依次尝试已启用的 worker 直传、S3，再回退到 controller 有界内存 relay。 |
| `remote_peer_transfer_enabled` | `LOCAL_SHELL_MCP_REMOTE_PEER_TRANSFER_ENABLED` | `False` | 启用目标 worker 的一次性 HTTP receiver 进行 worker→worker 直传；仅建议在 VPC/Tailscale 等可信私网中开启。 |
| `remote_peer_transfer_bind_host` | `LOCAL_SHELL_MCP_REMOTE_PEER_TRANSFER_BIND_HOST` | `'0.0.0.0'` | 一次性 receiver 的监听地址。 |
| `remote_peer_transfer_advertise_host` | `LOCAL_SHELL_MCP_REMOTE_PEER_TRANSFER_ADVERTISE_HOST` | `None` | 告知源 worker 的目标地址；默认使用目标 worker 主机名/FQDN。 |
| `remote_peer_transfer_port` | `LOCAL_SHELL_MCP_REMOTE_PEER_TRANSFER_PORT` | `0` | receiver 端口；`0` 表示自动选择临时端口。 |
| `remote_peer_transfer_timeout_s` | `LOCAL_SHELL_MCP_REMOTE_PEER_TRANSFER_TIMEOUT_S` | `3600` | 一次性直传 receiver 的超时/存活时间。 |
| `remote_transfer_s3_bucket` | `LOCAL_SHELL_MCP_REMOTE_TRANSFER_S3_BUCKET` | `None` | 可选 S3 兼容 bucket，用于预签名 URL 传输；需安装 `s3` extra。 |
| `remote_transfer_s3_prefix` | `LOCAL_SHELL_MCP_REMOTE_TRANSFER_S3_PREFIX` | `'local-shell-mcp'` | 临时对象 key 前缀。 |
| `remote_transfer_s3_region` | `LOCAL_SHELL_MCP_REMOTE_TRANSFER_S3_REGION` | `None` | 可选 S3 region。 |
| `remote_transfer_s3_endpoint_url` | `LOCAL_SHELL_MCP_REMOTE_TRANSFER_S3_ENDPOINT_URL` | `None` | 可选 S3 兼容 endpoint。 |
| `remote_transfer_s3_presign_ttl_s` | `LOCAL_SHELL_MCP_REMOTE_TRANSFER_S3_PRESIGN_TTL_S` | `3600` | 预签名 PUT/GET URL 有效期；传输结束后自动删除临时对象。 |

### Shell 与可执行路径

| YAML key | 环境变量 | 默认值 | 说明 |
|---|---|---|---|
| `shell_executable` | `LOCAL_SHELL_MCP_SHELL_EXECUTABLE` | `'/bin/bash'` | shell 可执行文件。 |
| `shell_env_blocklist` | `LOCAL_SHELL_MCP_SHELL_ENV_BLOCKLIST` | `['CLOUDFLARE_TUNNEL_TOKEN']` | 传给 shell 前需要屏蔽的环境变量。 |
| `shell_env_blocked_prefixes` | `LOCAL_SHELL_MCP_SHELL_ENV_BLOCKED_PREFIXES` | `['LOCAL_SHELL_MCP_', 'DOCKER_']` | 环境变量中用逗号分隔，YAML 中用列表。 |
| `tmux_bin` | `LOCAL_SHELL_MCP_TMUX_BIN` | `'tmux'` | 首选 tmux 可执行文件；不可用时 Linux 发行包和 Docker 使用内置 helper，其余情况退回 native backend。 |
| `rg_bin` | `LOCAL_SHELL_MCP_RG_BIN` | `'rg'` | ripgrep 可执行文件。 |
| `git_bin` | `LOCAL_SHELL_MCP_GIT_BIN` | `'git'` | git 可执行文件。 |
| `python_bin` | `LOCAL_SHELL_MCP_PYTHON_BIN` | `'python3'` | Python 可执行文件。 |

### 认证与 OAuth

| YAML key | 环境变量 | 默认值 | 说明 |
|---|---|---|---|
| `auth_mode` | `LOCAL_SHELL_MCP_AUTH_MODE` | `'oauth'` | 公开部署使用 `oauth`。 |
| `auth_bypass_localhost` | `LOCAL_SHELL_MCP_AUTH_BYPASS_LOCALHOST` | `True` | 是否允许 localhost 绕过认证。 |
| `require_auth_for_mcp_discovery` | `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY` | `True` | MCP 初始化与工具发现是否要求 OAuth 认证。 |
| `mcp_session_idle_timeout_s` | `LOCAL_SHELL_MCP_MCP_SESSION_IDLE_TIMEOUT_S` | `180` | Stateful Streamable HTTP 会话空闲超时。 |
| `mcp_max_sessions` | `LOCAL_SHELL_MCP_MCP_MAX_SESSIONS` | `1024` | Stateful MCP 会话最大并发数。 |
| `public_base_url` | `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` | `None` | 外部 HTTPS origin。不要包含 `/mcp`。 |
| `oauth_issuer` | `LOCAL_SHELL_MCP_OAUTH_ISSUER` | `None` | OAuth issuer 覆盖值。 |
| `oauth_resource` | `LOCAL_SHELL_MCP_OAUTH_RESOURCE` | `None` | OAuth resource 覆盖值。 |
| `oauth_admin_pin` | `LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN` | `None` | OAuth 管理 PIN。 |
| `oauth_jwt_secret` | `LOCAL_SHELL_MCP_OAUTH_JWT_SECRET` | <generated or configured> | OAuth JWT secret。 |
| `oauth_access_token_ttl_s` | `LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S` | `0` | `0` 表示访问令牌不自动过期。 |
| `oauth_code_ttl_s` | `LOCAL_SHELL_MCP_OAUTH_CODE_TTL_S` | `300` | OAuth code TTL。 |

### 内置策略列表

| YAML key | 环境变量 | 默认值 | 说明 |
|---|---|---|---|
| `command_denylist` | `LOCAL_SHELL_MCP_COMMAND_DENYLIST` | `[]` | full-container 模式启用时会自动清空。 |
| `path_denylist` | `LOCAL_SHELL_MCP_PATH_DENYLIST` | `[]` | full-container 模式启用时会自动清空。 |

## YAML 示例

```yaml
host: 0.0.0.0
port: 8765
mode: mcp
workspace_root: /workspace
auth_mode: oauth
remote_enabled: true
disable_local: false
file_download_enabled: true
shell_env_blocked_prefixes:
  - LOCAL_SHELL_MCP_
  - DOCKER_
```

Serverless 控制器并使用 Redis 持久化控制面状态：

```yaml
mode: mcp
stateless_controller: true
state_backend: redis
state_backend_url: redis://redis.internal:6379/0
remote_transfer_strategy: auto
```

`stateless_controller` 不要求 controller 挂载持久卷。`memory` 后端是完全临时的：冷启动会使待使用的 remote invite 和 worker identity 失效，并丢弃 OAuth client、job 与 audit 状态。需要这些状态跨冷启动保留（包括可靠的 worker revoke 语义）时应使用 Redis。使用默认的 `auth_mode=oauth` 时，同时通过 `LOCAL_SHELL_MCP_OAUTH_JWT_SECRET` 注入至少 32 字节的随机密钥。当前远程 RPC 的活动队列/等待 future 仍位于 controller 进程内，因此使用 remote worker 时应保持单个 active controller 实例，而不是多个负载均衡副本。

## 运维建议

- 除非容器或 VM 是一次性的，否则保持 `allow_full_container=false`。
- 任何公开端点都保持 `auth_mode=oauth`。
- 如果不用远程 worker，关闭 `remote_enabled`。
- 如果从不需要聊天中下载产物，关闭 `file_download_enabled`。
- 命令、文件和审计限制应足够支持编程任务，同时避免意外输出失控。
