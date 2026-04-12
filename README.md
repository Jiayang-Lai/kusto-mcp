# Introduction

**Kusto MCP** is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that exposes Kusto table schemas as tools for AI agents and LLM applications.

## What it does

This server allows AI assistants to discover and understand Kusto log table structures by providing:

- **`list_tables`** — A tool that returns all available tables with their descriptions
- **`get_table_schema(table_name)`** — A tool that returns the full schema (columns, types, descriptions) for any specific table

## Why it's useful

When writing KQL (Kusto Query Language) queries against Kusto logs, knowing the exact column names and types is essential. This MCP server gives AI agents direct access to schema information, enabling them to generate accurate queries without hallucinating column names.

## Quick Start

### Installation

```bash
# Using uv (recommended)
uv add kusto-mcp

# Using pip
pip install kusto-mcp
```

### Adding custom schemas

Place your table schema JSON files in the `samples/schemas/` directory relative to where your invocation of the server occurs. Each file should follow the schema format defined in `schemas/table.json`.

### Running the server

```python
from kusto_mcp.server import mcp

mcp.run()
```

#### Implementing a custom loader

To load schemas from other sources (API, database, etc.), subclass `SchemaLoader`:

```python
from kusto_mcp.loaders import SchemaLoader
from kusto_mcp.models import TableSchema, Column

class ApiSchemaLoader(SchemaLoader):
  def __init__(self, api_url: str):
    self.api_url = api_url

  def load_schemas(self) -> dict[str, TableSchema]:
    # Fetch schemas from your API
    response = requests.get(f"{self.api_url}/schemas")
    schemas = {}
    for data in response.json():
      schema = TableSchema.model_validate(data)
      schemas[schema.table_name] = schema
    return schemas
```

#### Configuring the loader for MCP

To use a custom loader with the MCP server, call `configure_loader()` before starting:

```python
from kusto_mcp.server import mcp, configure_loader
from your_module import ApiSchemaLoader

# Configure custom loader before server starts
configure_loader(ApiSchemaLoader("https://api.example.com"))

# Start the server
mcp.run()
```

**Note:** `configure_loader()` must be called before any schema access. If not configured, the server defaults to `FileSchemaLoader`.

## Architecture

The project uses an extensible loader pattern via Python's ABC (Abstract Base Class), allowing schemas to be loaded from various sources:

- **`FileSchemaLoader`** — Loads schemas from local JSON files (default)
- **`CSVSchemaLoader`** — Loads schemas from CSV files; use this when your table metadata is maintained in spreadsheet/tabular form rather than per-table JSON documents
- Custom loaders can be implemented to fetch schemas from APIs, databases, or other sources

## SBOM and CVE Scanning

This project uses [Syft](https://github.com/anchore/syft) for generating Software Bill of Materials (SBOM) and [Grype](https://github.com/anchore/grype) for vulnerability scanning.

### Generate SBOM

```bash
# Using Makefile
make sbom

# Or manually
syft scan uv.lock -o cyclonedx-json=sbom.json
```

### Scan for CVE

```bash
# Using Makefile
make scan

# Or manually
grype sbom:sbom.json -v
```

### Full Vulnerability Workflow

```bash
# Generate SBOM and scan in one step
make vuln
```

# Functional Requirements

- [X] Read from schema file to list available table for agent.
- [X] Expose a list of available tables as MCP tool (currently just load from `samples/schemas`).
- [X] Expose each table schema as an MCP tool.
- [X] Use ABC so that the loading of schemas can be flexible.

# Non-functional Requirements

- [X] Use Pydantic to convert content from schema files to Pydantic objects.

# To-dos

This section lists out the to-dos for the project.

- [ ] Add `strip_whitespace` and `min_length` [arguments](https://pydantic.dev/docs/validation/2.1/usage/types/string_types/#constrained-types) to the `TableSchema` so that edge cases like empty fields are handled robustly.
- [ ] Add `$schema` as one of the field requirement in `table.json`.
- [ ] Ads GitHub action to publish package to PyPI.
