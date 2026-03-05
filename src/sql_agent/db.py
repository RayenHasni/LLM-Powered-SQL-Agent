from __future__ import annotations

from typing import Dict, List

import pandas as pd
import pypyodbc


def connect_db(connection_string: str):
    return pypyodbc.connect(connection_string)


def extract_table_metadata(connection, schema_name: str, table_name: str) -> Dict[str, str]:
    query = """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """

    cursor = connection.cursor()
    cursor.execute(query, [schema_name, table_name])
    columns = cursor.fetchall()
    return {f"[{col[0]}]": col[1] for col in columns}


def list_tables(connection) -> List[str]:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
    )
    rows = cursor.fetchall()
    return [f"{row[0]}.{row[1]}" for row in rows]


def execute_query(connection, sql_query: str) -> pd.DataFrame:
    cursor = connection.cursor()
    cursor.execute(sql_query)

    if cursor.description is None:
        return pd.DataFrame()

    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    return pd.DataFrame(rows, columns=columns)
