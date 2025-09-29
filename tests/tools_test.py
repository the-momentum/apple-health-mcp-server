import asyncio

from fastmcp import FastMCP

from app.mcp.v1.mcp import mcp_router


app = FastMCP()

@app.tool
def add_nr(a: int, b: int) -> int:
    return a + b

async def get_mcp_tools(mcp: FastMCP):
    return await mcp.get_tools()

ad = {"b": 6, "a": 5, "6": 7}
ab = {"6": 7, "a": 5, "b": 6}

print(asyncio.run(get_mcp_tools(mcp_router)))

print(ad == ab)
