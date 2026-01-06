# Getting Started

[← Back to README](../README.md)

Follow these steps to set up Apple Health MCP Server in your environment.

## Prerequisites

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
   Edit the `config/.env` file with your credentials and configuration. See [Environment Variables](../README.md#-Environment-Variables)

## Prepare Your Data

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
   - Run `make ch` to create a database with your exported XML data
   - **Note: If you are using Windows, Docker is the only way to integrate ClickHouse into this MCP Server.**
   - On Windows: Run `mingw32-make chwin` (or any other version of `make` available on Windows)

4. Lastly, if you're going to be using DuckDB:
   - Run `make duckdb` to create a parquet file with your exported XML data
   - If you want to connect to the file through http(s):
     - The only thing you need to do is change the .env path, e.g. `localhost:8080/applehealth.parquet`
     - If you want an example on how to host the files locally, run `uv run tests/fileserver.py`


## Configuration Files

You can run the MCP Server in your LLM Client in two ways:
- **Docker** (recommended)
- **Local (uv run)**

### Docker MCP Server

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
            "--mount", // optional - only include this if you use clickhouse
            "type=bind,source=<project-path>/applehealth.chdb,target=/root_project/applehealth.chdb", // optional
            "--mount", // optional - only include this if you use duckdb
            "type=bind,source=<project-path>/<parquet-file-name>,target=/root_project/applehealth.parquet", // optional
            "-e",
            "ES_HOST=host.docker.internal",
            "mcp-server:latest"
         ]
       }
     }
   }
   ```

### Local uv MCP Server

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

## 3. Restart Your MCP Client

After completing the above steps, restart your MCP Client to apply the changes. In some cases, you may need to terminate all related processes using Task Manager or your system's process manager to ensure:
- The updated configuration is properly loaded
- Environment variables are correctly applied
- The Apple Health MCP client initializes with the correct settings
