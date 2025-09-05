from datetime import datetime
import json
from json import JSONDecodeError
from pathlib import Path
from sys import stderr
from typing import Any, Generator
from xml.etree import ElementTree as ET

import chdb
from pandas import DataFrame

from app.config import settings


class CHIndexer:
    def __init__(self):
        self.session = chdb.session.Session("applehealth.chdb")
        self.db_name: str = settings.CH_DB_NAME
        self.table_name: str = settings.CH_TABLE_NAME
        self.path: Path = Path(settings.RAW_XML_PATH)
        self.chunk_size: int = settings.CHUNK_SIZE
        self.session.query(f"CREATE DATABASE IF NOT EXISTS {self.db_name}")

    DATE_FIELDS: tuple[str] = ("startDate", "endDate", "creationDate")
    DEFAULT_VALUES: dict[str, str] = {
        "unit": "unknown",
        "sourceVersion": "unknown",
        "device": "unknown",
        "value": "unknown",
    }
    COLUMN_NAMES: tuple[str, ...] = (
        "type",
        "sourceVersion",
        "sourceName",
        "device",
        "startDate",
        "endDate",
        "creationDate",
        "unit",
        "value",
        "numerical",
    )

    def __del__(self):
        self.session.close()
        self.session.cleanup()

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

    def parse_xml(self) -> Generator[DataFrame, Any, None]:
        """
        Parses the XML file and yields pandas dataframes of specified chunk_size.
        Extracts attributes from each Record element.
        :param path: path to XML file
        :param chunk_size: Size of yielded dataframe
        """
        records: list[dict[str, Any]] = []


        def update_record(document: dict[str, Any]) -> dict[str, Any]:
            """
            Updates records to fill out columns without specified data:
            There are 9 columns that need to be filled out, and there are 4 columns
            that are optional and aren't filled out in every record
            """
            for field in self.DATE_FIELDS:
                document[field] = datetime.strptime(
                    document[field], '%Y-%m-%d %H:%M:%S %z'
                )

            if len(document) != 9:
                document.update(
                    {k: v for k, v in self.DEFAULT_VALUES.items() if k not in document}
                )

            # making sure there are value field with text values
            # and numerical which always contain numbers for the sake
            # of aggregation in clickhouse
            try:
                val = float(document['value'])
                document['numerical'] = val
            except (TypeError, ValueError):
                document['numerical'] = 0.0

            return document

        for event, elem in ET.iterparse(self.path, events=("start",)):
            if elem.tag == "Record" and event == "start":
                if len(records) >= self.chunk_size:
                    yield DataFrame(records).reindex(columns=self.COLUMN_NAMES)
                    records = []
                record: dict[str, Any] = elem.attrib.copy()

                # fill out empty cells if they exist and convert dates to datetime
                update_record(record)
                records.append(record)
            elem.clear()

        # yield remaining records
        yield DataFrame(records).reindex(columns=self.COLUMN_NAMES)

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