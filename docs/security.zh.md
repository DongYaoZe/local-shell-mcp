<!-- i18n-source-sha256: 1f30fc9935125c84fb0838d17ec894d78aaa6253fe3903356414aac716ba2adc -->
# 安全

公开部署应使用 OAuth。请为 `LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN` 和 `LOCAL_SHELL_MCP_OAUTH_JWT_SECRET` 设置强随机值并妥善保密。

默认情况下，路径操作仅限于工作区范围，并会阻止访问敏感路径片段。Full-container 模式会禁用内置的工作区和路径限制，仅应在一次性容器或虚拟机中使用。

生成的文件下载链接是公开的 bearer URL。其安全性依赖高熵令牌、TTL、可选的下载次数限制、可选的文件大小限制以及撤销机制。
