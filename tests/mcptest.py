import pytest

from agents import Agent, Runner
from agents.mcp import MCPServerStdio, MCPServerStdioParams

params = MCPServerStdioParams(
    command="uv",
    args = [
        "run",
        "--directory",
        "..",
        "fastmcp",
        "run",
        "start.py"
    ]
)

server = MCPServerStdio(params=params)

agent = Agent()