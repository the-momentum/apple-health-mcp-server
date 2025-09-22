# Configuration

[← Back to README](../README.md)

## Environment Variables

> **Note:** All variables below are optional unless marked as required. If not set, the server will use the default values shown. Only `RAW_XML_PATH` is required and must point to your Apple Health XML file.

| Variable           | Description                                | Example Value         | Required |
|--------------------|--------------------------------------------|----------------------|----------|
| RAW_XML_PATH       | Path to the Apple Health XML file           | `raw.xml`            | ✅       |
| ES_HOST            | Elasticsearch host                          | `localhost`          | ❌       |
| ES_PORT            | Elasticsearch port                          | `9200`               | ❌       |
| ES_USER            | Elasticsearch username                      | `elastic`            | ❌       |
| ES_PASSWORD        | Elasticsearch password                      | `elastic`            | ❌       |
| ES_INDEX           | Elasticsearch index name                    | `apple_health_data`  | ❌       |
| CH_DIRNAME         | ClickHouse directory name                   | `applehealth.chdb`   | ❌       |
| CH_DB_NAME         | ClickHouse database name                    | `applehealth`        | ❌       |
| CH_TABLE_NAME      | ClickHouse table name                       | `data`               | ❌       |
| DUCKDB_FILENAME    | DuckDB parquet file name                    | `applehealth`        | ❌       |
| CHUNK_SIZE         | Records indexed into CH/DuckDB at once      | `50000`              | ❌       |
| XML_SAMPLE_SIZE    | Number of XML records to sample             | `1000`               | ❌       |
