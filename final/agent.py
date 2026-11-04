from __future__ import annotations

import json
import os
from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph

DANGEROUS_KEYWORDS = ("前の指示は無視", "秘密情報", "システムプロンプト")

OPEN_DATA_DOCS = [
    {
        "id": "doc-gif-01",
        "title": "デジタル庁 政府相互運用性フレームワーク（GIF）",
        "url": "https://www.digital.go.jp/policies/data_strategy/gif",
        "license": "CC BY 4.0（公共データ利用規約 第1.0版）",
        "keywords": ["オープンデータ", "デジタル", "データ", "調査", "〇〇"],
        "excerpt": "行政機関や民間企業がデータを相互に連携・活用するための標準仕様およびデータモデルを定義しています。",
    },
    {
        "id": "doc-cloud-02",
        "title": "デジタル庁 ガバメントクラウド利用指針",
        "url": "https://www.digital.go.jp/policies/gov_cloud",
        "license": "CC BY 4.0（公共データ利用規約 第1.0版）",
        "keywords": ["クラウド", "セキュリティ", "AI", "システム", "調査"],
        "excerpt": "クラウドスマートの方針に基づき、迅速・柔軟かつセキュアなシステム構築と運用監視の自動化を推進しています。",
    },
]


class AgentState(TypedDict, total=False):
    query: str
    status: str
    docs: List[Dict[str, str]]
    structured: Dict[str, Any]
    reply: str
    steps: int


def search_open_data_tool(query: str) -> List[Dict[str, str]]:
    """[Tool] 公開データからキーワードに一致するドキュメントを検索します。"""
    if "該当なし" in query or "ヒットなし" in query:
        return []
    return [doc for doc in OPEN_DATA_DOCS if any(kw in query for kw in doc["keywords"])]


def _guard_node(state: AgentState) -> AgentState:
    q = state.get("query", "").strip()
    steps = state.get("steps", 0) + 1
    if not q:
        return {**state, "status": "invalid", "steps": steps}
    if any(kw in q for kw in DANGEROUS_KEYWORDS):
        return {**state, "status": "blocked", "steps": steps}
    return {**state, "status": "ok", "steps": steps}


def _tool_node(state: AgentState) -> AgentState:
    docs = search_open_data_tool(state.get("query", ""))
    status = "found" if docs else "not_found"
    return {**state, "docs": docs, "status": status, "steps": state.get("steps", 0) + 1}


def _generate_node(state: AgentState) -> AgentState:
    q = state.get("query", "")
    docs = state.get("docs", [])
    citations = [
        {"title": d["title"], "url": d["url"], "excerpt": d["excerpt"], "license": d["license"]}
        for d in docs
    ]
    summary = f"「{q}」について公開データを調査した結果、{docs[0]['excerpt']}"
    structured = {
        "answer_summary": summary,
        "citations": citations,
        "confidence": "high",
        "next_actions": [
            "提示された出典URLから最新のガイドライン原文を確認する",
            "具体的な適用対象（システム要求やデータ項目）を絞り込んで再調査する",
        ],
    }
    cite_lines = "\n".join([f"- {c['title']} ({c['url']}): \"{c['excerpt']}\"" for c in citations])
    reply = (
        f"【回答】\n{summary}\n\n"
        f"【根拠】\n{cite_lines}\n\n"
        f"【構造化出力】\n{json.dumps(structured, ensure_ascii=False, indent=2)}"
    )
    return {**state, "structured": structured, "reply": reply, "steps": state.get("steps", 0) + 1}


def _fallback_node(state: AgentState) -> AgentState:
    status = state.get("status", "")
    if status == "blocked":
        msg = "セキュリティポリシーにより、指示の乗っ取りや秘密情報に関する要求は処理できません。"
        action = "安全な通常の質問形式で再入力してください"
    elif status == "invalid":
        msg = "入力が空です。調査したいテーマを入力してください。"
        action = "調査対象のキーワードを入力して再実行してください"
    else:
        msg = "公開データ内に該当する根拠が見つかりませんでした（検索ヒット0件）。推測による回答を防ぐため保留します。"
        action = "「オープンデータ」「クラウド」「セキュリティ」などのキーワードを含めて再質問してください"

    structured = {
        "answer_summary": msg,
        "citations": [],
        "confidence": "low",
        "next_actions": [action],
    }
    reply = (
        f"【回答（フォールバック）】\n{msg}\n\n"
        f"【根拠】\n 該当なし（出典0件）\n\n"
        f"【構造化出力】\n{json.dumps(structured, ensure_ascii=False, indent=2)}"
    )
    return {**state, "structured": structured, "reply": reply, "steps": state.get("steps", 0) + 1}


def _build_graph():
    g = StateGraph(AgentState)
    g.add_node("guard", _guard_node)
    g.add_node("search_tool", _tool_node)
    g.add_node("generate", _generate_node)
    g.add_node("fallback", _fallback_node)
    g.set_entry_point("guard")
    g.add_conditional_edges("guard", lambda s: "search_tool" if s.get("status") == "ok" else "fallback")
    g.add_conditional_edges("search_tool", lambda s: "generate" if s.get("status") == "found" else "fallback")
    g.add_edge("generate", END)
    g.add_edge("fallback", END)
    return g.compile()


def run_agent(message: str, history: List[Dict[str, str]] | None = None) -> Dict[str, Any]:
    """チャットUI（`final/chat_ui.py`）から呼び出されるエージェントの入口です。

    受講者が実装する場所は基本的にこの関数（またはこの関数が呼ぶ下位関数）です。

    実装の方針（例）：
    - LangGraphでstateを持つフローを構築
    - ツール（RAG検索、計算、日付取得など）をTool callingで呼び出す
    - 失敗時フォールバック（検索ヒットなし、JSON破損など）を入れる

    引数：
    - message: ユーザーの最新発話
    - history: これまでの会話履歴（role/contentの配列）

    戻り値（辞書）：
    - reply: str（ユーザーに見せる本文）
    - meta: dict（任意。デバッグ用情報や構造化出力を入れてよい）

    注意：
    - APIキーや認証情報をコードに直書きしない
    - 例外は握りつぶさず、UI側で原因が分かるよう meta に入れるか適切にエラー化する
    """
    history = history or []
    app = _build_graph()
    final_state = app.invoke({"query": message, "steps": 0})
    return {
        "reply": final_state.get("reply", ""),
        "meta": {
            "status": final_state.get("status"),
            "steps": final_state.get("steps"),
            "history_len": len(history),
            "model_id": os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
            "structured": final_state.get("structured", {}),
        },
    }