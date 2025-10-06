import os
from pathlib import Path

import duckdb
import polars as pl

from app.services.duckdb_client import DuckDBClient
from scripts.xml_exporter import XMLExporter


class ParquetImporter(XMLExporter, DuckDBClient):
    def __init__(self):
        XMLExporter.__init__(self)
        DuckDBClient.__init__(self)

    chunk_files = []

    def write_to_file(self, index: int, df: pl.DataFrame) -> None:
        chunk_file: Path | None = None
        try:
            # TODO: clean this up
            if "workoutActivityType" in df.columns:
                chunk_file = Path(f"workouts.chunk_{index}.parquet")
                print(f"processed {index * self.chunk_size} docs")
                df.write_parquet(chunk_file, compression="zstd", compression_level=1)
                self.chunk_files.append(chunk_file)
            elif "type" in df.columns:
                chunk_file = Path(f"records.chunk_{index}.parquet")
                print(f"processed {index * self.chunk_size} docs")
                df.write_parquet(chunk_file, compression="zstd", compression_level=1)
                self.chunk_files.append(chunk_file)
            elif "sum" in df.columns:
                chunk_file = Path(f"workout_stats.chunk_{index}.parquet")
                print(f"processed {index * self.chunk_size} docs")
                df.write_parquet(chunk_file, compression="zstd", compression_level=1)
                self.chunk_files.append(chunk_file)
            else:
                for chunk_file in self.chunk_files:
                    os.remove(chunk_file)
                raise RuntimeError("Missing required fields in export file")
        except Exception:
            for file in self.chunk_files:
                os.remove(file)
            raise RuntimeError(f"Failed to write chunk file to disk: {chunk_file}")

    def export_xml(self) -> None:
        for i, docs in enumerate(self.parse_xml(), 1):
            df: pl.DataFrame = pl.DataFrame(docs)
            self.write_to_file(i, df)

        record_chunk_dfs: list[pl.DataFrame] = []
        workout_chunk_dfs: list[pl.DataFrame] = []
        stat_chunk_dfs: list[pl.DataFrame] = []
        # reference_columns: list[str] = []

        for chunk_file in self.chunk_files:
            df = pl.read_parquet(chunk_file)
            # print(df)
            # print(df.columns)
            cols = set(df.columns)
            # print(cols == set(self.RECORD_COLUMNS))
            # print(cols == set(self.WORKOUT_COLUMNS))
            # print(cols == set(self.WORKOUT_STATS_COLUMNS))
            if cols == set(self.RECORD_COLUMNS):
                print("record chunk dfs")
                df = df.select(self.RECORD_COLUMNS)
                record_chunk_dfs.append(df)
            elif cols == set(self.WORKOUT_COLUMNS):
                print("wk chunk dfs")
                df = df.select(self.WORKOUT_COLUMNS)
                workout_chunk_dfs.append(df)
            elif cols == set(self.WORKOUT_STATS_COLUMNS):
                print("stat chunk dfs")
                df = df.select(self.WORKOUT_STATS_COLUMNS)
                stat_chunk_dfs.append(df)

        record_df = None
        workout_df = None
        stat_df = None
        print("here")
        print(record_chunk_dfs, workout_chunk_dfs, stat_chunk_dfs)

        try:
            if record_chunk_dfs:
                record_df = pl.concat(record_chunk_dfs)
                # print(record_df)
            if workout_chunk_dfs:
                workout_df = pl.concat(workout_chunk_dfs)
                # print(workout_df)
            if stat_chunk_dfs:
                stat_df = pl.concat(stat_chunk_dfs)
                # print(stat_df)
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

    def export_to_multiple(self) -> None:
        con = duckdb.connect("healthdata.duckdb")
        con.sql("""
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
        """)
        con.sql("""
            CREATE TABLE IF NOT EXISTS workouts (
                type VARCHAR,
                duration DOUBLE,
                durationUnit VARCHAR,
                sourceName VARCHAR,
                startDate TIMESTAMP,
                endDate TIMESTAMP,
                creationDate TIMESTAMP
            )
        """)
        con.sql("""
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
        """)

        docs_count = 0
        for i, docs in enumerate(self.parse_xml(), 1):
            # tables = docs.partition_by("type", as_dict=True)
            cols = set(docs.columns)
            if cols == set(self.RECORD_COLUMNS):
                print("record chunk dfs")
                con.sql("""
                    INSERT INTO records SELECT * FROM docs;
                """)
            if cols == set(self.WORKOUT_COLUMNS):
                print("wk chunk dfs")
                con.sql("""
                    INSERT INTO workouts SELECT * FROM docs;
                """)
            if cols == set(self.WORKOUT_STATS_COLUMNS):
                print("stat chunk dfs")
                con.sql("""
                    INSERT INTO stats SELECT * FROM docs;
                """)
            print(f"processed {docs_count + len(docs)} docs")
            docs_count += len(docs)


if __name__ == "__main__":
    importer = ParquetImporter()
    # importer.export_xml()
    importer.export_to_multiple()
