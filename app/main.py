import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from app.config import settings
from app.mcp.v1.mcp import mcp_router
from app.services.health.manual_logs import close_con


@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[None]:
    try:
        yield
    finally:
        # Flush the manual-logs DB (CHECKPOINT + close) on a clean shutdown /
        # client disconnect so nothing is stranded in the WAL.
        close_con()


print("SETUP -> Setting up the app", file=sys.stderr)
mcp = FastMCP(settings.PROJECT_NAME, lifespan=lifespan)

mcp.mount(mcp_router)

if __name__ == "__main__":
    mcp.run()
