import os
from pathlib import Path

import polars as pl

from app.services.duckdb_client import DuckDBClient
from scripts.xml_exporter import XMLExporter


class ParquetImporter(XMLExporter, DuckDBClient):
    def __init__(self):
        XMLExporter.__init__(self)
        DuckDBClient.__init__(self)

    def exportxml(self):
        chunkfiles = []
        for i, docs in enumerate(self.parse_xml(), 1):
            df: pl.DataFrame = pl.DataFrame(docs)
            chunk_file: Path = Path(f"data.chunk_{i}.parquet")
            print(f"processed {i * self.chunk_size} docs")
            df.write_parquet(chunk_file, compression="zstd", compression_level=1)
            chunkfiles.append(chunk_file)
            print(f"written {i * self.chunk_size} docs")

        chunk_dfs: list[pl.DataFrame] = []
        reference_columns: list[str] = []

        for chunk_file in chunkfiles:
            df = pl.read_parquet(chunk_file)

            if not reference_columns:
                reference_columns = df.columns

            df = df.select(reference_columns)
            chunk_dfs.append(df)

        combined_df = pl.concat(chunk_dfs)
        combined_df.write_parquet(f"{self.parquetpath}", compression="zstd")

        for f in chunkfiles:
            os.remove(f)


if __name__ == "__main__":
    importer = ParquetImporter()
    importer.exportxml()
