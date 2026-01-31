from fastmcp import FastMCP

mcp = FastMCP(name="Echo MCP Server")


@mcp.tool(description="A simple echo tool")
def echo(message: str) -> str:
    return f"Echo: {message}"
