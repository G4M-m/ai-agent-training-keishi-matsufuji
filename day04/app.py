from __future__ import annotations

import argparse
import logging
import sys
from typing import List


def build_parser() -> argparse.ArgumentParser:
    """Day04のCLI引数を定義します（ユーザー入力テキスト）。"""
    p = argparse.ArgumentParser(prog="day04")
    p.add_argument("--text", required=True)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.text:
        raise ValueError("--text is required")


def run_chain(text: str) -> str:
    """LangChain + Tool calling を使って回答（文字列）を返します。

    この関数を実装すると、`python -m day04.app --text ...` が動くようになります。

    要件（READMEの受け入れ基準）：
    - `today` または `add` のツールを1つ実装し、LLMから1回以上呼び出す
    - ツール引数のバリデーションを入れる（不正なら実行しない）
    - ツール失敗時は安全に失敗する（例外でOK。mainがexit code=1にする）

    ヒント：
    - まずはツールをPython関数として作り、ログで「呼ばれた」ことを確認
    - 次にLLM側のプロンプトで「必要ならツールを使う」よう誘導
    """
    import os
    import logging
    from langchain_aws import ChatBedrock
    from langchain_core.tools import tool
    from langchain_core.messages import HumanMessage, SystemMessage
    # ① ツール（道具）の定義：Pythonで確定的に処理したい計算ロジック
    @tool
    def add(a: int, b: int) -> int:
        """2つの整数を足し算します。"""
        # 型のバリデーション（不正な引数ならエラーにして止める）
        if not isinstance(a, int) or not isinstance(b, int):
            raise ValueError("引数は整数である必要があります。")
        
        # ツールが呼ばれた証拠をログに残す
        logging.info(f"★★★ Pythonのツールが実行されました！ 計算: {a} + {b} ★★★")
        return a + b

    # ② LLM（AI）の初期化
    region = os.getenv("AWS_REGION", "us-east-2")
    model_id = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0")
    
    llm = ChatBedrock(
        model_id=model_id,
        region_name=region,
        model_kwargs={"temperature": 0.0}
    )
    
    # ③ AIに「この道具（ツール）を使っていいよ」と説明書を渡す
    llm_with_tools = llm.bind_tools([add])
    
    # ④ ユーザーの曖昧な言葉（口語）をAIに投げる
    system_prompt = (
        "あなたは提供されたツールのみを使用して回答するアシスタントです。"
        "ツールが受け付けない引数（小数や文字列など）が入力された場合、"
        "絶対に代替案や計算方法を自ら提案してはいけません。"
        "その場合は必ず「入力エラー：整数の計算のみ対応しています。窓口へお問い合わせください。」とだけ回答してください。"
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=text)
    ]
    ai_msg = llm_with_tools.invoke(messages)
    
    # ⑤ 通訳（LangChain）の動き：AIが「ツールを使いたい」と判断したかチェック
    if ai_msg.tool_calls:
        # AIの「ツールを使いたい」という要求を会話履歴に記録
        messages.append(ai_msg)
        
        # 指定された通りにPythonのツールを実行し、結果を履歴に記録
        for tool_call in ai_msg.tool_calls:
            if tool_call["name"] == "add":
                tool_msg = add.invoke(tool_call)
                messages.append(tool_msg)
                
        # ⑥ 計算結果を踏まえて、もう一度AIに最終的な日本語の回答を作らせる
        final_ai_msg = llm_with_tools.invoke(messages)
        return final_ai_msg.content
        
    # もしツールを使わずに普通に回答してきた場合
    return ai_msg.content
    


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    受講者は `run_chain()` の実装に集中し、ここは原則編集しません。
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
        out = run_chain(args.text)
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
