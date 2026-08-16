<!-- i18n-source-sha256: 1f30fc9935125c84fb0838d17ec894d78aaa6253fe3903356414aac716ba2adc -->
# 安全性

公開部署應使用 OAuth。請為 `LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN` 與 `LOCAL_SHELL_MCP_OAUTH_JWT_SECRET` 設定高強度隨機值並妥善保密。

預設情況下，路徑操作僅限於工作區範圍，且會封鎖敏感路徑片段。Full-container 模式會停用內建的工作區與路徑限制，僅應在一次性容器或虛擬機中使用。

產生的檔案下載連結是公開的 bearer URL。其安全性仰賴高熵權杖、TTL、可選的下載次數限制、可選的檔案大小限制以及撤銷機制。
