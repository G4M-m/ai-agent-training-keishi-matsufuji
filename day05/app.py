from __future__ import annotations

import argparse
import logging
import sys
from typing import List


def build_parser() -> argparse.ArgumentParser:
    """Day05のCLI引数を定義します（質問文）。"""
    p = argparse.ArgumentParser(prog="day05")
    p.add_argument("--question", required=True)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.question:
        raise ValueError("--question is required")


def answer_with_rag(question: str) -> str:
    """RAGで質問に回答し、指定フォーマットのテキストを返します。"""
    import os
    import glob
    from langchain_aws import ChatBedrock
    from langchain_core.messages import HumanMessage, SystemMessage

    # ① Retrieval（検索）：指定フォルダからテキストデータを読み込む
    data_dir = "day05/data"
    hit_contents = []
    hit_sources = []

    if os.path.exists(data_dir):
        # フォルダ内の .txt ファイルをすべて読み込む
        for filepath in glob.glob(f"{data_dir}/*.txt"):
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
                # 今回は簡易的なRAGのため、テキストが存在すれば検索ヒットとみなす
                if text.strip():
                    hit_contents.append(text)
                    hit_sources.append(filepath)

    # そもそも読み込むファイルが無い場合（または中身が空の場合）のフェイルセーフ
    if not hit_contents:
        return "Answer: 該当する根拠が見つかりません。\nSources:\n- (none)"

    # ② Augmented（プロンプトへの注入）：システムプロンプトに【参考資料】として埋め込む
    context_text = "\n---\n".join(hit_contents)
    
    # AIの知識を封じ込め、資料のみを使わせるための絶対ルール
    system_prompt = (
        "あなたは社内規定を案内するアシスタントです。"
        "以下の【参考資料】の情報のみを使って、ユーザーの質問に簡潔に答えてください。"
        "参考資料に答えが載っていない質問の場合は、絶対に推測せず、"
        "必ず「該当する根拠が見つかりません。」という一文のみを出力してください。\n\n"
        f"【参考資料】\n{context_text}"
    )

    # ③ Generation（生成）：AIに回答を作成させる
    region = os.getenv("AWS_REGION", "us-east-2")
    model_id = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0")

    llm = ChatBedrock(
        model_id=model_id,
        region_name=region,
        model_kwargs={"temperature": 0.0}
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=question)
    ]

    ai_msg = llm.invoke(messages)
    answer_text = str(ai_msg.content)

    # ④ 出力フォーマットの成形と、AIが「資料にない」と判断した場合の統制（コントロール）
    if "該当する根拠が見つかりません" in answer_text:
        # AIがギブアップした場合、仕様通りに Sources を (none) にする
        return "Answer: 該当する根拠が見つかりません。\nSources:\n- (none)"

    # 正常に回答できた場合、Python側で確実に証跡（ファイル名）を付与する
    sources_str = "\n".join([f"- {src} (excerpt: 参考資料より抽出)" for src in hit_sources])
    final_output = f"Answer: {answer_text}\nSources:\n{sources_str}"

    return final_output

def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    受講者は `answer_with_rag()` を実装します。
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        _validate_args(args)
    except Exception as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    try:
        out = answer_with_rag(args.question)
        print(out)
        return 0
    except NotImplementedError as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        logging.error("%s", e)
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
