"""Test script for the Kusto MCP server."""

import asyncio

from fastmcp import Client

from kusto_mcp import mcp


async def main():
  """Test the MCP server by listing and calling tools."""
  # mcp is the instantiated FastMCP server from kusto_mcp
  print(f"=== Server: {mcp.name} ===\n")

  # Create a client connected to our MCP server
  async with Client(mcp) as client:
    # List available tools
    print("=== Listing Tools ===")
    tools = await client.list_tools()
    for tool in tools:
      print(f"  - {tool.name}: {tool.description}\n")

    # Call list_tables tool
    print("\n=== Calling list_tables ===")
    result = await client.call_tool("list_tables")
    print(result)

    # Call get_table_schema tool (if available)
    print("\n=== Calling get_table_schema('DeviceInfo') ===")
    try:
      result = await client.call_tool("get_table_schema", {"table_name": "DeviceInfo"})
      print(result)
    except Exception as e:
      print(f"Could not get DeviceInfo schema: {e}")


if __name__ == "__main__":
  asyncio.run(main())
