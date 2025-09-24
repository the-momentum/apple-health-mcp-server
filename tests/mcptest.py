import asyncio
import os

import pytest
import nest_asyncio
from dotenv import load_dotenv

from agents import Agent, Runner
from agents.mcp import MCPServerStdio, MCPServerStdioParams, MCPServerStreamableHttp, MCPServerStreamableHttpParams
from agents.model_settings import ModelSettings


load_dotenv()
nest_asyncio.apply()


async def main():

    # params = MCPServerStdioParams(
    #     command="uv",
    #     args = [
    #         "run",
    #         "--directory",
    #         "../app",
    #         "fastmcp",
    #         "run",
    #         "main.py"
    #     ]
    # )
    #
    # async with MCPServerStdio(
    #     name="cwelowy serwer",
    #     params=params
    # ) as server:

    params = MCPServerStreamableHttpParams(
        url="http://localhost:8000/mcp/"
    )

    async with MCPServerStreamableHttp(
        params=params,
    ) as server:

        agent = Agent(
            name="cwel",
            mcp_servers=[server],
            model_settings=ModelSettings(tool_choice="required")
        )
        result = await Runner.run(agent, "give me a health summary from duckdb")
        print(result.final_output)

asyncio.run(main())