from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agent import answer_question
from app.llm import DEMO_MODE
from app.schema import SCHEMA_DESCRIPTION

app = FastAPI(
    title="AI Data Analyst Agent",
    description="Ask natural-language questions about county service-coverage data.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    question: str
    sql: str
    columns: list[str] = []
    rows: list[dict] = []
    summary: str = ""
    chart: dict | None = None
    error: str | None = None
    demo_mode: bool = DEMO_MODE


@app.get("/health")
def health():
    return {"status": "ok", "demo_mode": DEMO_MODE}


@app.get("/schema")
def schema():
    return {"schema": SCHEMA_DESCRIPTION, "demo_mode": DEMO_MODE}


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    result = answer_question(payload.question)
    return AskResponse(
        question=result.question,
        sql=result.sql,
        columns=result.columns,
        rows=result.rows,
        summary=result.summary,
        chart=result.chart,
        error=result.error,
        demo_mode=DEMO_MODE,
    )
