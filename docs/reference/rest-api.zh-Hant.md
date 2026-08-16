<!-- i18n-source-sha256: 87dd7fb66311534dcd5a7217bba8c809f71fe6189e8c39b3e265da923cc82d22 -->
# REST API

主要介面是 `/mcp` 上的 MCP。另有 REST 介面用於健康檢查、檔案連結以及部分服務操作。

## 健康檢查

```http
GET /healthz
```

回傳伺服器健康狀態與基本執行狀態。

## MCP

```http
POST /mcp
```

供 ChatGPT 與其他 MCP client 使用的 Streamable HTTP MCP endpoint。

## 透過 REST 呼叫工具

REST 工具呼叫採用一致的成功/錯誤 envelope。驗證錯誤會回傳結構化的 `ok: false` payload，而不是直接暴露框架例外。

## Agent Skills

固定的 Skills registry 也可透過 REST 使用：

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```

Skill 目錄的變更會在下一次呼叫時可見，而且不會改變 MCP 工具清單。

## 檔案連結

帶 token 的檔案下載由內建 HTTP app 提供。連結是 bearer URL，支援 TTL、可選的最大下載次數限制與撤銷。

## 驗證

公開部署應使用 OAuth。開發時可以啟用 localhost bypass，但在公網提供未驗證存取並不安全。
