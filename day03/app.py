from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Dict, List


def build_parser() -> argparse.ArgumentParser:
    """Day03のCLI引数を定義します（要件文とリトライ回数）。"""
    p = argparse.ArgumentParser(prog="day03")
    p.add_argument("--requirements", required=True)
    p.add_argument("--max-retry", type=int, default=1)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.requirements:
        raise ValueError("--requirements is required")
    if not (0 <= args.max_retry <= 3):
        raise ValueError("--max-retry must be between 0 and 3")


def generate_json(requirements: str) -> str:
    """要件文字列から、JSON文字列（本文のみ）を生成して返します。"""
    import os
    import json
    import boto3
    from botocore.config import Config

    region = os.getenv("AWS_REGION", "us-east-2")
    model_id = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0")

    # システムインストラクション（LLMの出力フォーマットをJSONに強制する厳格な指示）
    prompt = f"""
以下の要件に基づいてタスクとリスクを分析し、指定されたJSONフォーマットのみを出力してください。
前置き、解説、Markdownのコードブロック(```json)などの余計な文字列は一切含めず、純粋なJSON文字列だけを返してください。

[要件]
{requirements}

[出力形式]
{{
  "title": "要件の要約タイトル",
  "tasks": [
    {{
      "id": 1,
      "description": "作業内容の詳細",
      "acceptance_criteria": "完了条件"
    }}
  ],
  "risks": [
    "想定されるリスク1",
    "想定されるリスク2"
  ]
}}
"""

    config = Config(read_timeout=30)
    client = boto3.client("bedrock-runtime", region_name=region, config=config)

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 5000,
        "temperature": 0.0,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(request_body)
    )

    response_body = json.loads(response.get("body").read())
    reply_text = response_body["content"][0]["text"]
    
    # LLMが万が一 ```json ... ``` で囲ってしまった場合の保険（簡易的なクレンジング）
    reply_text = reply_text.strip()
    if reply_text.startswith("```json"):
        reply_text = reply_text[7:]
    if reply_text.endswith("```"):
        reply_text = reply_text[:-3]
        
    return reply_text.strip()

def validate_json(text: str) -> Dict[str, Any]:
    """生成結果のJSONを検証します（必須キーと型）。"""
    obj = json.loads(text)
    for key in ("title", "tasks", "risks"):
        if key not in obj:
            raise ValueError(f"missing key: {key}")
    if not isinstance(obj.get("tasks"), list):
        raise ValueError("tasks must be a list")
    return obj


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    JSON生成→検証→（失敗時は再生成）までを制御します。受講者は `generate_json()` を実装します。
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

    last_err: Exception | None = None
    for _ in range(args.max_retry + 1):
        try:
            text = generate_json(args.requirements)
            validate_json(text)
            print(text)
            return 0
        except NotImplementedError as e:
            logging.error(str(e))
            print(str(e), file=sys.stderr)
            return 1
        except Exception as e:
            last_err = e

    msg = str(last_err) if last_err else "validation failed"
    logging.error(msg)
    print(msg, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
