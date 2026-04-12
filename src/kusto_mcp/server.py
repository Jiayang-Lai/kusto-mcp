"""MCP server for Kusto table schemas."""

import json
import threading

from fastmcp import FastMCP

from kusto_mcp.loaders import FileSchemaLoader, SchemaLoader
from kusto_mcp.models import TableSchema

# Initialize MCP server
mcp = FastMCP("Kusto MCP")

# Schema state - lazy loaded on first access
_schemas: dict[str, TableSchema] | None = None
_loader: SchemaLoader | None = None
_lock = threading.Lock()


def configure_loader(loader: SchemaLoader) -> None:
  """Configure the schema loader before first use.

  This must be called before any schema access (e.g., before starting the server)
  to use a custom loader. If not called, defaults to FileSchemaLoader.

  This function is thread-safe.

  Args:
    loader: The SchemaLoader instance to use for loading schemas.

  Raises:
    RuntimeError: If schemas have already been loaded.
  """
  global _loader, _schemas
  with _lock:
    if _schemas is not None:
      raise RuntimeError(
        "Cannot configure loader after schemas have been loaded. "
        "Call configure_loader() before accessing any resources."
      )
    _loader = loader


def _get_schemas() -> dict[str, TableSchema]:
  """Get schemas, loading them lazily on first access.

  This function is thread-safe using double-checked locking.
  """
  global _schemas, _loader
  if _schemas is None:
    with _lock:
      # Double-check after acquiring lock
      if _schemas is None:
        if _loader is None:
          _loader = FileSchemaLoader()
        _schemas = _loader.load_schemas()
  return _schemas


@mcp.tool()
def list_tables() -> str:
  """List all available Kusto tables.

  Returns:
    A JSON array of table names with their descriptions.
  """
  schemas = _get_schemas()
  tables = [
    {"name": schema.table_name, "description": schema.table_description}
    for schema in schemas.values()
  ]
  return json.dumps(tables)


@mcp.tool()
def get_table_schema(table_name: str) -> str:
  """Get the schema for a specific Kusto table.

  Args:
    table_name: The name of the table to retrieve the schema for.

  Returns:
    JSON representation of the table schema.

  Raises:
    KeyError: If the table is not found.
  """
  schemas = _get_schemas()
  if table_name not in schemas:
    raise KeyError(
      f"Table '{table_name}' not found. Available tables: {list(schemas.keys())}"
    )

  schema = schemas[table_name]
  return schema.model_dump_json(by_alias=True)
