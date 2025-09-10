import json
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any

import chdb

from app.config import settings


@dataclass
class CHClient:
    def __init__(self):
        self.ch_session = chdb.session.Session(settings.CH_DIRNAME)
        self.db_name: str = settings.CH_DB_NAME
        self.table_name: str = settings.CH_TABLE_NAME
        self.path: Path = Path(settings.RAW_XML_PATH)

    def __post_init__(self):
        if not self.path.exists():
            raise FileNotFoundError(f"XML file not found: {self.path}")
        self.ch_session.query(f"CREATE DATABASE IF NOT EXISTS {self.db_name}")

    def inquire(self, query: str) -> dict[str, Any]:
        """
        Makes an SQL query to the database
        :return: result of the query
        """
        # first call to json.loads() only returns a string, and the second one a dict
        response: str = json.dumps(str(self.ch_session.query(query, fmt="JSON")))
        try:
            return json.loads(json.loads(response))
        except JSONDecodeError as e:
            return {"error": str(e)}
