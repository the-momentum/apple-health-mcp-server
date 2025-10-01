# About The Project

[← Back to README](../README.md)

**Apple Health MCP Server** implements a Model Context Protocol (MCP) server designed for seamless interaction between LLM-based agents and Apple Health data. It provides a standardized interface for querying, analyzing, and managing Apple Health records—imported from XML exports and indexed in Elasticsearch, Clickhouse or DuckDB—through a comprehensive suite of tools. These tools are accessible from MCP-compatible clients (such as Claude Desktop), enabling users to explore, search, and analyze personal health data using natural-language prompts and advanced filtering, all without requiring direct knowledge of the underlying data formats or Elasticsearch/ClickHouse/DuckDB queries.

## 🏗️ Architecture

The Apple Health MCP Server is built with a modular, extensible architecture designed for robust health data management and LLM integration:

- **MCP Tools**: Dedicated tools for Apple Health XML structure analysis, record search, type-based extraction, and statistics/trend generation. Each tool is accessible via the MCP protocol for natural language and programmatic access.
- **XML Import & Parsing**: Efficient streaming and parsing of large Apple Health XML exports, extracting records, workouts, and metadata for further analysis.
- **Elasticsearch Backend**: All health records are indexed in Elasticsearch, enabling fast, scalable search, filtering, and aggregation across large datasets.
- **ClickHouse Backend**: Health records can also be indexed to a ClickHouse database, making the deployment easier for the enduser by using an in-memory database instead of a server-based approach.
- **DuckDB Backend**: Alternative to both Elasticsearch and ClickHouse, DuckDB may offer faster import and query speeds.
- **Service Layer**: Business logic for XML and database operations is encapsulated in dedicated service modules, ensuring separation of concerns and easy extensibility.
- **FastMCP Framework**: Provides the MCP server interface, routing, and tool registration, making the system compatible with LLM-based agents and MCP clients (e.g., Claude Desktop).
- **Configuration & Deployment**: Environment-based configuration and Docker support for easy setup and deployment in various environments.
