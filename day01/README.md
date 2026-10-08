# Day 01

## 受講者が実装する場所

- `day01/app.py`（基本はこのファイルを編集）

## 目的

- 開発環境のセットアップができる状態にする
- GitHubのPR提出フローに慣れる
- Pythonで小さなCLIを作り、例外/ログ/READMEの書き方を身につける

## ゴール（完了条件）

- READMEどおりに第三者が実行できる
- 入力不備で終了コード `2` になり、標準エラーに分かりやすいメッセージが出る

## 機能要件

### 機能要件

コマンド

- `python -m day01.app` で起動できること（モジュール名は固定）

必須オプション

- `--name`：表示したい名前（文字列、必須）

任意オプション

- `--repeat`：繰り返し回数（整数、デフォルト `1`、1〜10）
- `--format`：出力形式（`text` / `json`、デフォルト `text`）

出力

- `--format text` の場合：標準出力に、指定回数分のテキストを出す
- `--format json` の場合：標準出力にJSONを出す
  - 例：`{"name":"Taro","repeat":2,"outputs":["Hello, Taro","Hello, Taro"]}`

終了コード

- 正常終了：`0`
- 入力不備（未指定、範囲外など）：`2`

ログ

- 実行開始時に、`name` / `repeat` / `format` をINFOで出す
- 例外発生時はERRORで出す

### 受け入れ基準

- `--name` 未指定で終了コード `2`、標準エラーに分かりやすいメッセージが出る
- `--repeat 2` で2行（または2要素）出る
- `--format json` でJSONとしてパース可能な文字列が出る

## 実装タスク

- `day01/app.py` を編集し、機能要件を満たす
- 例外時は標準エラーへメッセージを出し、終了コードを要件どおりにする

## 実行方法

### セットアップ

```bash
# 仮想環境の作成と有効化
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 実行コマンド例

```bash
# 基本的な実行
python -m day01.app --name "Taro"

# 繰り返し回数を指定
python -m day01.app --name "Taro" --repeat 3

# JSON形式で出力
python -m day01.app --name "Taro" --repeat 2 --format json
```

### 期待する出力例

```
# --name "Taro" の場合
Hello, Taro

# --name "Taro" --repeat 2 --format json の場合
{"name": "Taro", "repeat": 2, "outputs": ["Hello, Taro", "Hello, Taro"]}
```

---

**以下は受講者が記入してください**

- 追加で確認した入力例：python -m day01.app --name "Keishi" --repeat 3 --format json


- 発生したエラーと対処：コマンドミス　引数をコロン : で繋いでエラーになったが、スペース区切りに直して解決した。--name を未指定にして意図通りエラーになることを確認した

## 提出物

- `day01/app.py`
- `day01/README.md`

## セルフレビュー

- 正常系：`--name Keishi` で期待どおりに表示される
- 異常系：`--name` を省略した場合や、--repeat 11 のように1〜10以外の範囲外数値を指定した場合、エラーメッセージが出て処理が終了（exit code 2）することを確認。
- 境界：`format --json` を指定した際、JSON形式でパース可能な文字列が正しく出力されることを確認。
- 再実行：同じコマンドを実行して、毎回同じ結果になることを確認
- ログ：実行時に設定値のINFOログが、例外発生時にERRORログが出力されることを確認。

## リサーチメモ（任意）

調べたURLや、理解した要点をメモしてください。
- システム間でデータを受け渡す際は、DBのカラムのように「どのデータが何の意味を持つか」を完全に一致させて取り出せるJSON形式を用いるのが基本だと再確認した（非エンジニアのビジネスプロセス考慮する場合においても）
- **エラー処理とログ**
  間違った入力には分かりやすいエラーを返し、正常時（INFO）と異常時（ERROR）でログをしっかり分けることが研修体験を通して運用保守の観点で重要だと学んだ。
- **GitHubでの提出フロー**
  作業用ブランチを作ってからPR（プルリクエスト）で承認を求める一連のチーム開発の流れを体験できた。

