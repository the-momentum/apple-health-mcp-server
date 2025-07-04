# MCP server

## Config files

### Docker

Build docker image:
```make build```
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

### UV

Get uv path:

on Windows:
```(Get-Command uv).Path```

on MacOS/Linux:
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
