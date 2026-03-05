from __future__ import annotations

import argparse
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from sql_agent.agent import SQLAgent
from sql_agent.config import Settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SQL Agent from CLI")
    parser.add_argument("question", help="Business question to ask the SQL Agent")
    args = parser.parse_args()

    settings = Settings.from_env()
    agent = SQLAgent(settings)
    result = agent.ask(args.question)

    print("\nQuestion:")
    print(result.question)
    print("\nGenerated SQL:")
    print(result.sql_query)
    print("\nRows returned:", len(result.dataframe))
    print("\nAI answer:")
    print(result.answer)


if __name__ == "__main__":
    main()
