# MCP Tools

[← Back to README](../README.md)

The Apple Health MCP Server provides a suite of tools for exploring, searching, and analyzing your Apple Health data, both at the raw XML level and in Elasticsearch/ClickHouse:

## XML Tools (`xml_reader`)

| Tool                | Description                                                                                   |
|---------------------|-----------------------------------------------------------------------------------------------|
| `get_xml_structure` | Analyze the structure and metadata of your Apple Health XML export (file size, tags, types).   |
| `search_xml_content`| Search for specific content in the XML file (by attribute value, device, type, etc.).          |
| `get_xml_by_type`   | Extract all records of a specific health record type from the XML file.                        |

## Elasticsearch Tools (`es_reader`)

| Tool                        | Description                                                                                         |
|-----------------------------|-----------------------------------------------------------------------------------------------------|
| `get_health_summary_es`     | Get a summary of all Apple Health data in Elasticsearch (total count, type breakdown, etc.).         |
| `search_health_records_es`  | Flexible search for health records in Elasticsearch with advanced filtering and query options.        |
| `get_statistics_by_type_es` | Get comprehensive statistics (count, min, max, avg, sum) for a specific health record type.          |
| `get_trend_data_es`         | Analyze trends for a health record type over time (daily, weekly, monthly, yearly aggregations).     |
| `search_values_es`          | Search for records with exactly matching values (including text).     |

## ClickHouse Tools (`ch_reader`)

| Tool                        | Description                                                                                         |
|-----------------------------|-----------------------------------------------------------------------------------------------------|
| `get_health_summary_ch`     | Get a summary of all Apple Health data in ClickHouse (total count, type breakdown, etc.).         |
| `search_health_records_ch`  | Flexible search for health records in ClickHouse with advanced filtering and query options.        |
| `get_statistics_by_type_ch` | Get comprehensive statistics (count, min, max, avg, sum) for a specific health record type.          |
| `get_trend_data_ch`         | Analyze trends for a health record type over time (daily, weekly, monthly, yearly aggregations).     |
| `search_values_ch`          | Search for records with exactly matching values (including text).     |

## DuckDB Tools (`duckdb_reader`)

| Tool                        | Description                                                                                         |
|-----------------------------|-----------------------------------------------------------------------------------------------------|
| `get_health_summary_duckdb`     | Get a summary of all Apple Health data in DuckDB (total count, type breakdown, etc.).         |
| `search_health_records_duckdb`  | Flexible search for health records in DuckDB with advanced filtering and query options.        |
| `get_statistics_by_type_duckdb` | Get comprehensive statistics (count, min, max, avg, sum) for a specific health record type.          |
| `get_trend_data_duckdb`         | Analyze trends for a health record type over time (daily, weekly, monthly, yearly aggregations).     |
| `search_values_duckdb`          | Search for records with exactly matching values (including text).     |

All tools are accessible via MCP-compatible clients and can be used with natural language or programmatic queries to explore and analyze your Apple Health data.
