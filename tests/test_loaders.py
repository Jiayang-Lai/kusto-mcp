"""Unit tests for kusto_mcp.loaders module."""

import json
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from kusto_mcp.loaders import (
  CSVSchemaLoader,
  FileSchemaLoader,
  SchemaLoader,
)
from kusto_mcp.models import TableSchema


class TestSchemaLoaderAbstract:
  """Tests for the abstract SchemaLoader class."""

  def test_schema_loader_is_abstract(self) -> None:
    """Test that SchemaLoader cannot be instantiated directly."""
    with pytest.raises(TypeError):
      SchemaLoader()  # type: ignore[abstract]

  def test_concrete_loader_must_implement_load_schemas(self) -> None:
    """Test that concrete classes must implement load_schemas."""

    class IncompleteLoader(SchemaLoader):
      """Incomplete loader without load_schemas implementation."""

      pass

    with pytest.raises(TypeError):
      IncompleteLoader()  # type: ignore[abstract]


class TestFileSchemaLoader:
  """Tests for the FileSchemaLoader class."""

  def test_init_with_default_directory(self) -> None:
    """Test FileSchemaLoader initialization with default directory."""
    loader = FileSchemaLoader()
    assert loader.schemas_dir.name == "schemas"
    assert "samples" in str(loader.schemas_dir)

  def test_init_with_custom_directory(self, temp_schemas_dir: Path) -> None:
    """Test FileSchemaLoader initialization with custom directory."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    assert loader.schemas_dir == temp_schemas_dir

  def test_load_schema_single_file(self, temp_schemas_dir: Path) -> None:
    """Test loading a single schema file."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    schema = loader.load_schema(temp_schemas_dir / "DeviceInfo.json")

    assert schema.table_name == "DeviceInfo"
    assert len(schema.columns) == 4
    assert schema.columns[0].name == "DeviceId"

  def test_load_schemas_all(self, temp_schemas_dir: Path) -> None:
    """Test loading all schemas from directory."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    schemas = loader.load_schemas()

    assert len(schemas) == 2
    assert "DeviceInfo" in schemas
    assert "DeviceEvents" in schemas

  def test_load_schemas_empty_directory(self, empty_schemas_dir: Path) -> None:
    """Test loading from empty directory returns empty dict."""
    loader = FileSchemaLoader(schemas_dir=empty_schemas_dir)
    schemas = loader.load_schemas()

    assert schemas == {}

  def test_load_schemas_nonexistent_directory(self) -> None:
    """Test loading from nonexistent directory returns empty dict."""
    loader = FileSchemaLoader(schemas_dir=Path("/nonexistent/path"))
    schemas = loader.load_schemas()

    assert schemas == {}

  def test_load_schema_file_not_found(self, temp_schemas_dir: Path) -> None:
    """Test FileNotFoundError when schema file doesn't exist."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)

    with pytest.raises(FileNotFoundError):
      loader.load_schema(temp_schemas_dir / "nonexistent.json")

  def test_load_schema_invalid_json(self, invalid_json_schema_dir: Path) -> None:
    """Test JSONDecodeError for invalid JSON file."""
    loader = FileSchemaLoader(schemas_dir=invalid_json_schema_dir)

    with pytest.raises(json.JSONDecodeError):
      loader.load_schema(invalid_json_schema_dir / "invalid.json")

  def test_load_schema_validation_error(self) -> None:
    """Test ValidationError for JSON that doesn't match schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
      schemas_dir = Path(tmpdir)
      # Create JSON file missing required fields
      with open(schemas_dir / "incomplete.json", "w") as f:
        json.dump({"table_name": "Incomplete"}, f)

      loader = FileSchemaLoader(schemas_dir=schemas_dir)

      with pytest.raises(ValidationError):
        loader.load_schema(schemas_dir / "incomplete.json")

  def test_get_schema_by_name(self, temp_schemas_dir: Path) -> None:
    """Test getting a specific schema by name."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    schema = loader.get_schema_by_name("DeviceInfo")

    assert schema is not None
    assert schema.table_name == "DeviceInfo"

  def test_get_schema_by_name_not_found(self, temp_schemas_dir: Path) -> None:
    """Test getting a nonexistent schema returns None."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    schema = loader.get_schema_by_name("NonexistentTable")

    assert schema is None


class TestCSVSchemaLoader:
  """Tests for the CSVSchemaLoader class."""

  def test_init_with_default_directory(self) -> None:
    """Test CSVSchemaLoader initialization with default directory."""
    loader = CSVSchemaLoader()
    assert loader.schemas_dir.name == "schemas_csv"
    assert loader.schema_url == ""
    assert "learn.microsoft.com" in loader.reference_base_url

  def test_init_with_custom_parameters(self, temp_csv_schemas_dir: Path) -> None:
    """Test CSVSchemaLoader initialization with custom parameters."""
    loader = CSVSchemaLoader(
      schemas_dir=temp_csv_schemas_dir,
      schema_url="https://custom-schema.com",
      reference_base_url="https://custom-docs.com/",
    )
    assert loader.schemas_dir == temp_csv_schemas_dir
    assert loader.schema_url == "https://custom-schema.com"
    assert loader.reference_base_url == "https://custom-docs.com/"

  def test_load_columns_from_csv(self, temp_csv_schemas_dir: Path) -> None:
    """Test loading columns from a CSV file."""
    loader = CSVSchemaLoader(schemas_dir=temp_csv_schemas_dir)
    columns = loader.load_columns_from_csv(temp_csv_schemas_dir / "DeviceInfo.csv")

    assert len(columns) == 3
    assert columns[0].name == "DeviceId"
    assert columns[0].type == "string"
    assert columns[1].name == "DeviceName"
    assert columns[2].name == "IsActive"
    assert columns[2].type == "bool"

  def test_load_schema_from_csv(self, temp_csv_schemas_dir: Path) -> None:
    """Test loading a full schema from CSV."""
    loader = CSVSchemaLoader(schemas_dir=temp_csv_schemas_dir)
    schema = loader.load_schema(temp_csv_schemas_dir / "DeviceInfo.csv")

    assert schema.table_name == "DeviceInfo"
    assert schema.table_description == "Schema for DeviceInfo table."
    assert "deviceinfo" in schema.reference.lower()
    assert len(schema.columns) == 3

  def test_load_schemas_all(self, temp_csv_schemas_dir: Path) -> None:
    """Test loading all schemas from CSV directory."""
    loader = CSVSchemaLoader(schemas_dir=temp_csv_schemas_dir)
    schemas = loader.load_schemas()

    assert len(schemas) == 2
    assert "DeviceInfo" in schemas
    assert "DeviceEvents" in schemas

  def test_load_schemas_empty_directory(self, empty_schemas_dir: Path) -> None:
    """Test loading from empty directory returns empty dict."""
    loader = CSVSchemaLoader(schemas_dir=empty_schemas_dir)
    schemas = loader.load_schemas()

    assert schemas == {}

  def test_load_schemas_nonexistent_directory(self) -> None:
    """Test loading from nonexistent directory returns empty dict."""
    loader = CSVSchemaLoader(schemas_dir=Path("/nonexistent/path"))
    schemas = loader.load_schemas()

    assert schemas == {}

  def test_load_columns_file_not_found(self, temp_csv_schemas_dir: Path) -> None:
    """Test FileNotFoundError when CSV file doesn't exist."""
    loader = CSVSchemaLoader(schemas_dir=temp_csv_schemas_dir)

    with pytest.raises(FileNotFoundError):
      loader.load_columns_from_csv(temp_csv_schemas_dir / "nonexistent.csv")

  def test_load_columns_missing_columns(self) -> None:
    """Test KeyError when CSV is missing required columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
      csv_dir = Path(tmpdir)
      # Create CSV with wrong column names
      with open(csv_dir / "bad.csv", "w") as f:
        f.write("Name,DataType,Desc\n")
        f.write("Field1,string,Description\n")

      loader = CSVSchemaLoader(schemas_dir=csv_dir)

      with pytest.raises(KeyError):
        loader.load_columns_from_csv(csv_dir / "bad.csv")

  def test_schema_reference_url_generation(self, temp_csv_schemas_dir: Path) -> None:
    """Test that reference URLs are generated correctly."""
    loader = CSVSchemaLoader(
      schemas_dir=temp_csv_schemas_dir,
      reference_base_url="https://docs.example.com/tables/",
    )
    schema = loader.load_schema(temp_csv_schemas_dir / "DeviceInfo.csv")

    assert schema.reference == "https://docs.example.com/tables/deviceinfo"

  def test_get_schema_by_name(self, temp_csv_schemas_dir: Path) -> None:
    """Test getting a specific schema by name."""
    loader = CSVSchemaLoader(schemas_dir=temp_csv_schemas_dir)
    schema = loader.get_schema_by_name("DeviceEvents")

    assert schema is not None
    assert schema.table_name == "DeviceEvents"
    assert len(schema.columns) == 3

  def test_get_schema_by_name_not_found(self, temp_csv_schemas_dir: Path) -> None:
    """Test getting a nonexistent schema returns None."""
    loader = CSVSchemaLoader(schemas_dir=temp_csv_schemas_dir)
    schema = loader.get_schema_by_name("NonexistentTable")

    assert schema is None


class TestLoaderInteroperability:
  """Tests for interoperability between different loader types."""

  def test_both_loaders_produce_valid_schemas(
    self, temp_schemas_dir: Path, temp_csv_schemas_dir: Path
  ) -> None:
    """Test that both loaders produce valid TableSchema objects."""
    file_loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    csv_loader = CSVSchemaLoader(schemas_dir=temp_csv_schemas_dir)

    file_schemas = file_loader.load_schemas()
    csv_schemas = csv_loader.load_schemas()

    for schema in file_schemas.values():
      assert isinstance(schema, TableSchema)

    for schema in csv_schemas.values():
      assert isinstance(schema, TableSchema)

  def test_schema_structure_consistency(
    self, temp_schemas_dir: Path, temp_csv_schemas_dir: Path
  ) -> None:
    """Test that schemas from both loaders have consistent structure."""
    file_loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    csv_loader = CSVSchemaLoader(schemas_dir=temp_csv_schemas_dir)

    file_schema = file_loader.get_schema_by_name("DeviceInfo")
    csv_schema = csv_loader.get_schema_by_name("DeviceInfo")

    assert file_schema is not None
    assert csv_schema is not None

    # Both should have table_name
    assert file_schema.table_name == csv_schema.table_name

    # Both should have columns with required attributes
    for schema in [file_schema, csv_schema]:
      for column in schema.columns:
        assert column.name
        assert column.type
        assert column.description
