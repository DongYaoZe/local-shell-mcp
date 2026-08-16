<!-- i18n-source-sha256: 87dd7fb66311534dcd5a7217bba8c809f71fe6189e8c39b3e265da923cc82d22 -->
# REST API

주요 interface는 `/mcp`의 MCP입니다. REST surface도 health check, file link 및 일부 service operation에 사용할 수 있습니다.

## 상태 확인

```http
GET /healthz
```

서버의 상태와 기본 실행 정보를 반환합니다.

## MCP

```http
POST /mcp
```

ChatGPT와 기타 MCP client가 사용하는 Streamable HTTP MCP endpoint입니다.

## REST를 통한 도구 호출

REST 도구 호출은 일관된 성공/오류 envelope를 사용합니다. 검증 오류는 원시 프레임워크 예외 대신 구조화된 `ok: false` payload를 반환합니다.

## Agent Skills

고정된 Skills registry도 REST를 통해 사용할 수 있습니다.

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```

Skill 디렉터리 변경 사항은 다음 호출에서 반영되며 MCP 도구 목록은 변경되지 않습니다.

## 파일 링크

토큰화된 파일 다운로드는 내장 HTTP app에서 제공됩니다. 링크는 bearer URL이며 TTL, 선택적 최대 다운로드 횟수, 철회를 지원합니다.

## 인증

공개 배포에서는 OAuth를 사용해야 합니다. 개발용으로 localhost bypass를 활성화할 수 있지만 인증되지 않은 공개 접근은 안전하지 않습니다.
