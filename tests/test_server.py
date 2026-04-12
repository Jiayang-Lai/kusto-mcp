"""Unit tests for kusto_mcp.server module."""

import json
from pathlib import Path

import pytest

# Import server module components
# Note: We need to reload the module for each test to reset global state
import kusto_mcp.server as server_module
from kusto_mcp.loaders import FileSchemaLoader


@pytest.fixture(autouse=True)
def reset_server_state() -> None:
  """Reset the server module's global state before each test."""
  # Reset global state in server module
  server_module._schemas = None
  server_module._loader = None


class TestConfigureLoader:
  """Tests for the configure_loader function."""

  def test_configure_loader_success(self, temp_schemas_dir: Path) -> None:
    """Test configuring a custom loader before schema access."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    server_module.configure_loader(loader)

    assert server_module._loader is loader

  def test_configure_loader_after_schemas_loaded_raises(
    self, temp_schemas_dir: Path
  ) -> None:
    """Test that configuring loader after schemas loaded raises RuntimeError."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    server_module.configure_loader(loader)

    # Access schemas to trigger loading
    _ = server_module._get_schemas()

    # Try to configure again should raise
    with pytest.raises(RuntimeError) as exc_info:
      server_module.configure_loader(loader)

    assert "Cannot configure loader after schemas have been loaded" in str(
      exc_info.value
    )

  def test_configure_loader_multiple_times_before_load(
    self, temp_schemas_dir: Path
  ) -> None:
    """Test configuring loader multiple times before any schema access."""
    loader1 = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    loader2 = FileSchemaLoader(schemas_dir=temp_schemas_dir)

    server_module.configure_loader(loader1)
    server_module.configure_loader(loader2)

    assert server_module._loader is loader2


class TestGetSchemas:
  """Tests for the _get_schemas internal function."""

  def test_get_schemas_lazy_loads(self, temp_schemas_dir: Path) -> None:
    """Test that schemas are lazy loaded on first access."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    server_module.configure_loader(loader)

    assert server_module._schemas is None

    schemas = server_module._get_schemas()

    assert server_module._schemas is not None
    assert schemas is server_module._schemas

  def test_get_schemas_uses_default_loader(self) -> None:
    """Test that default FileSchemaLoader is used if none configured."""
    # Don't configure any loader
    schemas = server_module._get_schemas()

    assert server_module._loader is not None
    assert isinstance(server_module._loader, FileSchemaLoader)
    assert isinstance(schemas, dict)

  def test_get_schemas_returns_same_instance(self, temp_schemas_dir: Path) -> None:
    """Test that repeated calls return the same cached instance."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    server_module.configure_loader(loader)

    schemas1 = server_module._get_schemas()
    schemas2 = server_module._get_schemas()

    assert schemas1 is schemas2


class TestListTablesTool:
  """Tests for the list_tables MCP tool."""

  def test_list_tables_returns_json(self, temp_schemas_dir: Path) -> None:
    """Test that list_tables returns valid JSON."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    server_module.configure_loader(loader)

    result = server_module.list_tables()

    # Should be valid JSON
    tables = json.loads(result)
    assert isinstance(tables, list)

  def test_list_tables_content(self, temp_schemas_dir: Path) -> None:
    """Test that list_tables returns correct table information."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    server_module.configure_loader(loader)

    result = server_module.list_tables()
    tables = json.loads(result)

    assert len(tables) == 2

    # Check structure
    for table in tables:
      assert "name" in table
      assert "description" in table

    # Check content
    table_names = {t["name"] for t in tables}
    assert "DeviceInfo" in table_names
    assert "DeviceEvents" in table_names

  def test_list_tables_empty_schemas(self, empty_schemas_dir: Path) -> None:
    """Test list_tables with no schemas available."""
    loader = FileSchemaLoader(schemas_dir=empty_schemas_dir)
    server_module.configure_loader(loader)

    result = server_module.list_tables()
    tables = json.loads(result)

    assert tables == []


class TestGetTableSchemaTool:
  """Tests for the get_table_schema MCP tool."""

  def test_get_table_schema_success(self, temp_schemas_dir: Path) -> None:
    """Test getting a valid table schema."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    server_module.configure_loader(loader)

    result = server_module.get_table_schema("DeviceInfo")

    # Should be valid JSON
    schema_data = json.loads(result)
    assert schema_data["table_name"] == "DeviceInfo"
    assert "$schema" in schema_data  # Uses alias in output
    assert "columns" in schema_data

  def test_get_table_schema_not_found(self, temp_schemas_dir: Path) -> None:
    """Test getting a nonexistent table raises KeyError."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    server_module.configure_loader(loader)

    with pytest.raises(KeyError) as exc_info:
      server_module.get_table_schema("NonexistentTable")

    assert "NonexistentTable" in str(exc_info.value)
    assert "not found" in str(exc_info.value)

  def test_get_table_schema_shows_available_tables(
    self, temp_schemas_dir: Path
  ) -> None:
    """Test that error message includes available table names."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    server_module.configure_loader(loader)

    with pytest.raises(KeyError) as exc_info:
      server_module.get_table_schema("BadTable")

    error_msg = str(exc_info.value)
    assert "DeviceInfo" in error_msg or "DeviceEvents" in error_msg

  def test_get_table_schema_columns_structure(self, temp_schemas_dir: Path) -> None:
    """Test that schema columns have correct structure."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    server_module.configure_loader(loader)

    result = server_module.get_table_schema("DeviceInfo")
    schema_data = json.loads(result)

    columns = schema_data["columns"]
    assert len(columns) > 0

    for column in columns:
      assert "name" in column
      assert "type" in column
      assert "description" in column

  def test_get_table_schema_case_sensitive(self, temp_schemas_dir: Path) -> None:
    """Test that table name lookup is case-sensitive."""
    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    server_module.configure_loader(loader)

    # Correct case works
    result = server_module.get_table_schema("DeviceInfo")
    assert "DeviceInfo" in result

    # Wrong case raises error
    with pytest.raises(KeyError):
      server_module.get_table_schema("deviceinfo")

    with pytest.raises(KeyError):
      server_module.get_table_schema("DEVICEINFO")


class TestMCPServerIntegration:
  """Integration tests for the MCP server."""

  def test_mcp_server_instance_exists(self) -> None:
    """Test that the MCP server instance is created."""
    assert server_module.mcp is not None
    assert server_module.mcp.name == "Kusto MCP"

  def test_tools_are_registered(self) -> None:
    """Test that tools are registered with the MCP server."""
    # The tools should be callable
    assert callable(server_module.list_tables)
    assert callable(server_module.get_table_schema)


class TestThreadSafety:
  """Tests for thread safety of server module."""

  def test_configure_loader_thread_safe(self, temp_schemas_dir: Path) -> None:
    """Test that configure_loader uses locking."""
    import threading

    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    results: list[Exception | None] = []

    def configure() -> None:
      try:
        server_module.configure_loader(loader)
        results.append(None)
      except Exception as e:
        results.append(e)

    threads = [threading.Thread(target=configure) for _ in range(5)]
    for t in threads:
      t.start()
    for t in threads:
      t.join()

    # All should succeed (before schemas loaded)
    assert all(r is None for r in results)

  def test_get_schemas_thread_safe(self, temp_schemas_dir: Path) -> None:
    """Test that _get_schemas uses double-checked locking."""
    import threading

    loader = FileSchemaLoader(schemas_dir=temp_schemas_dir)
    server_module.configure_loader(loader)

    results: list[dict] = []

    def get_schemas() -> None:
      schemas = server_module._get_schemas()
      results.append(schemas)

    threads = [threading.Thread(target=get_schemas) for _ in range(10)]
    for t in threads:
      t.start()
    for t in threads:
      t.join()

    # All results should be the same instance
    assert len(results) == 10
    first = results[0]
    assert all(r is first for r in results)
