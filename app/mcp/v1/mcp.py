from fastmcp import FastMCP

from app.mcp.v1.tools import es_reader, xml_reader, ch_reader

mcp_router = FastMCP(name="Main MCP")

mcp_router.mount(es_reader.es_reader_router)
mcp_router.mount(xml_reader.xml_reader_router)
mcp_router.mount(ch_reader.ch_reader_router)
