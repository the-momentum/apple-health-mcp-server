import os

import polars as pl

from xml_exporter import XMLExporter


class ParquetImporter(XMLExporter):
    def __init__(self):
        XMLExporter.__init__(self)

    def exportxml(self):
        chunkfiles = []
        for i, docs in enumerate(self.parse_xml()):
            df = pl.DataFrame(docs)
            chunk_file = f"data.chunk_{i}.parquet"
            print(f"processed {(i + 1) * 200000} docs")
            df.write_parquet(chunk_file, compression="zstd", compression_level=1)
            chunkfiles.append(chunk_file)
            print(f"written {(i + 1) * 200000} docs")

        chunk_dfs = []
        reference_columns = None

        for chunk_file in chunkfiles:
            df = pl.read_parquet(chunk_file)

            # Set reference from first chunk
            if reference_columns is None:
                reference_columns = df.columns

            # Reorder columns to match reference
            df = df.select(reference_columns)
            chunk_dfs.append(df)

        combined_df = pl.concat(chunk_dfs)
        combined_df.write_parquet("appledata.parquet", compression="zstd")

        for f in chunkfiles:
            os.remove(f)
