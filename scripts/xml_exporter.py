from datetime import datetime
from pathlib import Path
from typing import Any, Generator
from xml.etree import ElementTree as ET

from pandas import DataFrame

from app.config import settings


class XMLExporter:
    def __init__(self):
        self.xml_path: Path = Path(settings.RAW_XML_PATH)
        self.chunk_size: int = settings.CHUNK_SIZE

    DATE_FIELDS: tuple[str, ...] = ("startDate", "endDate", "creationDate")
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
        "textValue",
    )

    def update_record(self, document: dict[str, Any]) -> dict[str, Any]:
        """
        Updates records to fill out columns without specified data:
        There are 9 columns that need to be filled out, and there are 4 columns
        that are optional and aren't filled out in every record
        Additionally a textValue field is added for querying text values
        """
        for field in self.DATE_FIELDS:
            document[field] = datetime.strptime(document[field], "%Y-%m-%d %H:%M:%S %z")

        if len(document) != 9:
            document.update({k: v for k, v in self.DEFAULT_VALUES.items() if k not in document})

        document["textValue"] = document["value"]

        try:
            document["value"] = float(document["value"])
        except (TypeError, ValueError):
            document["value"] = 0.0

        return document

    def parse_xml(self) -> Generator[DataFrame, Any, None]:
        """
        Parses the XML file and yields pandas dataframes of specified chunk_size.
        Extracts attributes from each Record element.
        """
        records: list[dict[str, Any]] = []

        for event, elem in ET.iterparse(self.xml_path, events=("start",)):
            if elem.tag == "Record" and event == "start":
                if len(records) >= self.chunk_size:
                    yield DataFrame(records).reindex(columns=self.COLUMN_NAMES)
                    records = []
                record: dict[str, Any] = elem.attrib.copy()

                # fill out empty cells if they exist and convert dates to datetime
                self.update_record(record)
                records.append(record)
            elem.clear()

        # yield remaining records
        yield DataFrame(records).reindex(columns=self.COLUMN_NAMES)
