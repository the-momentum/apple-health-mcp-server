from typing import Any, Hashable

from duckdb import DuckDBPyRelation

class DuckDBClient:
    def __init__(self):
        """tu dodac jakis config"""
        self.path = "appledata.parquet"

    @staticmethod
    def format_response(resp: DuckDBPyRelation) -> dict[Hashable, Any]:
        resp: dict[Hashable, Any] = resp.df().to_dict()
        resp = {k: v[0] for k, v in resp.items()}
        return resp
