"""
Two responsibilities, each with a DEMO_MODE (no API key) and LLM_MODE path:

  1. plan_sql(question) -> SQL string       ("AI agent interprets request" + drafts SQL)
  2. summarize(question, df) -> str          ("Explains its findings")

DEMO_MODE keeps the project fully runnable with zero API cost by matching the
question against a small set of intents and filling in a parameterized,
already-safe SQL template. LLM_MODE asks Claude to do the same job for
arbitrary questions, but the result still passes through app/sql_guard.py
before anything runs.
"""
import os
import re

from dotenv import load_dotenv

from app.schema import SCHEMA_DESCRIPTION, TABLE_NAME

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
DEMO_MODE = not bool(ANTHROPIC_API_KEY)

SYSTEM_PROMPT_SQL = f"""You are a careful data analyst. You write a single SQLite \
SELECT statement (and nothing else - no markdown, no commentary) that answers the \
user's question using only this schema:

{SCHEMA_DESCRIPTION}

Rules: SELECT statements only. Never modify data. Always include a LIMIT. Only use \
the table and columns listed above."""

SYSTEM_PROMPT_SUMMARY = """You are a data analyst explaining query results to a \
non-technical stakeholder. Given the user's question and a small results table, \
write a concise (3-5 sentence) plain-English explanation of what the data shows. \
Mention specific numbers/names from the table. Do not mention SQL."""


def _client():
    from anthropic import Anthropic
    return Anthropic(api_key=ANTHROPIC_API_KEY)


# ---------------------------------------------------------------------------
# DEMO_MODE planner: keyword-matched, parameterized, already-whitelisted SQL.
# ---------------------------------------------------------------------------
def _demo_plan_sql(question: str) -> str:
    q = question.lower()

    metric_map = {
        "health": "health_facility_coverage_pct",
        "water": "water_access_pct",
        "electric": "electricity_access_pct",
        "education": "education_enrollment_pct",
        "enroll": "education_enrollment_pct",
        "road": "road_coverage_km_per_1000",
        "population": "population",
    }
    metric = "health_facility_coverage_pct"
    for key, col in metric_map.items():
        if key in q:
            metric = col
            break

    year_match = re.search(r"(20\d{2})", q)
    year_clause = f"WHERE reporting_year = {year_match.group(1)}" if year_match else ""

    n_match = re.search(r"top\s+(\d+)|(\d+)\s+largest|(\d+)\s+highest", q)
    n = next((g for g in (n_match.groups() if n_match else []) if g), "5") if n_match else "10"

    if "gap" in q or "largest gaps" in q or "worst" in q or "lowest" in q:
        # Average across the four coverage metrics as a simple composite "gap" score.
        return (
            "SELECT county, region, reporting_year, "
            "ROUND((health_facility_coverage_pct + water_access_pct + "
            "electricity_access_pct + education_enrollment_pct) / 4.0, 1) "
            "AS avg_coverage_pct "
            f"FROM {TABLE_NAME} {year_clause} "
            "ORDER BY avg_coverage_pct ASC LIMIT 10"
        )

    if "region" in q or "compare" in q:
        return (
            f"SELECT region, ROUND(AVG({metric}), 1) AS avg_value "
            f"FROM {TABLE_NAME} {year_clause} "
            "GROUP BY region ORDER BY avg_value DESC LIMIT 20"
        )

    if "top" in q or "highest" in q or "largest" in q or "best" in q:
        return (
            f"SELECT county, region, reporting_year, {metric} "
            f"FROM {TABLE_NAME} {year_clause} "
            f"ORDER BY {metric} DESC LIMIT {n}"
        )

    # Default: show the requested metric per county for the (optional) year.
    return (
        f"SELECT county, region, reporting_year, {metric} "
        f"FROM {TABLE_NAME} {year_clause} "
        f"ORDER BY {metric} DESC LIMIT 15"
    )


def _demo_summarize(question: str, df) -> str:
    if df.empty:
        return "No rows matched that question — try rephrasing it or removing a filter."

    numeric_cols = [c for c in df.columns if df[c].dtype.kind in "if" and c != "reporting_year"]
    lines = [f"Your question returned {len(df)} row(s)."]

    if numeric_cols:
        col = numeric_cols[0]
        top_row = df.iloc[0]
        bottom_row = df.iloc[-1]
        lines.append(
            f"'{top_row.get('county', top_row.get('region', 'Top result'))}' leads on "
            f"{col.replace('_', ' ')} at {top_row[col]}, while "
            f"'{bottom_row.get('county', bottom_row.get('region', 'the lowest result'))}' "
            f"is lowest at {bottom_row[col]}."
        )
        lines.append(
            f"Across the returned rows, {col.replace('_', ' ')} averages "
            f"{round(df[col].mean(), 1)}, ranging from {df[col].min()} to {df[col].max()}."
        )
    return " ".join(lines)


# ---------------------------------------------------------------------------
# Public API used by app/agent.py
# ---------------------------------------------------------------------------
def plan_sql(question: str) -> str:
    if DEMO_MODE:
        return _demo_plan_sql(question)

    response = _client().messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=300,
        system=SYSTEM_PROMPT_SQL,
        messages=[{"role": "user", "content": question}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    # Strip accidental markdown fences.
    return re.sub(r"^```sql|```$|^```", "", text.strip(), flags=re.MULTILINE).strip()


def summarize(question: str, df) -> str:
    if DEMO_MODE:
        return _demo_summarize(question, df)

    table_preview = df.head(20).to_csv(index=False)
    user_msg = f"Question: {question}\n\nResults (CSV):\n{table_preview}"
    response = _client().messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=400,
        system=SYSTEM_PROMPT_SUMMARY,
        messages=[{"role": "user", "content": user_msg}],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()
