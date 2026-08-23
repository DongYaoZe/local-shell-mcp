<!-- i18n-source-sha256: a5b96c45536a4d18d1e09f2c47a873e568d0594539aa630ed159b4ddbf3cc25d -->
# 감사 로그

`local-shell-mcp`는 연결된 client가 수행한 작업을 재구성할 수 있도록 구조화된 감사 항목을 기록합니다.

기본 경로:

```text
/workspace/.local-shell-mcp/audit.jsonl
```

## 기록되는 내용

감사 항목에는 다음과 같은 이벤트가 포함됩니다.

- Tool call 시작/종료.
- 명령 실행 metadata.
- Timeout 및 처리된 오류.
- Remote worker 등록 및 job activity.
- File-link 생성 및 철회.
- 해당하는 인증 관련 이벤트.

서버가 식별할 수 있는 민감한 인수는 redaction됩니다.

## 로그 읽기

MCP tool을 사용합니다.

```text
audit_tail
```

또는 직접 확인합니다.

```bash
tail -n 100 /workspace/.local-shell-mcp/audit.jsonl
```

## 운영 용도

감사 로그는 특히 다음에 유용합니다.

- 파일을 변경한 명령 검토.
- Remote worker 사용 여부 확인.
- 예상하지 못한 실패 디버깅.
- File link의 실수로 인한 노출 탐지.
- 공개 deployment 오류 이후 incident response 지원.

## 보존

활성 `audit.jsonl`은 기본적으로 `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES`에 의해 20 MB로 제한됩니다. 보존 정리 시 오래된 레코드는 삭제되지 않고 자체 포함 Zstandard 아카이브인 `audit-archive/*.jsonl.zst`로 이동합니다. 외부화된 큰 audit payload도 hot store에서 정리되기 전에 아카이브에 포함됩니다.

압축 아카이브는 `LOCAL_SHELL_MCP_MAX_AUDIT_ARCHIVE_BYTES`로 별도 제한되며 기본값은 512 MB입니다. 한도를 넘으면 가장 오래된 아카이브부터 삭제됩니다. `0`으로 설정하면 장기 압축 보존을 비활성화할 수 있습니다. 최근 조회는 hot log만 읽고, 과거 기록이 필요할 때만 아카이브를 조회합니다.

## 제한 사항

감사 로그는 sandbox가 아닙니다. 추적성을 제공하지만 연결된 모델이 구성된 권한 범위 내에서 작업하는 것을 막지는 않습니다.
