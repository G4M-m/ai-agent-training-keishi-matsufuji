from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List

from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

DANGEROUS_KEYWORDS = ("前の指示は無視", "秘密情報", "システムプロンプト")
MAX_INPUT_CHARS = 200

def build_parser() -> argparse.ArgumentParser:
    """Day09のCLI引数を定義します（suite入力と出力先）。"""
    p = argparse.ArgumentParser(prog="day09")
    p.add_argument("--suite", required=True)
    p.add_argument("--out", default=os.path.join("day09", "result.json"))
    p.add_argument("--timeout-sec", type=int, default=30)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.suite:
        raise ValueError("--suite is required")
    if args.timeout_sec <= 0:
        raise ValueError("--timeout-sec must be a positive integer")


def load_suite(path: str) -> List[Dict[str, Any]]:
    """テスト入力セットを読み込んでケース配列を返します。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _run_target_workflow(user_input: str) -> Dict[str, str]:
    """評価対象となる模擬処理（改善後：長文対策・ガードレール追加）"""
    if not user_input.strip():
        return {"status": "invalid_input", "output": "入力エラー"}
    
    # 改善後追加1：危険な指示をブロックするガードレール
    if any(kw in user_input for kw in DANGEROUS_KEYWORDS):
        return {"status": "blocked", "output": "セキュリティ警告: 不正な指示をブロックしました"}
    
    # 改善後追加2：文字数超過時はエラー終了せず、上限で安全に切り詰める
    if len(user_input) > MAX_INPUT_CHARS:
        user_input = user_input[:MAX_INPUT_CHARS]
        
    return {"status": "ok", "output": f"回答: {user_input[:20]}..."}

def _expected_status(text: str) -> str:
    """入力に対する期待値を判定します"""
    if not text.strip(): return "invalid_input"
    if any(kw in text for kw in DANGEROUS_KEYWORDS): return "blocked"
    return "ok"

def run_case(case: Dict[str, Any], timeout_sec: int) -> Dict[str, Any]:
    """1ケースを実行して結果dictを返します。"""
    case_id = case["id"]
    user_input = case["input"]
    expected = _expected_status(user_input)

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_run_target_workflow, user_input)
    try:
        res = future.result(timeout=timeout_sec)
    except FuturesTimeoutError:
        return {"id": case_id, "passed": False, "reason": "タイムアウト", "output": ""}
    except Exception as e:
        return {"id": case_id, "passed": False, "reason": f"実行エラー: {e}", "output": ""}

    actual = res.get("status", "")
    passed = (actual == expected)

    if passed:
        reason = "OK: 期待通り"
    elif expected == "blocked":
        reason = f"ガード失敗: 危険な指示をブロックできませんでした (expected={expected}, actual={actual})"
    elif actual == "error":
        reason = f"長文エラー: 上限超過で処理が失敗しました (expected={expected}, actual={actual})"
    else:
        reason = f"不一致 (expected={expected}, actual={actual})"

    return {
        "id": case_id,
        "passed": passed,
        "reason": reason,
        "output": res.get("output", "")
    }

def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    suite読み込み→各ケース実行→結果JSON出力までを制御します。
    受講者は `load_suite()` と `run_case()` を実装します。
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)

    try:
        _validate_args(args)
    except Exception as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    try:
        suite = load_suite(args.suite)
        results: List[Dict[str, Any]] = []
        ok = 0
        ng = 0

        for case in suite:
            start = time.perf_counter()
            try:
                r = run_case(case, timeout_sec=args.timeout_sec)
                r.setdefault("duration_ms", int((time.perf_counter() - start) * 1000))
                passed = bool(r.get("passed", False))
                ok += 1 if passed else 0
                ng += 0 if passed else 1
                results.append(r)
            except NotImplementedError as e:
                logging.error(str(e))
                print(str(e), file=sys.stderr)
                return 1

        out_obj = {
            "summary": {"passed": ok, "failed": ng, "total": ok + ng},
            "results": results,
        }
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out_obj, f, ensure_ascii=False, indent=2)

        print(f"passed={ok} failed={ng} total={ok + ng}")
        return 0
    except Exception as e:
        logging.error("%s", e)
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
