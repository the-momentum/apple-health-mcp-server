import os
import shutil
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import polars as pl

from app.config import settings
from app.services.duckdb_client import DuckDBClient
from scripts.xml_exporter import XMLExporter

RECORDS_SCHEMA = """
    CREATE TABLE IF NOT EXISTS records (
        type VARCHAR,
        sourceVersion VARCHAR,
        sourceName VARCHAR,
        device VARCHAR,
        startDate TIMESTAMP,
        endDate TIMESTAMP,
        creationDate TIMESTAMP,
        unit VARCHAR,
        value DOUBLE,
        textValue VARCHAR
    );
"""
WORKOUTS_SCHEMA = """
    CREATE TABLE IF NOT EXISTS workouts (
        type VARCHAR,
        duration DOUBLE,
        durationUnit VARCHAR,
        sourceName VARCHAR,
        startDate TIMESTAMP,
        endDate TIMESTAMP,
        creationDate TIMESTAMP
    )
"""
STATS_SCHEMA = """
    CREATE TABLE IF NOT EXISTS stats (
        type VARCHAR,
        startDate TIMESTAMP,
        endDate TIMESTAMP,
        sum DOUBLE,
        average DOUBLE,
        maximum DOUBLE,
        minimum DOUBLE,
        unit VARCHAR
    )
"""


def find_split_offsets(path: Path, n_splits: int) -> list[int]:
    """
    Returns byte offsets partitioning the export into up to n_splits ranges,
    each boundary aligned to the start of a top-level HealthData child element.

    Apple's export is pretty-printed with exactly one leading space for direct
    children of <HealthData> (Record/Workout/Correlation/...) and two-or-more
    for anything nested inside them (WorkoutStatistics, MetadataEntry, Records
    nested inside a Correlation, etc). A top-level element's own closing tag
    (e.g. " </Correlation>") is indented the same as its opening tag though,
    so splitting must also skip past those and land on an actual opening tag
    -- otherwise a worker can be left with an unmatched open tag.
    """
    size = path.stat().st_size
    if n_splits <= 1 or size == 0:
        return [0, size]

    offsets = {0, size}
    with path.open("rb") as f:
        for i in range(1, n_splits):
            target = size * i // n_splits
            f.seek(target)
            f.readline()  # discard the (possibly partial) line at the seek point
            while True:
                pos = f.tell()
                line = f.readline()
                if not line:
                    pos = size
                    break
                if (
                    line.startswith(b" <")
                    and not line.startswith(b"  <")
                    and not line.startswith(b" </")
                ):
                    break
            offsets.add(pos)
    return sorted(offsets)


class _BoundedXMLSection:
    """
    File-like view over [start, end) bytes of a larger XML file, padded with a
    synthetic <HealthData> root (only where the real one is missing, i.e. not
    at the true start/end of the file) so the slice is a well-formed document
    on its own and can be fed straight into ET.iterparse.
    """

    def __init__(self, path: Path, start: int, end: int, file_size: int):
        self._file = open(path, "rb")  # noqa: SIM115
        self._file.seek(start)
        self._remaining = end - start
        self._prefix = b"" if start == 0 else b"<HealthData>"
        self._suffix = b"" if end == file_size else b"</HealthData>"
        self._stage = 0  # 0=prefix, 1=body, 2=suffix, 3=done

    def read(self, size: int = -1) -> bytes:
        # Loops (rather than recursing/returning) past empty prefix/suffix
        # segments (first/last range), since returning b"" would otherwise
        # signal EOF to the parser before any real content has been read.
        while self._stage != 3:
            if self._stage == 0:
                self._stage = 1
                if self._prefix:
                    return self._prefix
                continue
            if self._stage == 1:
                want_all = size is None or size < 0
                to_read = self._remaining if want_all else min(size, self._remaining)
                data = self._file.read(to_read) if to_read > 0 else b""
                self._remaining -= len(data)
                if data:
                    return data
                self._file.close()
                self._stage = 2
                continue
            if self._stage == 2:
                self._stage = 3
                if self._suffix:
                    return self._suffix
                continue
        return b""

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()


def _parse_worker_range(args: tuple[str, int, int, int, str, int]) -> dict[str, Any]:
    """
    Runs in a worker process: parses one byte range of the export and writes
    each kept chunk straight to a uniquely-named Parquet file, so the main
    process only has to do one cheap bulk COPY per table at the end.
    """
    xml_path, start, end, worker_id, tmp_dir, file_size = args
    t0 = time.perf_counter()

    exporter = XMLExporter()
    section = _BoundedXMLSection(Path(xml_path), start, end, file_size)
    column_sets = {
        "records": set(exporter.RECORD_COLUMNS),
        "workouts": set(exporter.WORKOUT_COLUMNS),
        "stats": set(exporter.WORKOUT_STATS_COLUMNS),
    }
    kept = {"records": 0, "workouts": 0, "stats": 0}
    chunk_index = {"records": 0, "workouts": 0, "stats": 0}

    for docs in exporter.parse_xml(source=section):
        if docs.empty:
            continue
        cols = set(docs.columns)
        name = next((n for n, s in column_sets.items() if cols == s), None)
        if name is None:
            continue
        kept[name] += len(docs)
        out_path = Path(tmp_dir) / f"{name}_{worker_id}_{chunk_index[name]}.parquet"
        docs.to_parquet(out_path, compression="zstd", index=False)
        chunk_index[name] += 1

    return {
        "worker_id": worker_id,
        "kept_records": kept["records"],
        "kept_workouts": kept["workouts"],
        "kept_stats": kept["stats"],
        "seconds": time.perf_counter() - t0,
    }


class ParquetImporter(XMLExporter, DuckDBClient):
    def __init__(self):
        XMLExporter.__init__(self)
        DuckDBClient.__init__(self)

    chunk_files = []

    def export_xml(self) -> None:
        """
        Export xml data from Apple Health export file
        to a .duckdb database with path specified by user
        """
        con = duckdb.connect(str(self.path))
        con.sql(RECORDS_SCHEMA)
        con.sql(WORKOUTS_SCHEMA)
        con.sql(STATS_SCHEMA)

        docs_count = 0
        for i, docs in enumerate(self.parse_xml(), 1):
            cols = set(docs.columns)
            if cols == set(self.RECORD_COLUMNS):
                con.sql("""
                    INSERT INTO records SELECT * FROM docs;
                """)
            if cols == set(self.WORKOUT_COLUMNS):
                con.sql("""
                    INSERT INTO workouts SELECT * FROM docs;
                """)
            if cols == set(self.WORKOUT_STATS_COLUMNS):
                con.sql("""
                    INSERT INTO stats SELECT * FROM docs;
                """)
            print(f"processed {docs_count + len(docs)} docs")
            docs_count += len(docs)

    def export_xml_parallel(self, workers: int | None = None) -> None:
        """
        Same output as export_xml, but splits the XML across multiple worker
        processes (parsing is CPU-bound and single-threaded, so this is the
        only way to use more than one core). Each worker writes its kept
        records/workouts/stats straight to Parquet; this process only opens
        the DuckDB file once, at the end, to bulk-load all of it.
        """
        workers = workers or settings.IMPORT_WORKERS or os.cpu_count() or 1
        offsets = find_split_offsets(self.xml_path, workers)
        file_size = offsets[-1]
        ranges = [(s, e) for s, e in zip(offsets, offsets[1:]) if e > s]

        tmp_dir = Path(f"_duckdb_import_tmp_{os.getpid()}")
        tmp_dir.mkdir(exist_ok=True)
        print(f"Splitting {self.xml_path} into {len(ranges)} range(s), {len(ranges)} worker(s)")

        try:
            worker_args = [
                (str(self.xml_path), start, end, i, str(tmp_dir), file_size)
                for i, (start, end) in enumerate(ranges)
            ]
            with ProcessPoolExecutor(max_workers=len(ranges)) as pool:
                for result in pool.map(_parse_worker_range, worker_args):
                    print(
                        f"[worker {result['worker_id']}] kept {result['kept_records']} records, "
                        f"{result['kept_workouts']} workouts, {result['kept_stats']} stats "
                        f"in {result['seconds']:.1f}s",
                    )

            con = duckdb.connect(str(self.path))
            con.sql(RECORDS_SCHEMA)
            con.sql(WORKOUTS_SCHEMA)
            con.sql(STATS_SCHEMA)

            for table in ("records", "workouts", "stats"):
                if list(tmp_dir.glob(f"{table}_*.parquet")):
                    con.sql(f"""
                        INSERT INTO {table}
                        SELECT * FROM read_parquet('{tmp_dir}/{table}_*.parquet')
                    """)
            con.close()
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def write_to_file(self, index: int, df: pl.DataFrame) -> None:
        chunk_file: str | Path = ""
        try:
            # check for columns specific for each table
            if "workoutActivityType" in df.columns:
                chunk_file = Path(f"workouts.chunk_{index}.parquet")
            elif "type" in df.columns:
                chunk_file = Path(f"records.chunk_{index}.parquet")
            elif "sum" in df.columns:
                chunk_file = Path(f"workout_stats.chunk_{index}.parquet")
            print(f"processed {index * self.chunk_size} docs")
            df.write_parquet(chunk_file, compression="zstd", compression_level=1)
            self.chunk_files.append(chunk_file)

        except Exception:
            for file in self.chunk_files:
                os.remove(file)
            raise RuntimeError(f"Failed to write chunk file to disk: {chunk_file}")

    def export_xml_parquet(self) -> None:
        """
        Deprecated method for exporting to multiple parquet files
        corresponding to each table in the duckdb database
        use export_xml instead
        """

        for i, docs in enumerate(self.parse_xml(), 1):
            df: pl.DataFrame = pl.DataFrame(docs)
            self.write_to_file(i, df)

        record_chunk_dfs: list[pd.DataFrame] = []
        workout_chunk_dfs: list[pd.DataFrame] = []
        stat_chunk_dfs: list[pd.DataFrame] = []

        for chunk_file in self.chunk_files:
            df = pl.read_parquet(chunk_file)
            cols = set(df.columns)
            if cols == set(self.RECORD_COLUMNS):
                df = df.select(self.RECORD_COLUMNS)
                record_chunk_dfs.append(df)
            elif cols == set(self.WORKOUT_COLUMNS):
                df = df.select(self.WORKOUT_COLUMNS)
                workout_chunk_dfs.append(df)
            elif cols == set(self.WORKOUT_STATS_COLUMNS):
                df = df.select(self.WORKOUT_STATS_COLUMNS)
                stat_chunk_dfs.append(df)

        record_df = None
        workout_df = None
        stat_df = None

        try:
            if record_chunk_dfs:
                record_df = pl.concat(record_chunk_dfs)
            if workout_chunk_dfs:
                workout_df = pl.concat(workout_chunk_dfs)
            if stat_chunk_dfs:
                stat_df = pl.concat(stat_chunk_dfs)
        except Exception as e:
            for f in self.chunk_files:
                os.remove(f)
            raise RuntimeError(f"Failed to concatenate dataframes: {str(e)}")
        try:
            if record_df is not None:
                record_df.write_parquet(f"{self.path / 'records.parquet'}", compression="zstd")
            if workout_df is not None:
                workout_df.write_parquet(f"{self.path / 'workouts.parquet'}", compression="zstd")
            if stat_df is not None:
                stat_df.write_parquet(f"{self.path / 'stats.parquet'}", compression="zstd")
        except Exception as e:
            for f in self.chunk_files:
                os.remove(f)
            raise RuntimeError(f"Failed to write to path {self.path}: {str(e)}")

        for f in self.chunk_files:
            os.remove(f)


if __name__ == "__main__":
    importer = ParquetImporter()
    importer.export_xml_parallel()
