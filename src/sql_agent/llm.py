from __future__ import annotations

import re
from typing import Dict, List

from google import genai


FORBIDDEN_SQL_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "MERGE",
    "GRANT",
    "REVOKE",
    "EXEC",
    "EXECUTE",
}


def create_client(api_key: str):
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing. Please set it in environment variables.")
    return genai.Client(api_key=api_key)


def extract_sql_from_response(text: str) -> str:
    cleaned = re.sub(r"```sql\s*", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned)
    cleaned = cleaned.strip()

    # Prefer explicit SELECT query ending with ';'.
    match = re.search(r"\bSELECT\s+.*?;", cleaned, flags=re.IGNORECASE | re.DOTALL)
    # Fall back to CTE query style: WITH ... SELECT ... ;
    if not match:
        match = re.search(r"\bWITH\b.*?\bSELECT\b.*?;", cleaned, flags=re.IGNORECASE | re.DOTALL)
    # Final fall back: no semicolon returned by model.
    if not match:
        match = re.search(r"\b(SELECT|WITH)\b[\s\S]*$", cleaned, flags=re.IGNORECASE)
    if not match:
        raise ValueError(
            "No valid SELECT SQL query was found in model response. "
            "Try rephrasing the question with explicit table intent."
        )

    sql = match.group(0).strip()
    if not sql.endswith(";"):
        sql += ";"

    sql_upper = sql.upper()
    if any(keyword in sql_upper for keyword in FORBIDDEN_SQL_KEYWORDS):
        raise ValueError("Unsafe SQL detected. Only read-only SELECT queries are allowed.")

    return sql


def build_sql_prompt(question: str, table_name: str, schema_name: str, column_metadata: Dict[str, str]) -> str:
    column_lines = "\\n".join([f"- {col}: {dtype}" for col, dtype in column_metadata.items()])
    full_table_name = f"{schema_name}.[{table_name}]"

    return f"""You are a senior SQL Server analyst.
Convert the business question into one accurate T-SQL SELECT query.

Business question:
{question}

Database context:
- Table: {full_table_name}
- Available columns and types:
{column_lines}

Rules:
1. Return exactly one SQL query and nothing else.
2. Use only provided columns and SQL Server syntax.
3. Keep square brackets for column and table names.
4. Use filters, grouping, and ordering only when relevant to the question.
5. Add TOP when the question asks for top/limit style outputs.
6. End the query with a semicolon.
7. Do not use INSERT, UPDATE, DELETE, DROP, ALTER, or other write operations.
"""


def generate_sql_query(client, model: str, prompt: str) -> str:
    response = client.models.generate_content(model=model, contents=prompt)
    return extract_sql_from_response(response.text)


def build_answer_prompt(question: str, results_json: str) -> str:
    return f"""You are a BI analyst writing concise business insights.
Answer the original question using only the SQL result rows below.

Question:
{question}

SQL result rows (JSON):
{results_json}

Response style:
- 2 to 5 short bullet points.
- Mention the key numbers or rankings directly.
- If results are empty, state that clearly.
- Do not invent data beyond the provided rows.
"""


def build_quick_questions_prompt(table_name: str, schema_name: str, column_metadata: Dict[str, str]) -> str:
    column_lines = "\n".join([f"- {col}: {dtype}" for col, dtype in column_metadata.items()])
    full_table_name = f"{schema_name}.[{table_name}]"

    return f"""You are a BI analytics assistant.
Generate 4 short and simple business questions a data analyst can ask about one SQL table.

Table context:
- Table: {full_table_name}
- Columns and data types:
{column_lines}

Rules:
1. Return exactly 4 lines.
2. Each line is one question ending with '?'.
3. Keep each question short and practical.
4. Questions must be answerable with this table only.
5. Do not include numbering, bullets, or any extra text.
"""


def extract_quick_questions(text: str, limit: int = 4) -> List[str]:
    cleaned = re.sub(r"```[\s\S]*?```", "", text).strip()
    lines = [line.strip(" -*\t") for line in cleaned.splitlines() if line.strip()]

    questions: List[str] = []
    for line in lines:
        candidate = re.sub(r"^\d+[\.)]\s*", "", line).strip()
        if not candidate:
            continue
        if not candidate.endswith("?"):
            candidate = f"{candidate.rstrip('.')}?"
        if 12 <= len(candidate) <= 140:
            questions.append(candidate)
        if len(questions) >= limit:
            break

    return questions


def generate_answer(client, model: str, prompt: str) -> str:
    response = client.models.generate_content(model=model, contents=prompt)
    return response.text.strip()


def generate_quick_questions(client, model: str, prompt: str) -> List[str]:
    response = client.models.generate_content(model=model, contents=prompt)
    return extract_quick_questions(response.text)
