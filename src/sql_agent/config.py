from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


def _load_env_file() -> None:
    root_env = Path(__file__).resolve().parents[2] / ".env"
    if root_env.exists():
        load_dotenv(dotenv_path=root_env, override=False)


@dataclass
class Settings:
    gemini_api_key: str = ""
    db_driver: str = "ODBC Driver 17 for SQL Server"
    db_server: str = "DESKTOP-BDE04OR\\SQLEXPRESS"
    db_name: str = "db_Churn"
    db_schema: str = "dbo"
    db_table: str = "prod_Churn"
    llm_model: str = "gemini-3-flash-preview"

    @classmethod
    def from_env(cls) -> "Settings":
        _load_env_file()
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            db_driver=os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
            db_server=os.getenv("DB_SERVER", "DESKTOP-BDE04OR\\SQLEXPRESS"),
            db_name=os.getenv("DB_NAME", "db_Churn"),
            db_schema=os.getenv("DB_SCHEMA", "dbo"),
            db_table=os.getenv("DB_TABLE", "prod_Churn"),
            llm_model=os.getenv("LLM_MODEL", "gemini-2.0-flash"),
        )

    @property
    def connection_string(self) -> str:
        return (
            f"Driver={{{self.db_driver}}};"
            f"Server={self.db_server};"
            f"Database={self.db_name};"
            "Trusted_Connection=yes;"
        )
