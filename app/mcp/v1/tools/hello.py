from fastmcp import FastMCP

hello_router = FastMCP(name="Hello MCP")


@hello_router.tool
def hello(name: str) -> str:
    """Say hello to user."""
    return f"Hello {name}, what's up!"
