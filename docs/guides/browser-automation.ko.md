<!-- i18n-source-sha256: 91695da5acbb82a8550b150249a9b97f17470140a72b27233e2470a93305e7fb -->
# 브라우저 자동화

브라우저 도구는 Playwright를 사용해 페이지를 검사하고, 증거를 캡처하며, 재현 가능한 브라우저 워크플로를 실행합니다. 공개 tool surface는 의도적으로 작게 유지됩니다.

## 도구

| Tool | 용도 |
|---|---|
| `browser_session` | 지속 브라우저 세션을 시작, 목록 조회, 종료 또는 정리하며 선택적으로 profile이나 storage state를 재사용합니다. |
| `browser_snapshot` | 범위가 제한된 페이지 텍스트, page/network error, `e1` 같은 짧은 ref가 있는 대화형 요소를 읽고 선택적으로 screenshot을 캡처합니다. |
| `browser_act` | snapshot ref 또는 CSS selector를 사용해 navigation, click, fill, select, key, wait 및 multi-page action을 구조화하여 실행합니다. |
| `browser_run_script` | 고수준 action set으로 충분하지 않을 때 완전한 Python Playwright script를 실행합니다. |

모든 브라우저 도구는 선택적 `machine`을 받습니다. 브라우저 의존성은 선택한 controller 또는 worker에 미리 설치되어 있어야 하며, 설치는 `python -m playwright install chromium` 같은 일반 shell command로 수행합니다.

## 일반 흐름

대화형 작업에서는 `browser_session(action="start", url=...)`를 호출한 다음 `browser_snapshot`을 사용합니다. Snapshot은 `e1`, `e2` 같은 짧은 ref를 반환하므로 `{"action": "click", "target": "e1"}` 또는 `{"action": "fill", "target": "e2", "value": "..."}`처럼 그대로 `browser_act`에 전달합니다. Element ref는 영구 selector가 아니라 page-state reference이므로 navigation 후에는 다시 snapshot을 생성하십시오.

일반적인 검사와 screenshot에는 `browser_session` + `browser_snapshot`을 우선 사용하십시오. Snapshot은 범위가 제한된 visible text를 반환하고 screenshot을 저장할 수 있습니다. JavaScript evaluation, 사용자 정의 capture/PDF logic 또는 `browser_act`로 표현되지 않는 상호작용에는 `browser_run_script`를 사용합니다.

Script의 범위를 제한하고 명시적 timeout을 설정하며 artifact를 workspace 아래에 저장하십시오. 환경이 해당 작업 전용이 아니라면 credential 입력을 피하십시오.
