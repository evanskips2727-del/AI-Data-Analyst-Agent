"""
OPTIONAL / advanced: the same workflow as app/agent.py, re-implemented as a
LangGraph graph, to demonstrate familiarity with agent-orchestration
frameworks. Not used by app/main.py or cli.py by default (they use the plain
pipeline in app/agent.py, which is easier to read and test) — import and call
`run(question)` from here if you specifically want the LangGraph version.

Requires: pip install langgraph
"""
from typing import TypedDict

import pandas as pd

from app import llm
from app.charts import to_chart_spec
from app.db import engine
from app.sql_guard import SqlGuardError, validate_and_finalize
from sqlalchemy import text


class State(TypedDict, total=False):
    question: str
    draft_sql: str
    safe_sql: str
    df: pd.DataFrame
    summary: str
    chart: dict
    error: str


def _plan(state: State) -> State:
    try:
        state["draft_sql"] = llm.plan_sql(state["question"])
    except Exception as exc:
        state["error"] = f"Could not draft a query: {exc}"
    return state


def _validate(state: State) -> State:
    if state.get("error"):
        return state
    try:
        state["safe_sql"] = validate_and_finalize(state["draft_sql"])
    except SqlGuardError as exc:
        state["error"] = f"Query rejected: {exc}"
    return state


def _execute(state: State) -> State:
    if state.get("error"):
        return state
    try:
        with engine.connect() as conn:
            state["df"] = pd.read_sql_query(text(state["safe_sql"]), conn)
    except Exception as exc:
        state["error"] = f"Query failed to run: {exc}"
    return state


def _summarize(state: State) -> State:
    if state.get("error"):
        return state
    df = state["df"]
    state["summary"] = llm.summarize(state["question"], df)
    state["chart"] = to_chart_spec(df)
    return state


def build_graph():
    from langgraph.graph import END, StateGraph

    graph = StateGraph(State)
    graph.add_node("plan", _plan)
    graph.add_node("validate", _validate)
    graph.add_node("execute", _execute)
    graph.add_node("summarize", _summarize)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "validate")
    graph.add_edge("validate", "execute")
    graph.add_edge("execute", "summarize")
    graph.add_edge("summarize", END)

    return graph.compile()


def run(question: str) -> State:
    app_graph = build_graph()
    return app_graph.invoke({"question": question})


if __name__ == "__main__":
    import sys
    result = run(" ".join(sys.argv[1:]) or "Which counties have the largest gaps in reported service coverage?")
    print(result.get("summary") or result.get("error"))
