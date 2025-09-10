from dataclasses import dataclass
from pathlib import Path
from typing import Any

from duckdb import DuckDBPyRelation

from app.config import settings


@dataclass
class DuckDBClient:
    def __init__(self):
        self.parquetpath: Path = Path(f"{settings.DUCKDB_FILENAME}.parquet")

    def __post_init__(self):
        if not self.parquetpath.exists():
            raise FileNotFoundError(f"Parquet file not found: {self.parquetpath}")

    @staticmethod
    def format_response(response: DuckDBPyRelation) -> list[dict[str, Any]]:
        return response.df().to_dict(orient="records")
