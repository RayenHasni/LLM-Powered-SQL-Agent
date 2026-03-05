# SQL Agent for BI Analysis

A SQL Agent project that converts natural language questions into SQL Server queries, executes them, and returns business-ready insights using Gemini.

## Project Highlights

- Multi-step AI pipeline that follows your notebook logic:
  - Extract table metadata
  - Generate T-SQL from business questions
  - Execute SQL on SQL Server
  - Summarize results in business language
- Improved prompts for more reliable SQL generation while preserving your original intent.
- Safe read-only SQL guardrails (SELECT-only policy).
- Streamlit interface with practical features:
  - Editable generated SQL before execution
  - Metadata-driven quick question suggestions (LLM-generated)
  - Quick chart builder (bar/line)
  - Query history with CSV export

## Folder Structure

```text
SQL Agent/
|-- app/
|   `-- streamlit_app.py
|-- scripts/
|   `-- run_cli.py
|-- src/
|   `-- sql_agent/
|       |-- __init__.py
|       |-- agent.py
|       |-- config.py
|       |-- db.py
|       `-- llm.py
|-- .env.example
|-- .gitignore
|-- pyproject.toml
|-- requirements.txt
|-- README.md
`-- SQL_Agents.ipynb
```

## Tech Stack

- Python
- Streamlit
- SQL Server + ODBC (`pypyodbc`)
- Gemini (`google-genai`)
- Pandas

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` into `.env` and set values:

```env
GEMINI_API_KEY="your_gemini_api_key_here"

DB_DRIVER="ODBC Driver 17 for SQL Server"
DB_SERVER="DESKTOP-xxxxxxx\\SQLEXPRESS"
DB_NAME="your_db"
DB_SCHEMA=dbo
DB_TABLE="your_table"

LLM_MODEL="your_model"
```

4. Ensure SQL Server and ODBC driver are installed and reachable.
5. The app explicitly loads `.env` at runtime, so it works even if terminal environment injection is disabled.

## Run

### Streamlit App

```bash
streamlit run app/streamlit_app.py
```

### CLI

```bash
python scripts/run_cli.py "Top 10 states by customer count"
```

## How It Works

1. `extract_table_metadata` reads schema details from `INFORMATION_SCHEMA.COLUMNS`.
2. Prompted Gemini model generates one T-SQL SELECT query.
3. SQL extraction is normalized from model output (supports plain SELECT and CTE-style responses).
4. SQL is validated with read-only safeguards and executed against SQL Server.
5. Result set is converted to DataFrame, visualized, and summarized into BI-friendly insights.

## Prompt Improvements

The SQL prompt was upgraded to be more deterministic and analyst-focused while keeping your original meaning:

- Keeps context of business question + available columns.
- Forces single-query output with SQL Server syntax.
- Preserves square-bracket naming style.
- Adds read-only constraints and explicit formatting rules.
- Adds question-generation prompt logic to produce practical quick suggestions from live table metadata.

## Security Notes

- Do not hardcode API keys in source code.
- Use environment variables (`GEMINI_API_KEY`).
- Current guardrail blocks non-SELECT operations.
- Frontend does not expose API key value.

## Future Enhancements

- Add unit tests for SQL extraction and prompt output.
- Add multi-table support with joins.
- Add role-based database credentials for deployment.

## License

This project is licensed under the [Apache License 2.0](LICENSE). You are free to use, modify, and share this project with proper attribution.
