"""
Orchestrates the agent workflow shown in the project README:

    user question -> interpret -> select tool -> draft SQL -> validate ->
    execute -> summarize -> return answer + table + chart

This is a plain function pipeline rather than a framework, which keeps it easy
to read, test, and explain in an interview. `agent_langgraph.py` shows the same
pipeline re-implemented as a LangGraph graph, for anyone who wants to see the
more "agentic framework" version.
"""
from dataclasses import dataclass, field

import pandas as pd
from sqlalchemy import text

from app import llm
from app.charts import to_chart_spec
from app.db import engine
from app.sql_guard import SqlGuardError, validate_and_finalize


@dataclass
class AgentResult:
    question: str
    sql: str
    rows: list = field(default_factory=list)
    columns: list = field(default_factory=list)
    summary: str = ""
    chart: dict | None = None
    error: str | None = None


ONE_APPROVED_TOOL = "run_sql_query"  # the agent has exactly one tool available


def _run_sql_query(sql: str) -> pd.DataFrame:
    """The agent's single approved tool: read-only SQL execution."""
    with engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn)


def answer_question(question: str) -> AgentResult:
    question = (question or "").strip()
    if not question:
        return AgentResult(question=question, sql="", error="Please ask a question.")

    # 1. Interpret request + 2. select tool + 3. draft SQL (the only tool call
    #    this agent can make is run_sql_query, so "tool selection" is a no-op
    #    here but is kept explicit for clarity / future extension).
    try:
        draft_sql = llm.plan_sql(question)
    except Exception as exc:  # LLM/network failure -> fail loud, not silently
        return AgentResult(question=question, sql="", error=f"Could not draft a query: {exc}")

    # 4. Validate query.
    try:
        safe_sql = validate_and_finalize(draft_sql)
    except SqlGuardError as exc:
        return AgentResult(question=question, sql=draft_sql, error=f"Query rejected: {exc}")

    # 5. Execute + validate results.
    try:
        df = _run_sql_query(safe_sql)
    except Exception as exc:
        return AgentResult(question=question, sql=safe_sql, error=f"Query failed to run: {exc}")

    # 6. Explain findings.
    try:
        summary = llm.summarize(question, df)
    except Exception as exc:
        summary = f"(Could not generate a summary: {exc})"

    # 7. Return answer + chart.
    return AgentResult(
        question=question,
        sql=safe_sql,
        rows=df.to_dict(orient="records"),
        columns=list(df.columns),
        summary=summary,
        chart=to_chart_spec(df),
    )
