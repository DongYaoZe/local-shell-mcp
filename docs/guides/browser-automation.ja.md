<!-- i18n-source-sha256: 91695da5acbb82a8550b150249a9b97f17470140a72b27233e2470a93305e7fb -->
# ブラウザー自動化

ブラウザーツールは Playwright を使用してページを調査し、証拠を取得し、再現可能なブラウザーワークフローを実行します。公開される tool surface は意図的に小さく保たれています。

## ツール

| Tool | 用途 |
|---|---|
| `browser_session` | 永続的なブラウザーセッションを開始、一覧表示、終了、クリーンアップします。必要に応じて profile または storage state を再利用できます。 |
| `browser_snapshot` | ページの範囲制限されたテキスト、page/network error、`e1` のような短い ref を持つ対話要素を読み取り、必要に応じて screenshot を取得します。 |
| `browser_act` | snapshot ref または CSS selector を使って、navigation、click、fill、select、key、wait、複数ページ操作を構造化して実行します。 |
| `browser_run_script` | 高水準の action set では足りない場合に、完全な Python Playwright script を実行します。 |

すべてのブラウザーツールは任意の `machine` を受け付けます。ブラウザー依存関係は選択した controller または worker に事前にインストールされている必要があり、インストールは `python -m playwright install chromium` のような通常の shell command で行います。

## 一般的なフロー

対話的な作業では、`browser_session(action="start", url=...)` を呼び出してから `browser_snapshot` を実行します。snapshot は `e1` や `e2` のような短い参照を返すため、それらをそのまま `browser_act` に渡せます。たとえば `{"action": "click", "target": "e1"}` や `{"action": "fill", "target": "e2", "value": "..."}` です。要素 ref は永続 selector ではなく page-state reference なので、navigation 後は再度 snapshot を取得してください。

通常の調査や screenshot では `browser_session` と `browser_snapshot` を優先してください。snapshot は範囲制限された可視テキストを返し、screenshot を保存できます。JavaScript evaluation、独自の capture/PDF logic、または `browser_act` で表現できない操作には `browser_run_script` を使用します。

script は必ず範囲を限定し、明示的な timeout を設定し、artifact は workspace 配下に保存してください。環境がそのタスク専用でない限り、credential の入力は避けてください。
