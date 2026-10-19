from __future__ import annotations

import argparse
import logging
import sys
from typing import List, TypedDict, Optional
from langgraph.graph import StateGraph, START, END

# --- 1. State（状態）の定義：システム全体で持ち回る「稟議書」 ---
class AgentState(TypedDict):
    input: str
    intent: str
    output: str
    errors: Optional[str]

# --- 2. Node（ノード）の定義：個別の作業を行う担当者 ---
def classifier_node(state: AgentState) -> dict:
    """入力を分析し、intent（意図）を決定する分類担当"""
    user_input = state["input"]
    
    if "教えて" in user_input or "調べて" in user_input:
        intent = "rag"
    elif "要約" in user_input:
        intent = "summarize"
    else:
        intent = "fallback"
        
    print(f"[分類担当] 入力を '{intent}' と分類しました。")
    return {"intent": intent}

def rag_node(state: AgentState) -> dict:
    """RAG（検索）処理の担当"""
    print("[RAG担当] 検索ベースの回答を作成します...")
    return {"output": "【RAG回答】検索結果に基づいて回答を作成しました。"}

def summarize_node(state: AgentState) -> dict:
    """要約処理の担当"""
    print("[要約担当] 入力文の要約を作成します...")
    return {"output": "【要約回答】入力された文章を要約しました。"}

def fallback_node(state: AgentState) -> dict:
    """分類不能時のデフォルト処理担当"""
    print("[デフォルト担当] 処理をフォールバックします...")
    return {"output": "【フォールバック】その質問の意図は判定できませんでした。"}

# --- 3. Edge（エッジ）の定義：分岐ルーター ---
def route_by_intent(state: AgentState) -> str:
    """バインダーの intent 欄を見て、次に渡す担当者（ノード名）を決定する"""
    return state["intent"]

def build_parser() -> argparse.ArgumentParser:
    """Day07のCLI引数を定義します（入力と分類モード）。"""
    p = argparse.ArgumentParser(prog="day07")
    p.add_argument("--text", required=True)
    p.add_argument("--mode", choices=["llm", "rule"], default="rule")
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.text:
        raise ValueError("--text is required")

def run_graph(*, text: str, mode: str) -> str:
    """LangGraphで「分類→分岐→処理」を実行し、最終出力（文字列）を返します。"""
    # 1. ワークフローの土台作成
    workflow = StateGraph(AgentState)

    # 2. 担当者の配属
    workflow.add_node("classifier", classifier_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("fallback", fallback_node)

    # 3. レールを敷く（START → 分類担当へ）
    workflow.add_edge(START, "classifier")

    # 4. 条件分岐ルーターの設置
    workflow.add_conditional_edges(
        "classifier",
        route_by_intent,
        {
            "rag": "rag",
            "summarize": "summarize",
            "fallback": "fallback"
        }
    )

    # 5. 個別処理からゴール（END）へのレール
    workflow.add_edge("rag", END)
    workflow.add_edge("summarize", END)
    workflow.add_edge("fallback", END)

    # 6. コンパイル（組み立て完了）
    app = workflow.compile()

    # 7. 実行（バインダーを投入してフロー開始）
    initial_state = {"input": text, "intent": "", "output": "", "errors": None}
    final_state = app.invoke(initial_state)

    return final_state["output"]


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    受講者は `run_graph()` を実装します。ここは引数解析/検証/終了コードを担当します。
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)

    try:
        _validate_args(args)
    except Exception as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    logging.info("mode=%s", args.mode)

    try:
        out = run_graph(text=args.text, mode=args.mode)
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
