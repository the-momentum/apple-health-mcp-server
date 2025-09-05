<a name="readme-top"></a>

<div align="center">
  <img src="https://cdn.prod.website-files.com/66a1237564b8afdc9767dd3d/66df7b326efdddf8c1af9dbb_Momentum%20Logo.svg" height="80">
  <h1>Apple Health MCP Server</h1>
  <p><strong>Apple Health Data Management</strong></p>

  [![Contact us](https://img.shields.io/badge/Contact%20us-AFF476.svg?style=for-the-badge&logo=mail&logoColor=black)](mailto:hello@themomentum.ai?subject=Apple%20Health%20MCP%20Server%20Inquiry)
  [![Visit Momentum](https://img.shields.io/badge/Visit%20Momentum-1f6ff9.svg?style=for-the-badge&logo=safari&logoColor=white)](https://themomentum.ai)
  [![MIT License](https://img.shields.io/badge/License-MIT-636f5a.svg?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](LICENSE)

  <a href="https://glama.ai/mcp/servers/@the-momentum/apple-health-mcp-server">
    <img width="380" height="200" src="https://glama.ai/mcp/servers/@the-momentum/apple-health-mcp-server/badge" alt="Apple Health Server MCP server" />
  </a>
</div>

## 📋 Table of Contents

- [🔍 About](#-about-the-project)
- [💡 Demo](#-demo)
- [🚀 Getting Started](#-getting-started)
- [📝 Usage](#-usage)
- [🔧 Configuration](#-configuration)
- [🐳 Docker Setup](#-docker-mcp)
- [🛠️ MCP Tools](#️-mcp-tools)
- [🗺️ Roadmap](#️-roadmap)
- [👥 Contributors](#-contributors)
- [📄 License](#-license)

## 🔍 About The Project

**Apple Health MCP Server** implements a Model Context Protocol (MCP) server designed for seamless interaction between LLM-based agents and Apple Health data. It provides a standardized interface for querying, analyzing, and managing Apple Health records—imported from XML exports and indexed in Elasticsearch or Clickhouse—through a comprehensive suite of tools. These tools are accessible from MCP-compatible clients (such as Claude Desktop), enabling users to explore, search, and analyze personal health data using natural-language prompts and advanced filtering, all without requiring direct knowledge of the underlying data formats or Elasticsearch/ClickHouse queries.

### ✨ Key Features

- **🚀 FastMCP Framework**: Built on FastMCP for high-performance MCP server capabilities
- **🍏 Apple Health Data Management**: Import, parse, and analyze Apple Health XML exports
- **🔎 Powerful Search & Filtering**: Query and filter health records using natural language and advanced parameters
- **📦 Elasticsearch and ClickHouse Integration**: Index and search health data efficiently at scale
- **🛠️ Modular MCP Tools**: Tools for structure analysis, record search, type-based extraction, and more
- **📈 Data Summaries & Trends**: Generate statistics and trend analyses from your health data
- **🐳 Container Ready**: Docker support for easy deployment and scaling
- **🔧 Configurable**: Extensive ```.env```-based configuration options

### 🏗️ Architecture

The Apple Health MCP Server is built with a modular, extensible architecture designed for robust health data management and LLM integration:

- **MCP Tools**: Dedicated tools for Apple Health XML structure analysis, record search, type-based extraction, and statistics/trend generation. Each tool is accessible via the MCP protocol for natural language and programmatic access.
- **XML Import & Parsing**: Efficient streaming and parsing of large Apple Health XML exports, extracting records, workouts, and metadata for further analysis.
- **Elasticsearch Backend**: All health records are indexed in Elasticsearch, enabling fast, scalable search, filtering, and aggregation across large datasets.
- **ClickHouse Backend**: Health records can also be indexed to a ClickHouse database, making the deployment easier for the enduser by using an in-memory database instead of a server-based approach.
- **Service Layer**: Business logic for XML and Elasticsearch operations is encapsulated in dedicated service modules, ensuring separation of concerns and easy extensibility.
- **FastMCP Framework**: Provides the MCP server interface, routing, and tool registration, making the system compatible with LLM-based agents and MCP clients (e.g., Claude Desktop).
- **Configuration & Deployment**: Environment-based configuration and Docker support for easy setup and deployment in various environments.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 💡 Demo

This demo shows how Claude uses the `apple-health-mcp-server` to answer questions about your data. Example prompts from the demo:
- I would like you to help me analyze my Apple Health data. Let's start by analyzing the data types - check what data is available and how much of it there is.
- What can you tell me about my activity in the last week? How did my daily statistics look?
- Please also summarise my running workouts in July and June. Do you see anything interesting?

https://github.com/user-attachments/assets/93ddbfb9-6da9-42c1-9872-815abce7e918

## 🚀 Getting Started

Follow these steps to set up Apple Health MCP Server in your environment.

### Prerequisites

- **Docker (recommended) or uv + docker**: For dependency management

   👉 [uv Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)
- **Clone the repository**:
   ```sh
   git clone https://github.com/the-momentum/apple-health-mcp-server
   cd apple-health-mcp-server
   ```

- **Set up environment variables**:
   ```sh
   cp config/.env.example config/.env
   ```
   Edit the `config/.env` file with your credentials and configuration. See [Environment Variables](#-Environment-Variables)

### Prepare Your Data

1. Export your Apple Health data as an XML file from your iPhone and place it somewhere in your filesystem. By default, the server expects the file in the project root directory.
  - if you need working example, we suggest this dataset: https://drive.google.com/file/d/1bWiWmlqFkM3MxJZUD2yAsNHlYrHvCmcZ/view?usp=drive_link
    - Rob Mulla. Predict My Sleep Patterns. https://kaggle.com/competitions/kaggle-pog-series-s01e04, 2023. Kaggle.
2. Prepare an Elasticsearch instance and populate it from the XML file:
   - Run `make es` to start Elasticsearch and import your XML data.
   - (Optional) To clear all data from the Elasticsearch index, run:
     ```sh
     uv run python scripts/xml2es.py --delete-all
     ```
3. If you choose to use ClickHouse instead of Elasticsearch:
   - Run `make ch` to create a Docker volume with your data in it **OR**
   - Run `uv run app/services/ch.py` if you're using an uv installation method.
   - **Note: If you are using Windows, Docker is the only way to integrate ClickHouse into this MCP Server.**
   - On Windows: Run `mingw32-make chwin` (or any other version of `make` available on Windows)

### Configuration Files

You can run the MCP Server in your LLM Client in two ways:
- **Docker** (recommended)
- **Local (uv run)**

#### Docker MCP Server

1. Build the Docker image:
   ```sh
   make build
   ```
2. Add the following config to your LLM Client settings (replace `<project-path>` with your local repository path and `<xml-file-name>` with name of your raw data from apple health file (without `.xml` extension)):
   ```json
   {
     "mcpServers": {
       "docker-mcp-server": {
         "command": "docker",
         "args": [
           "run",
           "-i",
           "--rm",
           "--init",
           "--mount",
           "type=bind,source=<project-path>/{xml-file-name}.xml,target=/root_project/raw.xml",
           "--mount", // optional - volume for reload
           "type=bind,source=<project-path>/app,target=/root_project/app", // optional
           "--mount",
           "type=bind,source=<project-path>/config/.env,target=/root_project/config/.env",
           "--mount",
		   "type=bind,source=C:\\Users\\czajk\\Desktop\\apple-health-mcp-server\\applehealth.chdb,target=/root_project/applehealth.chdb",
           "-e",
           "ES_HOST=host.docker.internal",
           "mcp-server:latest"
         ]
       }
     }
   }
   ```

#### Local uv MCP Server

1. Get the path to your `uv` binary:
   - On Windows:
     ```powershell
     (Get-Command uv).Path
     ```
   - On MacOS/Linux:
     ```sh
     which uv
     ```
2. Add the following config to your LLM Client settings (replace `<project-path>` and `<path-to-bin-folder>` as appropriate):
   ```json
   {
     "mcpServers": {
       "uv-mcp-server": {
         "command": "uv",
         "args": [
           "run",
           "--frozen",
           "--directory",
           "<project-path>",
           "start"
         ],
         "env": {
           "PATH": "<path-to-uv-bin-folder>"
         }
       }
     }
   }
   ```
   - `<path-to-uv-bin-folder>` should be the folder containing the `uv` binary (do not include `uv` itself at the end).

### 3. Restart Your MCP Client

After completing the above steps, restart your MCP Client to apply the changes. In some cases, you may need to terminate all related processes using Task Manager or your system's process manager to ensure:
- The updated configuration is properly loaded
- Environment variables are correctly applied
- The Apple Health MCP client initializes with the correct settings

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## 🔧 Configuration

### Environment Variables

> **Note:** All variables below are optional unless marked as required. If not set, the server will use the default values shown. Only `RAW_XML_PATH` is required and must point to your Apple Health XML file.

| Variable           | Description                                | Example Value         | Required |
|--------------------|--------------------------------------------|----------------------|----------|
| RAW_XML_PATH       | Path to the Apple Health XML file           | `raw.xml`            | ✅       |
| ES_HOST            | Elasticsearch host                          | `localhost`          | ❌       |
| ES_PORT            | Elasticsearch port                          | `9200`               | ❌       |
| ES_USER            | Elasticsearch username                      | `elastic`            | ❌       |
| ES_PASSWORD        | Elasticsearch password                      | `elastic`            | ❌       |
| ES_INDEX           | Elasticsearch index name                    | `apple_health_data`  | ❌       |
| CH_DB_NAME         | ClickHouse database name                    | `applehealth`        | ❌       |
| CH_TABLE_NAME      | ClickHouse table name                       | `data`               | ❌       |
| CHUNK_SIZE         | Number of records indexed into CH at once   | `10000`              | ❌       |
| XML_SAMPLE_SIZE    | Number of XML records to sample             | `1000`               | ❌       |

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## 🛠️ MCP Tools

The Apple Health MCP Server provides a suite of tools for exploring, searching, and analyzing your Apple Health data, both at the raw XML level and in Elasticsearch/ClickHouse:

### XML Tools (`xml_reader`)

| Tool                | Description                                                                                   |
|---------------------|-----------------------------------------------------------------------------------------------|
| `get_xml_structure` | Analyze the structure and metadata of your Apple Health XML export (file size, tags, types).   |
| `search_xml_content`| Search for specific content in the XML file (by attribute value, device, type, etc.).          |
| `get_xml_by_type`   | Extract all records of a specific health record type from the XML file.                        |

### Elasticsearch Tools (`es_reader`)

| Tool                        | Description                                                                                         |
|-----------------------------|-----------------------------------------------------------------------------------------------------|
| `get_health_summary_es`     | Get a summary of all Apple Health data in Elasticsearch (total count, type breakdown, etc.).         |
| `search_health_records_es`  | Flexible search for health records in Elasticsearch with advanced filtering and query options.        |
| `get_statistics_by_type_es` | Get comprehensive statistics (count, min, max, avg, sum) for a specific health record type.          |
| `get_trend_data_es`         | Analyze trends for a health record type over time (daily, weekly, monthly, yearly aggregations).     |

### ClickHouse Tools (`ch_reader`)

| Tool                        | Description                                                                                         |
|-----------------------------|-----------------------------------------------------------------------------------------------------|
| `get_health_summary_ch`     | Get a summary of all Apple Health data in ClickHouse (total count, type breakdown, etc.).         |
| `search_health_records_ch`  | Flexible search for health records in ClickHouse with advanced filtering and query options.        |
| `get_statistics_by_type_ch` | Get comprehensive statistics (count, min, max, avg, sum) for a specific health record type.          |
| `get_trend_data_ch`         | Analyze trends for a health record type over time (daily, weekly, monthly, yearly aggregations).     |

All tools are accessible via MCP-compatible clients and can be used with natural language or programmatic queries to explore and analyze your Apple Health data.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## 🗺️ Roadmap

We're continuously enhancing Apple Health MCP Server with new capabilities. Here's what's on the horizon:

- [ ] **Time Series Sampling During Import**: Add advanced analytical tools to sample and generate time series data directly during the XML-to-Elasticsearch loading process.
- [ ] **Optimized XML Tools**: Improve the performance and efficiency of XML parsing and querying tools.
- [ ] **Expanded Elasticsearch Analytics**: Add more advanced analytics and aggregation functions to the Elasticsearch toolset.
- [ ] **Embedded Database Tools**: Integrate tools for working with embedded databases for local/offline analytics and storage.

Have a suggestion? We'd love to hear from you! Contact us or contribute directly.

## 👥 Contributors

<a href="https://github.com/the-momentum/apple-health-mcp-server/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=the-momentum/apple-health-mcp-server" />
</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 📄 License

Distributed under the MIT License. See [MIT License](LICENSE) for more information.

---

<div align="center">
  <p><em>Built with ❤️ by <a href="https://themomentum.ai">Momentum</a> • Transforming healthcare data management with AI</em></p>
</div>
