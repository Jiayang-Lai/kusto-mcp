"""Abstract base class and implementations for loading table schemas."""

import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path

from kusto_mcp.models import Column, TableSchema

# Default path to schema files
# (3 levels up: kusto_mcp -> src -> project root)
DEFAULT_SCHEMAS_DIR = Path(__file__).parent.parent.parent / "samples" / "schemas"
DEFAULT_CSV_SCHEMAS_DIR = (
  Path(__file__).parent.parent.parent / "samples" / "schemas_csv"
)


class SchemaLoader(ABC):
  """Abstract base class for loading Kusto table schemas.

  Subclasses must implement the `load_schemas` method to provide
  different schema loading strategies (e.g., from files, API, database).
  """

  @abstractmethod
  def load_schemas(self) -> dict[str, TableSchema]:
    """Load all table schemas.

    Returns:
      A dictionary mapping table names to their TableSchema objects.
    """
    pass

  def get_schema_by_name(self, table_name: str) -> TableSchema | None:
    """Get a specific table schema by name.

    Args:
      table_name: The name of the table to look up.

    Returns:
      The TableSchema for the table, or None if not found.
    """
    schemas = self.load_schemas()
    return schemas.get(table_name)


class FileSchemaLoader(SchemaLoader):
  """Load table schemas from JSON files in a directory.

  If no directory is specified, it defaults to the `samples/schemas` directory
  """

  def __init__(self, schemas_dir: Path | None = None):
    """Initialize the file schema loader.

    Args:
      schemas_dir: Directory containing JSON schema files.
        Defaults to the samples/schemas directory.
    """
    self.schemas_dir = schemas_dir or DEFAULT_SCHEMAS_DIR

  def load_schema(self, schema_file: Path) -> TableSchema:
    """Load a single table schema from a JSON file.

    Args:
      schema_file: Path to the JSON schema file.

    Returns:
      A TableSchema object representing the table.

    Raises:
      FileNotFoundError: If the schema file does not exist.
      json.JSONDecodeError: If the file contains invalid JSON.
      pydantic.ValidationError: If the JSON does not match the schema.
    """
    with open(schema_file) as f:
      data = json.load(f)
    return TableSchema.model_validate(data)

  def load_schemas(self) -> dict[str, TableSchema]:
    """Load all table schemas from the configured directory.

    Returns:
      A dictionary mapping table names to their TableSchema objects.
    """
    schemas: dict[str, TableSchema] = {}

    if not self.schemas_dir.exists():
      return schemas

    for schema_file in self.schemas_dir.glob("*.json"):
      schema = self.load_schema(schema_file)
      schemas[schema.table_name] = schema

    return schemas


class CSVSchemaLoader(SchemaLoader):
  """Load table schemas from CSV files in a directory.

  CSV files should have columns: name, type, description.
  The table name is derived from the filename (e.g., DeviceInfo.csv -> DeviceInfo).

  If no directory is specified, it defaults to the `samples/schemas_csv` directory.
  """

  def __init__(
    self,
    schemas_dir: Path | None = None,
    schema_url: str = "",
    reference_base_url: str = "https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/",
  ):
    """Initialize the CSV schema loader.

    Args:
      schemas_dir: Directory containing CSV schema files.
        Defaults to the samples/schemas_csv directory.
      schema_url: URL for the $schema field (default: empty string).
      reference_base_url: Base URL for generating reference links.
        The table name (lowercased) is appended to form the full URL.
    """
    self.schemas_dir = schemas_dir or DEFAULT_CSV_SCHEMAS_DIR
    self.schema_url = schema_url
    self.reference_base_url = reference_base_url

  def load_columns_from_csv(self, csv_file: Path) -> list[Column]:
    """Load column definitions from a CSV file.

    Args:
      csv_file: Path to the CSV file containing column definitions.

    Returns:
      A list of Column objects parsed from the CSV.

    Raises:
      FileNotFoundError: If the CSV file does not exist.
      KeyError: If required columns (Column, Type, Description) are missing.
    """
    columns: list[Column] = []

    with open(csv_file, newline="", encoding="utf-8") as f:
      reader = csv.DictReader(f)
      for row in reader:
        column = Column(
          name=row["Column"],
          type=row["Type"],
          description=row["Description"],
        )
        columns.append(column)

    return columns

  def load_schema(self, csv_file: Path) -> TableSchema:
    """Load a table schema from a CSV file.

    Args:
      csv_file: Path to the CSV file.

    Returns:
      A TableSchema object with columns from the CSV.
      Table name is derived from the filename.
    """
    table_name = csv_file.stem
    columns = self.load_columns_from_csv(csv_file)

    return TableSchema(
      schema_url=self.schema_url,
      table_name=table_name,
      table_description=f"Schema for {table_name} table.",
      reference=f"{self.reference_base_url}{table_name.lower()}",
      columns=columns,
    )

  def load_schemas(self) -> dict[str, TableSchema]:
    """Load all table schemas from CSV files in the configured directory.

    Returns:
      A dictionary mapping table names to their TableSchema objects.
    """
    schemas: dict[str, TableSchema] = {}

    if not self.schemas_dir.exists():
      return schemas

    for csv_file in self.schemas_dir.glob("*.csv"):
      schema = self.load_schema(csv_file)
      schemas[schema.table_name] = schema

    return schemas
