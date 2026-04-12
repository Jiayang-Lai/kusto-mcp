"""Entry point for the Kusto MCP server."""

from kusto_mcp.server import mcp


def main() -> None:
  """Run the MCP server."""
  mcp.run()


if __name__ == "__main__":
  main()
