<!-- i18n-source-sha256: 4aec137923c38de0ed4a1b760b5dbd6ce99090d508ce3fe838d35ad44b4ba4f1 -->
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

로그 크기는 `LOCAL_SHELL_MCP_MAX_AUDIT_LOG_BYTES`로 제한됩니다. 장기간 보존이 필요하면 rotation하거나 외부로 export하십시오.

## 제한 사항

감사 로그는 sandbox가 아닙니다. 추적성을 제공하지만 연결된 모델이 구성된 권한 범위 내에서 작업하는 것을 막지는 않습니다.
