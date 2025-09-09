from dataclasses import dataclass
from typing import Any

from duckdb import DuckDBPyRelation

from app.config import settings


@dataclass
class DuckDBClient:
    def __init__(self):
        self.parquetpath = f"{settings.DUCKDB_FILENAME}.parquet"

    def __post_init__(self):
        if not self.path.exists():
            raise FileNotFoundError(f"XML file not found: {self.path}")

    @staticmethod
    def format_response(response: DuckDBPyRelation) -> list[dict[str, Any]]:
        return response.df().to_dict(orient="records")
