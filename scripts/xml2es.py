import xml.etree.ElementTree as ET
from typing import Any
from collections.abc import Generator
import sys
from datetime import datetime

from elasticsearch import NotFoundError, helpers

from app.services.es import ESClient


class ESIndexer:
    def __init__(self):
        self.es = ESClient()

    @staticmethod
    def convert_str2datetime(date_str: str) -> str:
        """Convert date strings to ISO 8601 datetime format."""
        try:
            # Parse string like "2022-04-29 05:49:44 -0400"
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S %z")
            return dt.isoformat()
        except Exception:
            return date_str  # fallback to original if parsing fails

    @staticmethod
    def convert_str2float(value_str: str) -> float:
        """Convert value string to numeric type (float)."""
        try:
            return float(value_str)
        except (ValueError, TypeError):
            return 0.0  # fallback to 0 if parsing fails

    def parse_xml(self) -> Generator[dict[str, Any], None, None]:
        """
        Parses the XML file and yields dictionaries for each document/item.
        Extracts attributes from each Record element.
        Converts date fields to ISO 8601 datetime strings and value to numeric type.
        """
        tree = ET.parse(self.es.xml_path)
        root = tree.getroot()
        for child in root:
            document: dict[str, Any] = child.attrib.copy()  # dictionary of attributes

            if "startDate" in document:
                document["startDate"] = self.convert_str2datetime(document["startDate"])
                document["dateComponents"] = document["startDate"]
            if "endDate" in document:
                document["endDate"] = self.convert_str2datetime(document["endDate"])

            if "value" in document:
                document["value"] = self.convert_str2float(document["value"])

            yield document

    def index_to_es(self, documents: list[dict[str, Any]]) -> None:
        """
        Bulk insert the documents into elasticsearch index.
        """
        actions = [{"_index": self.es.index, "_source": document} for document in documents]
        helpers.bulk(self.es.engine, actions)
        print(f"Indexed {len(actions)} documents into '{self.es.index}'")

    def delete_index(self) -> None:
        try:
            resp = self.es.engine.delete_by_query(
                index=self.es.index, body={"query": {"match_all": {}}}
            )
            print(f"Deleted {resp.get('deleted', 0)} documents from '{self.es.index}'")
        except NotFoundError:
            print(f"Index '{self.es.index}' does not exist. Nothing to delete.")

    def run(self, delete_all: bool = False) -> None:
        if delete_all:
            print(f"Deleting all documents from '{self.es.index}'...")
            self.delete_index()
            return

        print(f"Parsing XML from {self.es.xml_path}...")
        documents = list(self.parse_xml())
        print(f"Parsed {len(documents)} documents. Indexing to Elasticsearch...")
        self.index_to_es(documents)


if __name__ == "__main__":
    delete_all_flag = len(sys.argv) > 1 and sys.argv[1] == "--delete-all"
    indexer = ESIndexer()
    indexer.run(delete_all=delete_all_flag)
