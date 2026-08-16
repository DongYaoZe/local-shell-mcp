<!-- i18n-source-sha256: 1f30fc9935125c84fb0838d17ec894d78aaa6253fe3903356414aac716ba2adc -->
# Sicherheit

Verwenden Sie OAuth für öffentliche Bereitstellungen. Wählen Sie starke Werte für `LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN` und `LOCAL_SHELL_MCP_OAUTH_JWT_SECRET` und halten Sie sie geheim.

Standardmäßig sind Pfadoperationen auf den Workspace beschränkt und sensible Pfadbestandteile werden blockiert. Der Full-container-Modus hebt die eingebauten Workspace- und Pfadbeschränkungen auf und ist nur für wegwerfbare Container oder VMs vorgesehen.

Generierte Datei-Download-Links sind öffentliche Bearer-URLs. Sie werden durch hochentropische Tokens, TTLs, optionale Download-Anzahllimits, optionale Größenlimits und Widerruf geschützt.
