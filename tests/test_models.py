"""Unit tests for kusto_mcp.models module."""

import json

import pytest
from pydantic import ValidationError

from kusto_mcp.models import Column, TableSchema


class TestColumn:
  """Tests for the Column model."""

  def test_column_creation(self) -> None:
    """Test basic Column creation."""
    column = Column(
      name="DeviceId",
      type="string",
      description="Unique identifier for the device.",
    )
    assert column.name == "DeviceId"
    assert column.type == "string"
    assert column.description == "Unique identifier for the device."

  def test_column_with_different_types(self) -> None:
    """Test Column with various Kusto data types."""
    types = ["string", "bool", "long", "int", "datetime", "dynamic", "real", "guid"]
    for kusto_type in types:
      column = Column(
        name="TestColumn",
        type=kusto_type,
        description=f"Column of type {kusto_type}",
      )
      assert column.type == kusto_type

  def test_column_missing_required_field(self) -> None:
    """Test that missing required fields raise ValidationError."""
    with pytest.raises(ValidationError):
      Column(name="DeviceId", type="string")  # type: ignore[call-arg]

    with pytest.raises(ValidationError):
      Column(name="DeviceId", description="desc")  # type: ignore[call-arg]

    with pytest.raises(ValidationError):
      Column(type="string", description="desc")  # type: ignore[call-arg]

  def test_column_serialization(self, sample_column: Column) -> None:
    """Test Column JSON serialization."""
    json_str = sample_column.model_dump_json()
    data = json.loads(json_str)
    assert data["name"] == sample_column.name
    assert data["type"] == sample_column.type
    assert data["description"] == sample_column.description

  def test_column_deserialization(self) -> None:
    """Test Column creation from dict."""
    data = {
      "name": "EventTime",
      "type": "datetime",
      "description": "Event timestamp.",
    }
    column = Column.model_validate(data)
    assert column.name == "EventTime"
    assert column.type == "datetime"
    assert column.description == "Event timestamp."


class TestTableSchema:
  """Tests for the TableSchema model."""

  def test_table_schema_creation(self, sample_columns: list[Column]) -> None:
    """Test basic TableSchema creation."""
    schema = TableSchema(
      schema_url="https://example.com/schema.json",
      table_name="DeviceInfo",
      table_description="Device information table.",
      reference="https://docs.example.com/deviceinfo",
      columns=sample_columns,
    )
    assert schema.schema_url == "https://example.com/schema.json"
    assert schema.table_name == "DeviceInfo"
    assert schema.table_description == "Device information table."
    assert schema.reference == "https://docs.example.com/deviceinfo"
    assert len(schema.columns) == len(sample_columns)

  def test_table_schema_with_alias(self) -> None:
    """Test TableSchema creation using $schema alias."""
    data = {
      "$schema": "https://example.com/schema.json",
      "table_name": "DeviceInfo",
      "table_description": "Device info.",
      "reference": "https://example.com",
      "columns": [
        {"name": "Id", "type": "string", "description": "ID field."},
      ],
    }
    schema = TableSchema.model_validate(data)
    assert schema.schema_url == "https://example.com/schema.json"

  def test_table_schema_serialization_with_alias(
    self, sample_table_schema: TableSchema
  ) -> None:
    """Test TableSchema JSON serialization with by_alias option."""
    json_str = sample_table_schema.model_dump_json(by_alias=True)
    data = json.loads(json_str)

    # Should use $schema when by_alias=True
    assert "$schema" in data
    assert data["$schema"] == sample_table_schema.schema_url
    assert "schema_url" not in data

  def test_table_schema_serialization_without_alias(
    self, sample_table_schema: TableSchema
  ) -> None:
    """Test TableSchema JSON serialization without by_alias."""
    json_str = sample_table_schema.model_dump_json()
    data = json.loads(json_str)

    # Should use schema_url when by_alias=False
    assert "schema_url" in data
    assert data["schema_url"] == sample_table_schema.schema_url

  def test_table_schema_empty_columns(self) -> None:
    """Test TableSchema with empty columns list."""
    schema = TableSchema(
      schema_url="https://example.com/schema.json",
      table_name="EmptyTable",
      table_description="Table with no columns.",
      reference="https://example.com",
      columns=[],
    )
    assert schema.columns == []

  def test_table_schema_missing_required_field(self) -> None:
    """Test that missing required fields raise ValidationError."""
    with pytest.raises(ValidationError):
      TableSchema(
        schema_url="https://example.com/schema.json",
        table_name="Test",
        table_description="desc",
        # missing reference and columns
      )  # type: ignore[call-arg]

  def test_table_schema_columns_validation(self) -> None:
    """Test that invalid column data raises ValidationError."""
    with pytest.raises(ValidationError):
      TableSchema(
        schema_url="https://example.com/schema.json",
        table_name="Test",
        table_description="desc",
        reference="https://example.com",
        columns=[{"name": "incomplete"}],  # type: ignore[list-item]
      )

  def test_table_schema_roundtrip(self, sample_table_schema: TableSchema) -> None:
    """Test serialization and deserialization roundtrip."""
    # Serialize with alias (as JSON would appear in files)
    json_str = sample_table_schema.model_dump_json(by_alias=True)

    # Deserialize back
    restored = TableSchema.model_validate_json(json_str)

    assert restored.schema_url == sample_table_schema.schema_url
    assert restored.table_name == sample_table_schema.table_name
    assert restored.table_description == sample_table_schema.table_description
    assert restored.reference == sample_table_schema.reference
    assert len(restored.columns) == len(sample_table_schema.columns)

    for orig, rest in zip(
      sample_table_schema.columns, restored.columns, strict=True
    ):
      assert rest.name == orig.name
      assert rest.type == orig.type
      assert rest.description == orig.description
