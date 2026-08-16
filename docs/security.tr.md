<!-- i18n-source-sha256: 1f30fc9935125c84fb0838d17ec894d78aaa6253fe3903356414aac716ba2adc -->
# Güvenlik

Genel kullanıma açık dağıtımlarda OAuth kullanın. `LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN` ve `LOCAL_SHELL_MCP_OAUTH_JWT_SECRET` değerlerini güçlü tutun ve gizli saklayın.

Varsayılan olarak yol işlemleri çalışma alanıyla sınırlandırılır ve hassas yol parçaları engellenir. Full-container modu yerleşik çalışma alanı ve yol kısıtlamalarını devre dışı bırakır; yalnızca atılabilir kapsayıcılarda veya VM’lerde kullanılmalıdır.

Oluşturulan dosya indirme bağlantıları herkese açık bearer URL’lerdir. Yüksek entropili belirteçler, TTL’ler, isteğe bağlı indirme sayısı sınırları, isteğe bağlı boyut sınırları ve iptal mekanizmasına dayanırlar.
