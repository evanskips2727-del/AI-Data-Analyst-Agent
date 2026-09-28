#!/usr/bin/env python
"""
Command-line interface to the agent - no server required.

Usage:
    python cli.py "Which counties have the largest gaps in reported service coverage?"

Or run with no arguments for an interactive loop.
"""
import sys

from app.agent import answer_question
from app.llm import DEMO_MODE


def _print_result(result):
    print(f"\nSQL:\n  {result.sql}")
    if result.error:
        print(f"\nError: {result.error}")
        return
    print(f"\nSummary:\n  {result.summary}")
    print(f"\nRows returned: {len(result.rows)}")
    for row in result.rows[:10]:
        print(f"  {row}")


def main():
    print(f"AI Data Analyst Agent CLI ({'DEMO_MODE' if DEMO_MODE else 'LLM_MODE'})")

    if len(sys.argv) > 1:
        _print_result(answer_question(" ".join(sys.argv[1:])))
        return

    print("Type a question, or 'exit' to quit.")
    while True:
        question = input("\n> ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if question:
            _print_result(answer_question(question))


if __name__ == "__main__":
    main()
