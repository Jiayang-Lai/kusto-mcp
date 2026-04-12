"""Convert CSV schema files to JSON schema files.

Some fields are not included in the CSV
and are filled with default values or placeholders.
"""

import argparse
import json
from pathlib import Path

from kusto_mcp import CSVSchemaLoader

# Configure paths
CSV_DIR = Path("samples/schemas_csv")
JSON_DIR = Path("samples/schemas")

# Schema URL to use in output JSON files
SCHEMA_URL = "https://github.com/Jiayang-Lai/100-Days-of-KQL/raw/refs/heads/main/schemas/files/table.json"


def convert_csv_to_json(
  csv_file: Path, output_dir: Path, overwrite: bool = False, interactive: bool = False
) -> Path | None:
  """Convert a single CSV schema file to JSON.

  Args:
    csv_file: Path to the CSV file.
    output_dir: Directory to write the JSON file.
    overwrite: If True, overwrite existing JSON files. If False, skip them.
    interactive: If True, prompt for confirmation before overwriting.

  Returns:
    Path to the created JSON file, or None if skipped.
  """
  loader = CSVSchemaLoader(
    schema_url=SCHEMA_URL,
    reference_base_url="https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/",
  )

  schema = loader.load_schema(csv_file)

  # Create output JSON file
  output_file = output_dir / f"{schema.table_name}.json"

  # Check if file exists
  if output_file.exists():
    if interactive:
      response = input(f"  Overwrite {output_file.name}? [y/N] ").strip().lower()
      if response != "y":
        return None
    elif not overwrite:
      return None

  output_dir.mkdir(parents=True, exist_ok=True)

  # Write JSON with pretty formatting
  with open(output_file, "w", encoding="utf-8") as f:
    json.dump(
      json.loads(schema.model_dump_json(by_alias=True)),
      f,
      indent=2,
      ensure_ascii=False,
    )

  return output_file


def parse_args() -> argparse.Namespace:
  """Parse command line arguments."""
  parser = argparse.ArgumentParser(
    description="Convert CSV schema files to JSON schema files."
  )
  parser.add_argument(
    "-o",
    "--overwrite",
    action="store_true",
    help="Overwrite existing JSON schema files (default: skip existing files)",
  )
  parser.add_argument(
    "-i",
    "--interactive",
    action="store_true",
    help="Prompt for confirmation before overwriting each existing file",
  )
  parser.add_argument(
    "--input-dir",
    type=Path,
    default=CSV_DIR,
    help=f"Directory containing CSV schema files (default: {CSV_DIR})",
  )
  parser.add_argument(
    "--output-dir",
    type=Path,
    default=JSON_DIR,
    help=f"Directory to write JSON schema files (default: {JSON_DIR})",
  )
  return parser.parse_args()


def main() -> None:
  """Convert all CSV schema files to JSON."""
  args = parse_args()

  input_dir = args.input_dir
  output_dir = args.output_dir

  if not input_dir.exists():
    print(f"CSV directory not found: {input_dir}")
    return

  csv_files = list(input_dir.glob("*.csv"))

  if not csv_files:
    print(f"No CSV files found in {input_dir}")
    return

  print(f"Found {len(csv_files)} CSV file(s) to convert")

  exclude_tables = {
    # "DeviceProcessEvents",
    # "DeviceNetworkEvents",
    # "DeviceFileEvents",
    # "DeviceEvents",
  }

  for csv_file in csv_files:
    if csv_file.stem in exclude_tables:
      print(f"  Skipping excluded table: {csv_file.name}")
      continue
    result = convert_csv_to_json(
      csv_file, output_dir, overwrite=args.overwrite, interactive=args.interactive
    )
    if result is None:
      print(f"  Skipping (already exists): {csv_file.name}")
    else:
      print(f"  {csv_file.name} -> {result.name}")

  print("Done!")


if __name__ == "__main__":
  main()
