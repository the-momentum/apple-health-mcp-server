import sys

from fastmcp import FastMCP

from app.mcp.v1.mcp import mcp_router
from app.config import settings


print("SETUP -> Setting up the app", file=sys.stderr)
mcp = FastMCP(settings.PROJECT_NAME)

mcp.mount(mcp_router)

if __name__ == "__main__":
    mcp.run()
