import json
from json import JSONDecodeError
from pathlib import Path
from sys import stderr
from typing import Any

import chdb

from app.config import settings
from scripts.xml_exporter import XMLExporter

class CHIndexer(XMLExporter):
    def __init__(self):
        super().__init__()
        self.session = chdb.session.Session("applehealth.chdb")
        self.db_name: str = settings.CH_DB_NAME
        self.table_name: str = settings.CH_TABLE_NAME
        self.path: Path = Path(settings.RAW_XML_PATH)
        self.session.query(f"CREATE DATABASE IF NOT EXISTS {self.db_name}")


    def create_table(self) -> None:
        """
        Create a new table for exported xml health data
        """
        self.session.query(f"""
                   CREATE TABLE IF NOT EXISTS {self.db_name}.{self.table_name}
                   (
                       type String,
                       sourceVersion String,
                       sourceName String,
                       device String,
                       startDate DateTime,
                       endDate DateTime,
                       creationDate DateTime,
                       unit String,
                       value String,
                       numerical Float32
                   )
                       ENGINE = MergeTree
                       ORDER BY startDate
                        """)


    def index_data(self) -> bool:
        for docs in self.parse_xml():
            try:
                self.session.query(f"""
                           INSERT INTO {self.db_name}.{self.table_name}
                           SELECT *
                           FROM Python(docs)
                           """)
            except RuntimeError as e:
                print(f"Failed to insert {len(docs)} records")
                print(e, file=stderr)
                return False
        return True

    def inquire(self, query: str) -> dict[str, Any]:
        """
        Makes an SQL query to the database
        :return: result of the query
        """
        # first call to json.loads() only returns a string, and the second one a dict
        response: str = json.dumps(str(self.session.query(query, fmt='JSON')))
        try:
            return json.loads(json.loads(response))
        except JSONDecodeError as e:
            return {'error': str(e)}

    def run(self) -> bool:
        """
        Creates a new table in the database and populates it with data from the XML file provided
        """
        self.create_table()
        print(f"Created table {self.db_name}.{self.table_name}")
        result: bool = self.index_data()
        if result:
            print("Inserted data into chdb correctly")
            return True
        else:
            print("Error during data indexing")
            return False

if __name__ == "__main__":
    ch = CHIndexer()
    ch.run()