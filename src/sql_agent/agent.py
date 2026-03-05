from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd

from . import db
from .config import Settings
from .llm import (
    build_answer_prompt,
    build_quick_questions_prompt,
    build_sql_prompt,
    create_client,
    generate_answer,
    generate_quick_questions,
    generate_sql_query,
)


@dataclass
class SQLAgentResult:
    question: str
    sql_query: str
    dataframe: pd.DataFrame
    answer: str


class SQLAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = create_client(settings.gemini_api_key)

    def get_metadata(self) -> dict:
        with db.connect_db(self.settings.connection_string) as connection:
            return db.extract_table_metadata(
                connection=connection,
                schema_name=self.settings.db_schema,
                table_name=self.settings.db_table,
            )

    def generate_sql(self, question: str, metadata: dict) -> str:
        prompt = build_sql_prompt(
            question=question,
            table_name=self.settings.db_table,
            schema_name=self.settings.db_schema,
            column_metadata=metadata,
        )
        return generate_sql_query(self.client, self.settings.llm_model, prompt)

    def run_sql(self, sql_query: str) -> pd.DataFrame:
        with db.connect_db(self.settings.connection_string) as connection:
            return db.execute_query(connection=connection, sql_query=sql_query)

    def answer_from_df(self, question: str, dataframe: pd.DataFrame) -> str:
        prompt = build_answer_prompt(question, dataframe.to_json(orient="records"))
        return generate_answer(self.client, self.settings.llm_model, prompt)

    def suggest_quick_questions(self, metadata: dict, limit: int = 4) -> List[str]:
        prompt = build_quick_questions_prompt(
            table_name=self.settings.db_table,
            schema_name=self.settings.db_schema,
            column_metadata=metadata,
        )
        questions = generate_quick_questions(self.client, self.settings.llm_model, prompt)
        return questions[:limit]

    def ask(self, question: str) -> SQLAgentResult:
        metadata = self.get_metadata()
        sql_query = self.generate_sql(question=question, metadata=metadata)
        dataframe = self.run_sql(sql_query=sql_query)
        answer = self.answer_from_df(question=question, dataframe=dataframe)
        return SQLAgentResult(
            question=question,
            sql_query=sql_query,
            dataframe=dataframe,
            answer=answer,
        )
