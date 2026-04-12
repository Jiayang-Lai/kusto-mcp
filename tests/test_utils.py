"""Unit tests for kusto_mcp.utils module."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from kusto_mcp.loaders import CSVSchemaLoader, FileSchemaLoader
from kusto_mcp.models import Column, TableSchema
from kusto_mcp.utils import (
  get_schema_by_name,
  load_columns_from_csv,
  load_schema,
  load_schemas,
)


class TestLoadColumnsFromCsv:
  """Tests for the load_columns_from_csv utility function."""

  def test_load_columns_success(self, temp_csv_schemas_dir: Path) -> None:
    """Test loading columns from a valid CSV file."""
    columns = load_columns_from_csv(temp_csv_schemas_dir / "DeviceInfo.csv")

    assert len(columns) == 3
    assert all(isinstance(c, Column) for c in columns)
    assert columns[0].name == "DeviceId"

  def test_load_columns_file_not_found(self) -> None:
    """Test FileNotFoundError for nonexistent CSV file."""
    with pytest.raises(FileNotFoundError):
      load_columns_from_csv(Path("/nonexistent/file.csv"))


class TestLoadSchema:
  """Tests for the load_schema utility function."""

  def test_load_schema_success(self, temp_schemas_dir: Path) -> None:
    """Test loading a valid JSON schema file."""
    schema = load_schema(temp_schemas_dir / "DeviceInfo.json")

    assert isinstance(schema, TableSchema)
    assert schema.table_name == "DeviceInfo"
    assert len(schema.columns) == 4

  def test_load_schema_file_not_found(self) -> None:
    """Test FileNotFoundError for nonexistent JSON file."""
    with pytest.raises(FileNotFoundError):
      load_schema(Path("/nonexistent/file.json"))


class TestLoadSchemas:
  """Tests for the load_schemas utility function."""

  def test_load_schemas_with_default_loader(self) -> None:
    """Test loading schemas with default FileSchemaLoader."""
    # This will use the default schemas directory
    schemas = load_schemas()

    # Should return a dict (may or may not have entries depending on samples)
    assert isinstance(schemas, dict)

  def test_load_schemas_with_file_loader(self, temp_schemas_dir: Path) -> None:
    """Test loading schemas with explicit FileSchemaLoader."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    schemas = load_schemas(loader=loader)

    assert len(schemas) == 2
    assert "DeviceInfo" in schemas
    assert "DeviceEvents" in schemas

  def test_load_schemas_with_csv_loader(self, temp_csv_schemas_dir: Path) -> None:
    """Test loading schemas with CSVSchemaLoader."""
    loader = CSVSchemaLoader(schemas_dir=temp_csv_schemas_dir)
    schemas = load_schemas(loader=loader)

    assert len(schemas) == 2
    assert "DeviceInfo" in schemas
    assert "DeviceEvents" in schemas

  def test_load_schemas_with_custom_loader(
    self, sample_table_schema: TableSchema
  ) -> None:
    """Test loading schemas with a custom mock loader."""
    mock_loader = MagicMock()
    mock_loader.load_schemas.return_value = {"TestTable": sample_table_schema}

    schemas = load_schemas(loader=mock_loader)

    assert len(schemas) == 1
    assert "TestTable" in schemas
    mock_loader.load_schemas.assert_called_once()


class TestGetSchemaByName:
  """Tests for the get_schema_by_name utility function."""

  def test_get_schema_by_name_found(self, temp_schemas_dir: Path) -> None:
    """Test getting an existing schema by name."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    schema = get_schema_by_name("DeviceInfo", loader=loader)

    assert schema is not None
    assert schema.table_name == "DeviceInfo"

  def test_get_schema_by_name_not_found(self, temp_schemas_dir: Path) -> None:
    """Test getting a nonexistent schema returns None."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    schema = get_schema_by_name("NonexistentTable", loader=loader)

    assert schema is None

  def test_get_schema_by_name_with_default_loader(self) -> None:
    """Test getting a schema with default loader."""
    # This will use the default FileSchemaLoader
    # May return None if the table doesn't exist in default schemas
    result = get_schema_by_name("SomeTable")
    # Just verify it returns None or a TableSchema
    assert result is None or isinstance(result, TableSchema)

  def test_get_schema_by_name_with_csv_loader(self, temp_csv_schemas_dir: Path) -> None:
    """Test getting a schema using CSV loader."""
    loader = CSVSchemaLoader(schemas_dir=temp_csv_schemas_dir)
    schema = get_schema_by_name("DeviceEvents", loader=loader)

    assert schema is not None
    assert schema.table_name == "DeviceEvents"
    assert len(schema.columns) == 3

  def test_get_schema_by_name_case_sensitive(self, temp_schemas_dir: Path) -> None:
    """Test that schema lookup is case-sensitive."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)

    # Correct case
    schema = get_schema_by_name("DeviceInfo", loader=loader)
    assert schema is not None

    # Wrong case
    schema_wrong_case = get_schema_by_name("deviceinfo", loader=loader)
    assert schema_wrong_case is None

    schema_wrong_case2 = get_schema_by_name("DEVICEINFO", loader=loader)
    assert schema_wrong_case2 is None
