from datetime import datetime
from pathlib import Path
from typing import Any, Generator
from xml.etree import ElementTree as ET

import polars as pl
from pandas import DataFrame

from app.config import settings


class XMLExporter:
    def __init__(self):
        self.xml_path: Path = Path(settings.RAW_XML_PATH)
        self.chunk_size: int = settings.CHUNK_SIZE

    DATE_FIELDS: tuple[str, ...] = ("startDate", "endDate", "creationDate")
    DEFAULT_VALUES: dict[str, str] = {
        "unit": "",
        "sourceVersion": "",
        "device": "",
        "value": "",
    }
    DEFAULT_STATS: dict[str, float] = {
        "sum": 0.0,
        "average": 0.0,
        "maximum": 0.0,
        "minimum": 0.0,
    }
    RECORD_COLUMNS: tuple[str, ...] = (
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
    WORKOUT_COLUMNS: tuple[str, ...] = (
        "type",
        "duration",
        "durationUnit",
        "sourceName",
        "startDate",
        "endDate",
        "creationDate",
    )
    WORKOUT_STATS_COLUMNS: tuple[str, ...] = (
        "type",
        "startDate",
        "endDate",
        "sum",
        "average",
        "maximum",
        "minimum",
        "unit",
    )

    def update_record(self, kind: str, document: dict[str, Any]) -> dict[str, Any]:
        """
        Updates records to fill out columns without specified data:
        There are 9 columns that need to be filled out, and there are 4 columns
        that are optional and aren't filled out in every record
        Additionally a textValue field is added for querying text values
        """
        for field in self.DATE_FIELDS:
            if field in document:
                document[field] = datetime.strptime(document[field], "%Y-%m-%d %H:%M:%S %z")

        if kind == "record":
            if len(document) != 9:
                document.update({k: v for k, v in self.DEFAULT_VALUES.items() if k not in document})

            document["textValue"] = document["value"]

            try:
                document["value"] = float(document["value"])
            except (TypeError, ValueError):
                document["value"] = 0.0

        elif kind == "workout":
            document["type"] = document.pop("workoutActivityType")

            try:
                document["duration"] = float(document["duration"])
            except (TypeError, ValueError):
                document["duration"] = 0.0

        elif kind == "stat":
            document.update({k: v for k, v in self.DEFAULT_STATS.items() if k not in document})

        return document

    def parse_xml(self) -> Generator[pl.DataFrame, Any, None]:
        """
        Parses the XML file and yields pandas dataframes of specified chunk_size.
        Extracts attributes from each Record element.
        """
        records: list[dict[str, Any]] = []
        workouts: list[dict[str, Any]] = []
        workout_stats: list[dict[str, Any]] = []

        for event, elem in ET.iterparse(self.xml_path, events=("start",)):
            if elem.tag == "Record" and event == "start":
                if len(records) >= self.chunk_size:
                    # yield pl.DataFrame(records)
                    yield DataFrame(records).reindex(columns=self.RECORD_COLUMNS)
                    records = []
                record: dict[str, Any] = elem.attrib.copy()

                # fill out empty cells if they exist and convert dates to datetime
                self.update_record("record", record)
                records.append(record)

            elif elem.tag == "Workout" and event == "start":
                if len(workouts) >= self.chunk_size:
                    yield DataFrame(workouts).reindex(columns=self.WORKOUT_COLUMNS)
                    workouts = []
                workout: dict[str, Any] = elem.attrib.copy()

                for stat in elem:
                    if stat.tag != "WorkoutStatistics":
                        continue
                    statistic = stat.attrib.copy()
                    self.update_record("stat", statistic)
                    workout_stats.append(statistic)
                    if len(workout_stats) >= self.chunk_size:
                        yield DataFrame(workout_stats).reindex(columns=self.WORKOUT_STATS_COLUMNS)
                        workout_stats = []

                self.update_record("workout", workout)
                workouts.append(workout)

            elem.clear()

        # yield remaining records
        # yield pl.DataFrame(records)
        yield DataFrame(records).reindex(columns=self.RECORD_COLUMNS)
        yield DataFrame(workouts).reindex(columns=self.WORKOUT_COLUMNS)
        yield DataFrame(workout_stats).reindex(columns=self.WORKOUT_STATS_COLUMNS)
