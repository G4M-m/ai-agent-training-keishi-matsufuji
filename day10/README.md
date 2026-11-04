# Day 10

## 受講者が実装する場所

- `day10/app.py`（統合の入口）
- `final/agent.py` の `run_agent()`（最終課題の中身）

## 目的

- Day01〜Day09の部品を統合し、最終課題の最小フローを動かす
- 最終課題のREADME/設計メモの骨格を作る

## ゴール（完了条件）

- `python -m day10.app --text "..."` が起動できる
- `final/agent.py`（スタブでも可）を呼び出す導線がある

## 統合内容

以下を最終課題へ統合します（すべてを完璧に統合できなくてもOKですが、最小フローは動かします）。

- Bedrock呼び出し
- 構造化出力（JSON）
- Tool calling（最低1つ）
- LangGraphでの状態遷移
- フォールバック（最低1つ）
- ログ/エラー処理

## 機能要件

コマンド

- `python -m day10.app` で起動できること（モジュール名は固定）

必須オプション

- `--text`：最終課題へ渡す入力（文字列、必須）

出力

- 標準出力に、最終課題の最小フローの結果を出す（未完成ならエラーでも可）

終了コード

- 正常終了：`0`
- 入力不備：`2`
- 実行失敗：`1`

受け入れ基準

- `final/` に実装したエージェント（またはスタブ）を呼び出す導線がある

## 実装タスク

- `day10/app.py` を編集し、`final.agent.run_agent()` を呼び出して結果を標準出力へ出す
- `final/README.md` と `docs/` の骨格を整える

## 実行方法

### CLI実行

```bash
# 基本的な実行
python -m day10.app --text "〇〇について調査して"
```

### チャットUI（最終課題の動作確認用）

```bash
# チャットUIを起動
streamlit run final/chat_ui.py
```

詳細は `final/README.md` を参照してください。

---

**以下は受講者が記入してください**

## 提出物

- `day10/app.py`
- `day10/README.md`
- `final/`（最終課題のスケルトン）
- `docs/`（設計メモ）

## セルフレビュー

- `self-review-checklist.md` の該当項目：

最低限、以下を満たしていること。

- [x] 起動手順どおりに動く（`python -m day10.app --text "..."` で正常終了コード `0` を確認）
- [x] 出力に根拠（出典）が含まれる（デジタル庁公開データのタイトル・URL・抜粋・ライセンスを提示）
- [x] 失敗時の挙動が分かる（検索ヒット0件時・空入力時・禁止ワード検出時にフォールバックノードへ遷移し、明示的なメッセージと次アクションを出力）

## 最終課題の進捗

- できたこと：
  - `day10/app.py`（CLI）および `final/chat_ui.py`（Streamlit UI）から共通して呼び出せる `final/agent.py` の統合フロー実装
  - LangGraphを用いた状態遷移（`guard` → `search_tool` → `generate` / `fallback`）の構築
  - 公開データ検索ツール（Tool calling）と構造化JSON出力（`answer_summary`, `citations`, `confidence`, `next_actions`）の実装
  - `docs/` 配下の設計ドキュメント（状態遷移図、主要プロンプト、失敗パターン、評価結果）の作成
- 残っていること：
  - 特になし（最小統合フローおよび最終課題の必須要求をすべて実装・検証済み）
