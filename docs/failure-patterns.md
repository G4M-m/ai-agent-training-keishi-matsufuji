# 失敗パターンと対策（Failure Patterns）

本エージェントで想定される失敗パターンと、実装した安全対策（フォールバック・ガードレール）を以下に整理する。

## 1. 失敗パターン一覧と対策

| 失敗パターン | 発生原因 | 検知箇所（ノード） | 対策・フォールバック挙動 |
|---|---|---|---|
| **検索ヒットなし（0件）** | 公開データに該当キーワードが存在しない質問 | search_tool (status="not_found") | 推測回答（ハルシネーション）を行わず fallback ノードへ退避。confidence: "low" とし、検索可能なキーワード例を next_actions で提示する。 |
| **プロンプトインジェクション** | 「前の指示は無視して」「秘密情報を出して」等の不正入力 | guard (status="blocked") | ツール呼び出しや生成を行わず fallback ノードへ即時退避。セキュリティポリシーによる拒否メッセージを返す。 |
| **空入力・引数不備** | CLIで --text "" が渡された場合や空白のみの入力 | day10/app.py / guard (status="invalid") | CLI引数不備は終了コード 2 で停止。エージェント内部では fallback ノードへ遷移し、再入力を促す。 |
| **構造化出力（JSON）の破損** | 生成時のフォーマット崩れや必須キー欠落 | generate / fallback | スキーマ（answer_summary, citations, confidence, next_actions）を辞書構造で厳密に組み立てた上で json.dumps によりシリアライズし、パースエラーを防止する。 |

## 2. 無限ループ防止設計

- LangGraphのグラフ構造を単方向の非巡回グラフ（DAG：guard → search_tool → generate / fallback → END）として設計し、全パスが最大3ステップ以内で確実に END へ到達する構造としている。
- AgentState に steps カウンタを保持し、meta 情報として実行ステップ数を常時追跡可能にしている。