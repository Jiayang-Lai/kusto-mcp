"""Utility functions for loading Kusto table schemas.

This module provides convenience functions that accept any SchemaLoader.
Pass your own loader for custom schema sources, or use the default FileSchemaLoader.
"""

from pathlib import Path

from kusto_mcp.loaders import CSVSchemaLoader, FileSchemaLoader, SchemaLoader
from kusto_mcp.models import Column, TableSchema


def load_columns_from_csv(csv_file: Path) -> list[Column]:
  """Load column definitions from a CSV file.

  The CSV file should have columns: Column, Type, Description.

  Args:
    csv_file: Path to the CSV file containing column definitions.

  Returns:
    A list of Column objects parsed from the CSV.

  Raises:
    FileNotFoundError: If the CSV file does not exist.
    KeyError: If required columns (Column, Type, Description) are missing.
  """
  loader = CSVSchemaLoader()
  return loader.load_columns_from_csv(csv_file)


def load_schema(schema_file: Path) -> TableSchema:
  """Load a single table schema from a JSON file.

  This is a convenience function for file-based loading. For other sources,
  use a custom SchemaLoader directly.

  Args:
    schema_file: Path to the JSON schema file.

  Returns:
    A TableSchema object representing the table.

  Raises:
    FileNotFoundError: If the schema file does not exist.
    json.JSONDecodeError: If the file contains invalid JSON.
    pydantic.ValidationError: If the JSON does not match the schema.
  """
  loader = FileSchemaLoader()
  return loader.load_schema(schema_file)


def load_schemas(loader: SchemaLoader | None = None) -> dict[str, TableSchema]:
  """Load all table schemas using the provided loader.

  Args:
    loader: A SchemaLoader instance to use. Defaults to FileSchemaLoader
      with the samples/schemas directory.

  Returns:
    A dictionary mapping table names to their TableSchema objects.
  """
  if loader is None:
    loader = FileSchemaLoader()
  return loader.load_schemas()


def get_schema_by_name(
  table_name: str, loader: SchemaLoader | None = None
) -> TableSchema | None:
  """Get a specific table schema by name.

  Args:
    table_name: The name of the table to look up.
    loader: A SchemaLoader instance to use. Defaults to FileSchemaLoader
      with the samples/schemas directory.

  Returns:
    The TableSchema for the table, or None if not found.
  """
  if loader is None:
    loader = FileSchemaLoader()
  return loader.get_schema_by_name(table_name)
