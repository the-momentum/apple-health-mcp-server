import asyncio

import nest_asyncio
from agents import Agent, Runner
from agents.mcp import (
    MCPServerStreamableHttp,
    MCPServerStreamableHttpParams,
)
from agents.model_settings import ModelSettings
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from ragas.dataset_schema import MultiTurnSample
from ragas.llms import LangchainLLMWrapper
from ragas.messages import AIMessage, HumanMessage, ToolCall, ToolMessage
from ragas.metrics import AgentGoalAccuracyWithReference

LangchainLLMWrapper()

chat = ChatOpenAI()

load_dotenv()
nest_asyncio.apply()


async def main() -> None:
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
        url="http://localhost:8000/mcp/",
    )

    async with MCPServerStreamableHttp(
        params=params,
    ) as server:
        agent = Agent(
            name="cwel",
            mcp_servers=[server],
            model_settings=ModelSettings(tool_choice="required"),
        )
        result = await Runner.run(agent, "give me a health summary from duckdb")
        print(result.final_output)



asyncio.run(main())
