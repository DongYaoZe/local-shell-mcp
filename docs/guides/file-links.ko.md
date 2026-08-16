<!-- i18n-source-sha256: d758caead1c922385409aceebf498662f25f4cbf252a48d65b29d91f07e5a173 -->
# 파일 링크

`local-shell-mcp`는 제어된 workspace의 파일을 높은 엔트로피의 bearer URL로 노출할 수 있습니다. AI가 생성한 report, archive, PDF, screenshot 또는 기타 artifact를 chat에서 다운로드하거나 표시해야 할 때 유용합니다.

## 파일 링크 사용 시점

다음에 파일 링크를 사용하십시오.

- 생성된 PDF 또는 report.
- Screenshot 및 browser artifact.
- Build output.
- Chat에 붙이기엔 너무 큰 log.
- 수동 검토를 위해 준비한 archive.

Secret, private key, credential store 또는 관련 없는 개인 데이터에는 파일 링크를 사용하지 마십시오.

## 일반 흐름

1. `/workspace` 아래에서 파일을 생성하거나 찾습니다.
2. TTL과 선택적 download limit을 지정해 `link_create`를 호출합니다. 파일을 브라우저나 Markdown image에서 직접 표시해야 하면 `inline=true`를 설정합니다. 기본값은 `false`이며 attachment download를 강제합니다.
3. 반환된 URL을 공유합니다.
4. 더 이상 필요하지 않으면 링크를 revoke합니다.

## 관련 도구

| Tool | 용도 |
|---|---|
| `link_create` | Workspace file용 tokenized URL 생성. |
| `link_list` | 활성 링크 표시. |
| `link_revoke` | 만료 전에 링크 비활성화. |

## 제어 항목

설정 옵션에는 다음이 포함됩니다.

- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_ENABLED`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_MAX_DOWNLOADS`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_FILE_BYTES`

민감한 artifact에는 더 짧은 TTL을 사용하고, 한 명의 수신자를 위한 링크라면 maximum download count를 설정하십시오.

## 보안 참고

파일 링크는 bearer URL입니다. URL을 가진 사람은 링크가 만료되거나 download limit에 도달하거나 revoke될 때까지 파일을 다운로드할 수 있습니다. 임시 secret처럼 취급하십시오. Inline response에는 CSP sandbox와 `X-Content-Type-Options: nosniff`가 포함되어 active format이 LSM origin에 접근하거나 sandbox 없이 same-origin content로 실행되는 것을 막습니다.
