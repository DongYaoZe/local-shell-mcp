<!-- i18n-source-sha256: a5b96c45536a4d18d1e09f2c47a873e568d0594539aa630ed159b4ddbf3cc25d -->
# 审计日志

`local-shell-mcp` 会写入结构化审计记录，帮助还原已连接客户端做过什么。

默认路径：

```text
/workspace/.local-shell-mcp/audit.jsonl
```

## 记录内容

审计记录覆盖这些事件：

- 工具调用开始和结束。
- 命令执行元数据。
- 超时和已处理错误。
- 远程 worker 注册和任务活动。
- 文件链接创建和撤销。
- 适用时的认证相关事件。

服务能识别的敏感参数会被脱敏。

## 读取日志

使用 MCP 工具：

```text
audit_tail
```

也可以直接查看：

```bash
tail -n 100 /workspace/.local-shell-mcp/audit.jsonl
```

## 运维用途

审计日志主要用于：

- 复查修改文件的命令。
- 检查是否使用过远程 worker。
- 调试意外失败。
- 发现文件链接的意外暴露。
- 在公开部署配置错误后支持事件响应。

## 保留策略

活动 `audit.jsonl` 默认受 `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES` 限制为 20 MB。执行保留维护时，旧记录会移动到 `audit-archive/*.jsonl.zst` 的自包含 Zstandard 归档，而不是直接丢弃；外置的大型 audit payload 也会先写入归档。

压缩归档由 `LOCAL_SHELL_MCP_MAX_AUDIT_ARCHIVE_BYTES` 单独限制，默认 512 MB；超过后优先删除最旧归档。将其设为 `0` 可禁用长期压缩保留。近期查询只读取热日志，需要历史记录时才查询归档。

## 限制

审计日志不是沙箱。它能提升可追踪性，但不能阻止已连接模型在配置权限范围内执行操作。
