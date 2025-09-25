import asyncio
import os

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai import Agent
from pydantic_ai.tools import Tool
from pydantic_ai.mcp import MCPServerStreamableHTTP

from dotenv import load_dotenv
load_dotenv()
from app.config import settings

class AgentManager:
    def __init__(self):
        self.agent: Agent | None = None
        self.mcp_client: MCPServerStreamableHTTP | None = None
        self.tools: list[Tool] | None = None
        self._initialized = False

    async def initialize(self, model: str = "gpt-4o",
                         system_prompt: str | None = None):
        if self._initialized:
            return
        try:
            self.mcp_client = MCPServerStreamableHTTP("http://localhost:8000/mcp")
        except Exception as e:
            self.mcp_client = None
            raise ConnectionError("Could not connect to MCP server") from e

        if system_prompt is None:
            system_prompt = "You are an AI assistant to help the user as best as you can. You can use the tools provided to you to help the user."

        self.agent = self._create_agent(model, system_prompt)
        self._initialized = True

    def _create_agent(self, model: str, system_prompt: str) -> Agent:
        model = OpenAIChatModel(model, provider=OpenAIProvider(api_key=os.getenv("api_key")))
        return Agent(
            model=model,
            deps_type=dict[str, str],
            system_prompt=system_prompt,
            toolsets=[self.mcp_client],
            output_type=str,
        )

    async def handle_message(self, message: str) -> str:
        if not self._initialized:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        async with self.agent:
            result = await self.agent.run(message)
            return result.output

    def is_initialized(self) -> bool:
        return self._initialized

    async def close(self):
        """Close the MCP client"""
        if self.mcp_client:
            await self.mcp_client.close()


agent_manager = AgentManager()


async def main():
    await agent_manager.initialize()

    try:
        while True:
            user_input = input("Enter your message: ")
            if user_input == "exit":
                break
            print("User: ", user_input)
            response = await agent_manager.handle_message(user_input)
            print("Agent: ", response)
    finally:
        await agent_manager.close()


if __name__ == "__main__":
    asyncio.run(main())