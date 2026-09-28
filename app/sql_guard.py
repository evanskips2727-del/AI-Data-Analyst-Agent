"""
Validates SQL produced by the agent (whether by the demo planner or by an LLM)
before it is allowed anywhere near the database.

Rules enforced:
  1. Exactly one statement.
  2. That statement must be a SELECT (no INSERT/UPDATE/DELETE/DROP/ALTER/ATTACH/etc).
  3. No semicolon-chained statements ("SELECT 1; DROP TABLE ...").
  4. Only whitelisted tables/columns may be referenced.
  5. A LIMIT is enforced (added if missing, capped if too high).

This module is intentionally strict and dependency-light: sqlparse for tokenizing,
plain string/regex checks for the rest. It is the single choke point every
generated query passes through.
"""
import re

import sqlparse
from sqlparse.tokens import DDL, DML, Keyword

from app.schema import ALLOWED_COLUMNS, ALLOWED_TABLES

MAX_LIMIT = 500
DEFAULT_LIMIT = 100

FORBIDDEN_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE",
    "ATTACH", "DETACH", "REPLACE", "GRANT", "REVOKE", "PRAGMA", "VACUUM",
    "EXEC", "EXECUTE", "CALL",
}


class SqlGuardError(ValueError):
    pass


def _statements(sql: str):
    stripped = sql.strip().rstrip(";")
    if ";" in stripped:
        raise SqlGuardError("Multiple statements are not allowed.")
    parsed = sqlparse.parse(stripped)
    if len(parsed) != 1:
        raise SqlGuardError("Expected exactly one SQL statement.")
    return stripped, parsed[0]


def _assert_select_only(statement) -> None:
    stmt_type = statement.get_type()
    if stmt_type != "SELECT":
        raise SqlGuardError(f"Only SELECT statements are allowed (got {stmt_type}).")

    for token in statement.flatten():
        if token.ttype in (DDL, DML) and token.value.upper() != "SELECT":
            raise SqlGuardError(f"Disallowed keyword: {token.value.upper()}")
        if token.ttype is Keyword and token.value.upper() in FORBIDDEN_KEYWORDS:
            raise SqlGuardError(f"Disallowed keyword: {token.value.upper()}")


def _assert_identifiers_allowed(sql: str) -> None:
    # Cheap but effective for this fixed, single-table schema: every bare
    # identifier-looking token must be an allowed column/table name, a SQL
    # keyword/function, or a literal. We whitelist rather than blacklist.
    identifiers = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", sql)
    allowed = ALLOWED_TABLES | ALLOWED_COLUMNS | _SQL_SAFE_WORDS
    for ident in identifiers:
        if ident.upper() in _SQL_KEYWORDS_AND_FUNCS:
            continue
        if ident in allowed:
            continue
        raise SqlGuardError(f"Unrecognized identifier '{ident}' is not allowed.")


_SQL_KEYWORDS_AND_FUNCS = {
    "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "IN", "AS", "ON",
    "GROUP", "BY", "ORDER", "ASC", "DESC", "LIMIT", "OFFSET", "AVG", "SUM",
    "COUNT", "MIN", "MAX", "ROUND", "DISTINCT", "BETWEEN", "LIKE", "IS",
    "NULL", "CASE", "WHEN", "THEN", "ELSE", "END", "JOIN", "INNER", "LEFT",
    "HAVING", "ALL", "ANY", "EXISTS",
}
_SQL_SAFE_WORDS: set[str] = set()  # reserved for future literal-name allowances


def validate_and_finalize(sql: str) -> str:
    """Raises SqlGuardError on anything unsafe; otherwise returns a safe,
    LIMIT-enforced version of the query ready to execute."""
    stripped, statement = _statements(sql)
    _assert_select_only(statement)
    _assert_identifiers_allowed(stripped)

    limit_match = re.search(r"LIMIT\s+(\d+)", stripped, re.IGNORECASE)
    if limit_match:
        requested = int(limit_match.group(1))
        capped = min(requested, MAX_LIMIT)
        stripped = re.sub(
            r"LIMIT\s+\d+", f"LIMIT {capped}", stripped, flags=re.IGNORECASE
        )
    else:
        stripped = f"{stripped} LIMIT {DEFAULT_LIMIT}"

    return stripped
