# 状態遷移図（State Diagram）

## 1. フロー図

    graph TD
        START([開始]) --> guard[guard: 入力検証・ガードレール]
        guard -->|status == ok| search_tool[search_tool: 公開データ検索ツール]
        guard -->|status == invalid / blocked| fallback[fallback: 安全な退避・再質問促し]
        search_tool -->|status == found| generate[generate: 根拠付き回答・構造化JSON生成]
        search_tool -->|status == not_found| fallback
        generate --> END([終了])
        fallback --> END

## 2. Stateの定義（AgentState）

| 変数名 | 型 | 役割・保持する情報 |
|---|---|---|
| query | str | ユーザーからの入力テキスト（調査テーマ） |
| status | str | 各ノードでの判定状態（ok, invalid, blocked, found, not_found） |
| docs | List[Dict] | 検索ツール（RAG）でヒットした公開データのリスト（タイトル・URL・抜粋・ライセンス） |
| structured | Dict[str, Any] | 最終出力用の構造化JSONデータ（answer_summary, citations, confidence, next_actions） |
| reply | str | CLIやチャットUIに表示する最終回答テキスト |
| steps | int | 実行ステップ数のカウンタ（無限ループ防止および追跡用） |

## 3. ノードの一覧と役割

- **guard（_guard_node）**：空文字チェックおよび危険なキーワード（プロンプトインジェクション等）の検証を行う。
- **search_tool（_tool_node）**：search_open_data_tool() を呼び出し、公開データから関連ドキュメントを検索する。
- **generate（_generate_node）**：検索ヒットした公開データを根拠として引用し、回答本文と構造化JSONを生成する。
- **fallback（_fallback_node）**：入力不備・攻撃検知・検索ヒット0件の際にハルシネーションを防ぎ、理由と次アクションを返す。

## 4. エッジ（分岐）の条件

- **guard からの分岐**：
  - status == "ok" → search_tool へ遷移
  - それ以外（invalid / blocked） → fallback へ遷移
- **search_tool からの分岐**：
  - status == "found"（検索ヒット1件以上） → generate へ遷移
  - status == "not_found"（検索ヒット0件） → fallback へ遷移