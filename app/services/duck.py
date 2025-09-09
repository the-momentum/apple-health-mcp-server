from typing import Any

from duckdb import DuckDBPyRelation


class DuckDBClient:
    def __init__(self):
        """tu dodac jakis config"""
        self.path = "appledata.parquet"

    @staticmethod
    def format_response(response: DuckDBPyRelation) -> list[dict[str, Any]]:
        return response.df().to_dict(orient="records")
        records = response.fetchall()
        return records
