# MCP server

## Prepare your data
1. Place your XML file exported from Apple Health somewhere in your filesystem. By default, LLM should look for that file in project root directory.
2. If you don't have local instance of elasticsearch and want to use it, you can obtain it in 2 ways:

    - run MCP server with **docker method**, then elasticsearch container will be created automatically

    - if you choose **local uv run method**, first you have to run from project root directory command: `./scripts/run_elasticsearch.sh`

3. If you want to use elasticsearch, load data from XML into elasticsearch index by running script: `uv run python3 scripts/xml2es.py`.
    - run command `uv run python3 scripts/xml2es.py --delete-all` to remove all data from elasticsearch index


## Config files

You can run that MCP Server in your LLM Client in two ways:
- docker
- local uv run

### Docker MCP Server

1. Build docker image:
```make build```.
2. Put config into LLM Client settings (remember to replace path to your local repository or remove optional binding):
```
{
    "mcpServers": {
        "docker-mcp-server": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "--init",
                "--mount", # optional - volume for reload
                "type=bind,source=<project-path>/app,target=/root_project/app", # optional
                "--mount",
                "type=bind,source=<project-path>/config/.env,target=/root_project/config/.env",
                "mcp-server:latest"
            ]
        }
    }
}
```

### Local uv MCP Server
Get uv path and enter it in the config below, then put that config into LLM Client settings:

- on Windows:
```(Get-Command uv).Path```

- on MacOS/Linux:
```which uv```
```
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
                "PATH": "<path-to-bin-folder(without uv at the end of path)>"
            }
        }
    }
}
```
