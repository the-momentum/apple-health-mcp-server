from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Generator
from xml.etree import ElementTree as ET

import pandas as pd
from dateutil.relativedelta import relativedelta

from app.config import settings


class XMLExporter:
    def __init__(self):
        self.xml_path: Path = Path(settings.RAW_XML_PATH)
        self.chunk_size: int = settings.CHUNK_SIZE
        self.cutoff_date: datetime | None = None
        if settings.IMPORT_LOOKBACK_MONTHS is not None:
            self.cutoff_date = datetime.now(timezone.utc) - relativedelta(
                months=settings.IMPORT_LOOKBACK_MONTHS,
            )

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

    @staticmethod
    def parse_apple_date(value: str) -> datetime:
        """
        Parses Apple Health's fixed date format ("YYYY-MM-DD HH:MM:SS +HHMM")
        via direct string slicing instead of strptime, which is ~3.5x faster
        at the scale of millions of records in an Apple Health export.
        """
        sign = -1 if value[20] == "-" else 1
        return datetime(
            int(value[0:4]), int(value[5:7]), int(value[8:10]),
            int(value[11:13]), int(value[14:16]), int(value[17:19]),
            tzinfo=timezone(sign * timedelta(hours=int(value[21:23]), minutes=int(value[23:25]))),
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
                document[field] = self.parse_apple_date(document[field])

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
            for field in self.DEFAULT_STATS:
                try:
                    document[field] = float(document[field])
                except (TypeError, ValueError):
                    document[field] = 0.0

        return document

    def is_within_lookback(self, start_date: datetime) -> bool:
        """Returns False if IMPORT_LOOKBACK_MONTHS is set and start_date predates the cutoff."""
        return self.cutoff_date is None or start_date >= self.cutoff_date

    def parse_xml(self, source: Any = None) -> Generator[pd.DataFrame, Any, None]:
        """
        Parses the XML file and yields pandas dataframes of specified chunk_size.
        Extracts attributes from each Record element.

        `source` defaults to self.xml_path, but accepts any source ET.iterparse
        supports (e.g. a file-like object), so a caller can feed it an isolated
        byte range of the export for parallel import.
        """
        records: list[dict[str, Any]] = []
        workouts: list[dict[str, Any]] = []
        workout_stats: list[dict[str, Any]] = []
        pending_stats: list[dict[str, Any]] = []

        xml_source = source if source is not None else self.xml_path
        # Record's and WorkoutStatistics' own attributes are always complete
        # as soon as their opening tag is parsed, so "start" is safe for
        # them. They must be read there rather than deferred: every element
        # gets elem.clear()'d on its own "end" event below, and a
        # WorkoutStatistics child's "end" fires (clearing its attrib to {})
        # before its parent Workout's "end" is ever reached, so reading it
        # via "for stat in elem" at the Workout's "end" would only ever see
        # emptied-out children. Buffer stats per-workout in pending_stats and
        # only commit them once the Workout's "end" tells us whether to keep it.
        for event, elem in ET.iterparse(xml_source, events=("start", "end")):
            if event == "start" and elem.tag == "Record":
                if len(records) >= self.chunk_size:
                    yield pd.DataFrame(records).reindex(columns=self.RECORD_COLUMNS)
                    records = []
                record: dict[str, Any] = elem.attrib.copy()

                # fill out empty cells if they exist and convert dates to datetime
                self.update_record("record", record)
                if self.is_within_lookback(record["startDate"]):
                    records.append(record)

            elif event == "start" and elem.tag == "WorkoutStatistics":
                statistic = elem.attrib.copy()
                self.update_record("stat", statistic)
                pending_stats.append(statistic)

            elif event == "end" and elem.tag == "Workout":
                if len(workouts) >= self.chunk_size:
                    yield pd.DataFrame(workouts).reindex(columns=self.WORKOUT_COLUMNS)
                    workouts = []
                workout: dict[str, Any] = elem.attrib.copy()
                self.update_record("workout", workout)
                keep_workout = self.is_within_lookback(workout["startDate"])

                if keep_workout:
                    workouts.append(workout)
                    workout_stats.extend(pending_stats)
                    if len(workout_stats) >= self.chunk_size:
                        yield pd.DataFrame(workout_stats).reindex(
                            columns=self.WORKOUT_STATS_COLUMNS,
                        )
                        workout_stats = []
                pending_stats = []

            if event == "end":
                elem.clear()

        # yield remaining records
        yield pd.DataFrame(records).reindex(columns=self.RECORD_COLUMNS)
        yield pd.DataFrame(workouts).reindex(columns=self.WORKOUT_COLUMNS)
        yield pd.DataFrame(workout_stats).reindex(columns=self.WORKOUT_STATS_COLUMNS)
