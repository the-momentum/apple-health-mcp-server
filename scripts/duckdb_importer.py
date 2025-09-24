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
        try:
            if "workoutActivityType" in df.columns:
                chunk_file: Path = Path(f"workouts.chunk_{index}.parquet")
                print(f"processed {index * self.chunk_size} docs")
                df.write_parquet(chunk_file, compression="zstd", compression_level=1)
                self.chunk_files.append(chunk_file)
            elif "type" in df.columns:
                chunk_file: Path = Path(f"records.chunk_{index}.parquet")
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

    def exportxml(self) -> None:
        for i, docs in enumerate(self.parse_xml(), 1):
            df: pl.DataFrame = pl.DataFrame(docs)
            self.write_to_file(i, df)

        record_chunk_dfs: list[pl.DataFrame] = []
        workout_chunk_dfs: list[pl.DataFrame] = []
        stat_chunk_dfs: list[pl.DataFrame] = []
        # reference_columns: list[str] = []

        for chunk_file in self.chunk_files:
            df = pl.read_parquet(chunk_file)
            if "value" in df.columns:
                df = df.select(self.RECORD_COLUMNS)
                record_chunk_dfs.append(df)
            elif "device" in df.columns:
                df = df.select(self.WORKOUT_COLUMNS)
                workout_chunk_dfs.append(df)
            elif "sum" in df.columns:
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

    def export_to_multiple(self):
        con = duckdb.connect("shitass.duckdb")
        for i, docs in enumerate(self.parse_xml(), 1):
            tables = docs.partition_by("type", as_dict=True)
            for key, table in tables.items():
                pddf = table.to_pandas()
                con.execute(f"""
                    CREATE TABLE IF NOT EXISTS {key[0]}
                    AS SELECT * FROM pddf
                """)
                # print(duckdb.sql(f"select * from pddf").fetchall())
            print(f"processed {i * self.chunk_size} docs")


if __name__ == "__main__":
    importer = ParquetImporter()
    importer.exportxml()
