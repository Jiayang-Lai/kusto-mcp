"""Pytest fixtures for kusto-mcp tests."""

import json
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from kusto_mcp.models import Column, TableSchema


@pytest.fixture
def sample_column() -> Column:
  """Create a sample Column instance."""
  return Column(
    name="DeviceId",
    type="string",
    description="Unique identifier for the device in the service.",
  )


@pytest.fixture
def sample_columns() -> list[Column]:
  """Create a list of sample Column instances."""
  return [
    Column(
      name="DeviceId",
      type="string",
      description="Unique identifier for the device in the service.",
    ),
    Column(
      name="DeviceName",
      type="string",
      description="Fully qualified domain name (FQDN) of the device.",
    ),
    Column(
      name="IsAzureADJoined",
      type="bool",
      description="Boolean indicator of whether machine is joined to Azure AD.",
    ),
    Column(
      name="Timestamp",
      type="datetime",
      description="Date and time when the record was generated.",
    ),
  ]


@pytest.fixture
def sample_table_schema(sample_columns: list[Column]) -> TableSchema:
  """Create a sample TableSchema instance."""
  return TableSchema(
    schema_url="https://example.com/schema.json",
    table_name="DeviceInfo",
    table_description="Machine information including OS information.",
    reference="https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/deviceinfo",
    columns=sample_columns,
  )


@pytest.fixture
def temp_schemas_dir(sample_table_schema: TableSchema) -> Generator[Path, None, None]:
  """Create a temporary directory with JSON schema files."""
  with tempfile.TemporaryDirectory() as tmpdir:
    schemas_dir = Path(tmpdir)

    # Create DeviceInfo.json
    device_info_data = {
      "$schema": sample_table_schema.schema_url,
      "table_name": sample_table_schema.table_name,
      "table_description": sample_table_schema.table_description,
      "reference": sample_table_schema.reference,
      "columns": [
        {"name": c.name, "type": c.type, "description": c.description}
        for c in sample_table_schema.columns
      ],
    }
    with open(schemas_dir / "DeviceInfo.json", "w") as f:
      json.dump(device_info_data, f)

    # Create a second schema file for testing multiple schemas
    device_events_data = {
      "$schema": "https://example.com/schema.json",
      "table_name": "DeviceEvents",
      "table_description": "Device events table.",
      "reference": "https://example.com/deviceevents",
      "columns": [
        {"name": "EventId", "type": "string", "description": "Event identifier."},
        {"name": "EventType", "type": "string", "description": "Type of event."},
      ],
    }
    with open(schemas_dir / "DeviceEvents.json", "w") as f:
      json.dump(device_events_data, f)

    yield schemas_dir


@pytest.fixture
def temp_csv_schemas_dir() -> Generator[Path, None, None]:
  """Create a temporary directory with CSV schema files."""
  with tempfile.TemporaryDirectory() as tmpdir:
    schemas_dir = Path(tmpdir)

    # Create DeviceInfo.csv
    csv_content = """Column,Type,Description
DeviceId,string,Unique identifier for the device.
DeviceName,string,Fully qualified domain name of the device.
IsActive,bool,Indicates if the device is active.
"""
    with open(schemas_dir / "DeviceInfo.csv", "w") as f:
      f.write(csv_content)

    # Create DeviceEvents.csv
    csv_content2 = """Column,Type,Description
EventId,string,Unique identifier for the event.
EventType,string,Type of event that occurred.
Timestamp,datetime,Date and time of the event.
"""
    with open(schemas_dir / "DeviceEvents.csv", "w") as f:
      f.write(csv_content2)

    yield schemas_dir


@pytest.fixture
def invalid_json_schema_dir() -> Generator[Path, None, None]:
  """Create a temporary directory with invalid JSON file."""
  with tempfile.TemporaryDirectory() as tmpdir:
    schemas_dir = Path(tmpdir)
    with open(schemas_dir / "invalid.json", "w") as f:
      f.write("{ invalid json }")
    yield schemas_dir


@pytest.fixture
def empty_schemas_dir() -> Generator[Path, None, None]:
  """Create an empty temporary directory."""
  with tempfile.TemporaryDirectory() as tmpdir:
    yield Path(tmpdir)
