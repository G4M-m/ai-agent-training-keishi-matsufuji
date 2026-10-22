from __future__ import annotations

import argparse
import logging
import sys
from typing import List, TypedDict, Optional
from langgraph.graph import StateGraph, START, END


def build_parser() -> argparse.ArgumentParser:
    """Day08のCLI引数を定義します（入力と上限設定）。"""
    p = argparse.ArgumentParser(prog="day08")
    p.add_argument("--text", required=True)
    p.add_argument("--max-steps", type=int, default=10)
    p.add_argument("--max-retry", type=int, default=1)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.text:
        raise ValueError("--text is required")
    if not (1 <= args.max_steps <= 50):
        raise ValueError("--max-steps must be between 1 and 50")
    if not (0 <= args.max_retry <= 5):
        raise ValueError("--max-retry must be between 0 and 5")


# --- 1. State（バインダー）：状態とカウンターの定義 ---
class AgentState(TypedDict):
    input: str
    status: str          # "success" | "json_error" | "no_hit"
    retry_count: int     # 現在のリトライ回数
    max_retry: int       # 最大リトライ上限
    step_count: int      # 現在の累計ステップ数
    max_steps: int       # 最大ステップ上限
    output: str
    errors: Optional[str]


def _check_step_limit(step_count: int, max_steps: int) -> None:
    """最大ステップ数の上限チェック（上限を超えたらエラーで強制停止）"""
    if step_count > max_steps:
        raise RuntimeError(f"最大ステップ数上限（max_steps={max_steps}）に到達したため、処理を強制終了しました。")


# --- 2. Node（各担当者の箱）：実作業を行う関数 ---
def execute_node(state: AgentState) -> dict:
    """メイン処理（検索やJSON生成のシミュレーション）を行う担当者"""
    step_count = state["step_count"] + 1
    _check_step_limit(step_count, state["max_steps"])

    user_input = state["input"]
    retry_count = state["retry_count"]

    # ケース1：検索ヒットなし（フォールバックへ逃がすパターン）
    if "存在しない" in user_input:
        print(f"[実行担当 (Step {step_count})] 検索を実行しましたが、該当データが0件でした。")
        return {
            "status": "no_hit",
            "step_count": step_count,
            "errors": "SearchError: 0 hits"
        }

    # ケース2：JSONパース失敗（1回目のリトライで復帰成功するパターン）
    if "不完全なJSON" in user_input:
        if retry_count == 0:
            print(f"[実行担当 (Step {step_count})] 生成されたJSONのパースに失敗しました。（現在のリトライ回数: {retry_count}）")
            return {
                "status": "json_error",
                "step_count": step_count,
                "errors": "JSONDecodeError: Expecting property name"
            }
        else:
            print(f"[実行担当 (Step {step_count})] リトライ（{retry_count}回目）により、正しいJSONの再生成に成功しました。")
            return {
                "status": "success",
                "step_count": step_count,
                "output": '【正常完了（リトライ復帰）】{"result": "再生成された正常なJSONデータ"}',
                "errors": None
            }

    # ケース3：通常の正常処理
    print(f"[実行担当 (Step {step_count})] 処理を正常に完了しました。")
    return {
        "status": "success",
        "step_count": step_count,
        "output": f"【正常回答】「{user_input}」についての回答結果です。",
        "errors": None
    }


def retry_node(state: AgentState) -> dict:
    """リトライ回数をカウントアップし、再実行へ差し戻す担当者"""
    step_count = state["step_count"] + 1
    _check_step_limit(step_count, state["max_steps"])

    new_retry = state["retry_count"] + 1
    print(f"[リトライ担当 (Step {step_count})] エラー（{state['errors']}）を検知。再生成へ差し戻します（リトライ {new_retry}/{state['max_retry']} 回目）...")
    return {
        "retry_count": new_retry,
        "step_count": step_count
    }


def fallback_node(state: AgentState) -> dict:
    """検索0件の際に、質問の聞き返しテキストを作成する退避先の担当者"""
    step_count = state["step_count"] + 1
    _check_step_limit(step_count, state["max_steps"])

    print(f"[フォールバック担当 (Step {step_count})] 検索ヒットなしのため、聞き返しルートへ退避しました。")
    return {
        "step_count": step_count,
        "output": "【フォールバック回答】該当する情報が見つかりませんでした。検索キーワードを変更するか、条件を具体的にして再度お試しください。"
    }


def abort_node(state: AgentState) -> dict:
    """リトライ上限到達時に、無限ループを防いでエラー終了させる担当者"""
    print(f"[強制終了] リトライ上限（max_retry={state['max_retry']}）に到達しました。")
    raise RuntimeError(f"リトライ上限（{state['max_retry']}回）に到達したため処理を失敗終了しました。最後のエラー: {state['errors']}")


# --- 3. Edge（分岐ルーター）：結果と上限を見て次の矢印を決める関数 ---
def route_after_execute(state: AgentState) -> str:
    """execute_node の結果（status）とリトライ回数を見て行き先を振り分ける"""
    status = state["status"]

    if status == "success":
        return "end"
    elif status == "no_hit":
        return "fallback"
    elif status == "json_error":
        if state["retry_count"] < state["max_retry"]:
            return "retry"
        else:
            return "abort"
    return "abort"


def run_graph(*, text: str, max_steps: int, max_retry: int) -> str:
    """失敗時復帰（リトライ/フォールバック）付きのフローを実行します。"""
    workflow = StateGraph(AgentState)

    # ノード（箱）の登録
    workflow.add_node("execute", execute_node)
    workflow.add_node("retry", retry_node)
    workflow.add_node("fallback", fallback_node)
    workflow.add_node("abort", abort_node)

    # エッジ（矢印）の配線
    workflow.add_edge(START, "execute")

    workflow.add_conditional_edges(
        "execute",
        route_after_execute,
        {
            "end": END,
            "retry": "retry",
            "fallback": "fallback",
            "abort": "abort"
        }
    )

    # リトライから実行担当へ戻るループの矢印
    workflow.add_edge("retry", "execute")

    # フォールバックと強制終了からENDへの矢印
    workflow.add_edge("fallback", END)
    workflow.add_edge("abort", END)

    app = workflow.compile()

    initial_state: AgentState = {
        "input": text,
        "status": "",
        "retry_count": 0,
        "max_retry": max_retry,
        "step_count": 0,
        "max_steps": max_steps,
        "output": "",
        "errors": None
    }

    final_state = app.invoke(initial_state)
    return final_state["output"]


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    受講者は `run_graph()` を実装します。ここは引数解析/検証/上限の適用/終了コードを担当します。
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)

    try:
        _validate_args(args)
    except Exception as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    logging.info("max-steps=%s max-retry=%s", args.max_steps, args.max_retry)

    try:
        out = run_graph(text=args.text, max_steps=args.max_steps, max_retry=args.max_retry)
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
