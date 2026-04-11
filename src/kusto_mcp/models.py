"""Pydantic models for Kusto table schemas."""

from pydantic import BaseModel, Field


class Column(BaseModel):
  """Represents a column in a Kusto table.

  Attributes:
    name: The name of the column.
    type: The data type of the column (e.g., string, bool, long, datetime).
    description: Description of what the column contains.
  """

  name: str = Field(description="The name of the column")
  type: str = Field(
    description="The data type of the column (e.g., string, bool, long, datetime)"
  )
  description: str = Field(description="Description of what the column contains")


class TableSchema(BaseModel):
  """Represents a Kusto table schema.

  Attributes:
    schema_url: Reference to the JSON schema definition.
    table_name: Name of the table.
    table_description: Description of the table's purpose and contents.
    reference: URL to the official documentation.
    columns: List of columns in the table.
  """

  schema_url: str = Field(
    alias="$schema", description="Reference to the JSON schema definition"
  )
  table_name: str = Field(description="Name of the table")
  table_description: str = Field(
    description="Description of the table's purpose and contents"
  )
  reference: str = Field(description="URL to the official documentation")
  columns: list[Column] = Field(description="List of columns in the table")

  class Config:
    """Pydantic configuration for TableSchema."""

    populate_by_name = True
