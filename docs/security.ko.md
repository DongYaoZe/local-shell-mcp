<!-- i18n-source-sha256: 1f30fc9935125c84fb0838d17ec894d78aaa6253fe3903356414aac716ba2adc -->
# 보안

공개 배포에서는 OAuth를 사용하십시오. `LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN`과 `LOCAL_SHELL_MCP_OAUTH_JWT_SECRET`에는 충분히 강한 값을 사용하고 비밀로 유지하십시오.

기본적으로 경로 작업은 워크스페이스 범위로 제한되며 민감한 경로 조각은 차단됩니다. Full-container 모드는 내장 워크스페이스 및 경로 제한을 비활성화하므로 폐기 가능한 컨테이너나 VM에서만 사용해야 합니다.

생성된 파일 다운로드 링크는 공개 bearer URL입니다. 높은 엔트로피의 토큰, TTL, 선택적 다운로드 횟수 제한, 선택적 크기 제한 및 철회 기능으로 보호됩니다.
