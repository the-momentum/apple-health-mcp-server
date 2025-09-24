from sys import stderr

from app.services.ch_client import CHClient
from scripts.xml_exporter import XMLExporter


class CHIndexer(XMLExporter, CHClient):
    def __init__(self):
        XMLExporter.__init__(self)
        CHClient.__init__(self)
        self.ch_session.query(f"CREATE DATABASE IF NOT EXISTS {self.db_name}")

    def create_table(self) -> None:
        """
        Create a new table for exported xml health data
        """
        self.ch_session.query(f"""
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
                       value Float32,
                       textValue String,
                   )
                       ENGINE = MergeTree
                       ORDER BY startDate
                        """)

    def index_data(self) -> bool:
        for docs in self.parse_xml():
            try:
                self.ch_session.query(f"""
                           INSERT INTO {self.db_name}.{self.table_name}
                           SELECT *
                           FROM Python(docs)
                           """)
            except RuntimeError as e:
                print(f"Failed to insert {len(docs)} records")
                print(e, file=stderr)
                return False
        return True

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
        print("Error during data indexing")
        return False


if __name__ == "__main__":
    ch = CHIndexer()
    ch.run()
