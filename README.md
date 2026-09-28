# AI Data Analyst Agent

An end-to-end **AI agent that answers natural-language questions about a dataset** by
generating SQL, validating it, running it safely against a database, and explaining
the results in plain English — with a chart on top.

Built to demonstrate skills relevant to data analytics / data engineering roles:
Python, SQL, LLM tool-use, API design (FastAPI), data validation, and safe query
execution.

> Example question: **"Which counties have the largest gaps in reported service coverage?"**

## Agent workflow

```mermaid
flowchart TD
    A[User asks a question] --> B[AI agent interprets request]
    B --> C[Selects the run_sql_query tool]
    C --> D[LLM drafts a SQL SELECT statement]
    D --> E[SQL guard validates the query]
    E --> F[Query runs against the database]
    F --> G[Results validated / summarized]
    G --> H[LLM explains findings in plain English]
    H --> I[API returns answer + table + chart data]
```

## Why this works out of the box (no API key required)

Real portfolio reviewers should be able to clone this and **run it immediately**.
The agent has two modes:

- **DEMO_MODE (default, no key needed):** a lightweight rule-based planner maps the
  question to one of several parameterized, pre-validated SQL templates, and a
  templated summarizer describes the results using pandas statistics. Fully
  functional, deterministic, zero cost.
- **LLM_MODE (set `ANTHROPIC_API_KEY`):** the same pipeline instead asks Claude to
  write the SQL and the explanation, still passing through the exact same SQL guard.

This means the project is honest about being an *agent* (LLM writes SQL + explains
findings) while still being trivially runnable for anyone reviewing your GitHub.

## Dataset

Synthetic, de-identified data modeled on Kenyan county-level service-coverage
reporting (health facility coverage, water access, electricity access, education
enrollment, road density) across all 47 counties, for 3 reporting years. Generated
by `data/generate_data.py` — no real records are used or required.

## Project structure

```
ai-data-analyst-agent/
├── app/
│   ├── main.py          FastAPI app (POST /ask, GET /health, GET /schema)
│   ├── agent.py         Orchestrates the workflow (interpret -> SQL -> guard -> run -> summarize)
│   ├── llm.py           Claude API wrapper + DEMO_MODE fallback planner/summarizer
│   ├── sql_guard.py      Validates/limits generated SQL (SELECT-only, whitelisted tables)
│   ├── db.py            SQLAlchemy engine/session (SQLite by default, Postgres via DATABASE_URL)
│   ├── schema.py        ORM model for county_service_coverage
│   └── charts.py        Turns a result set into simple chart-ready JSON
├── data/
│   ├── generate_data.py Synthetic data generator -> data/county_service_coverage.csv
│   └── seed.py          Loads the CSV into the configured database
├── frontend/
│   └── index.html       Minimal chat-style UI that calls the API
├── tests/
│   ├── test_sql_guard.py
│   └── test_agent.py
├── cli.py                Command-line chat interface (no server needed)
├── scripts/run.sh        One-command setup + launch
├── requirements.txt
├── .env.example
└── .github/workflows/ci.yml   Runs tests on push
```

## Quickstart

```bash
git clone <your-fork-url>
cd ai-data-analyst-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # optional: add ANTHROPIC_API_KEY to enable LLM_MODE
python data/generate_data.py    # creates data/county_service_coverage.csv
python data/seed.py             # loads it into SQLite (data/app.db)
uvicorn app.main:app --reload   # starts the API on http://localhost:8000
```

Then open `frontend/index.html` in a browser (or visit `http://localhost:8000/docs`
for the interactive API docs), and ask something like:

- "Which counties have the largest gaps in reported service coverage?"
- "Top 5 counties by water access in 2024"
- "How does health facility coverage compare across regions?"

Or skip the server entirely:

```bash
python cli.py "Which counties have the largest gaps in reported service coverage?"
```

`scripts/run.sh` does all of the above (venv, install, generate data, seed, launch)
in one command.

## Switching to Postgres

Set `DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname` in `.env` before
running `seed.py` — SQLAlchemy handles the rest, no code changes needed.

## Safety: how the SQL guard works

`app/sql_guard.py` rejects any statement that:
- is not a single `SELECT` statement (blocks `INSERT`/`UPDATE`/`DELETE`/`DROP`/`;`-chained statements)
- references a table or column outside an explicit whitelist
- has no `LIMIT` (one is injected automatically, capped at 500 rows)

Every query — whether written by the demo planner or by Claude — passes through this
guard before it ever touches the database.

## Tests

```bash
pytest
```

Covers SQL-guard rejection of destructive statements and an end-to-end agent run in
DEMO_MODE.

## License

MIT — see `LICENSE`.
