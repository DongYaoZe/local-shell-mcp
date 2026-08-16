<!-- i18n-source-sha256: 87dd7fb66311534dcd5a7217bba8c809f71fe6189e8c39b3e265da923cc82d22 -->
# REST API

主要接口是 `/mcp` 上的 MCP。另有 REST 接口用于健康检查、文件链接以及部分服务操作。

## 健康检查

```http
GET /healthz
```

返回服务器健康状态和基本运行状态。

## MCP

```http
POST /mcp
```

供 ChatGPT 和其他 MCP client 使用的 Streamable HTTP MCP endpoint。

## 通过 REST 调用工具

REST 工具调用使用一致的成功/错误 envelope。验证错误会返回结构化的 `ok: false` payload，而不是直接暴露框架异常。

## Agent Skills

固定的 Skills registry 也可通过 REST 使用：

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```

Skill 目录发生变化后，下一次调用即可看到，且不会改变 MCP 工具列表。

## 文件链接

带 token 的文件下载由内置 HTTP app 提供。链接是 bearer URL，支持 TTL、可选的最大下载次数限制和撤销。

## 身份验证

公开部署应使用 OAuth。开发时可以启用 localhost bypass，但在公网提供未认证访问是不安全的。
