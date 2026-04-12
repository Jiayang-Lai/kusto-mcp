.PHONY: help chore lint lint-fix scan sbom vuln format test test-multi

help: ## Show help message
	@grep -E '^[a-zA-Z0-9_%\-]+:[[:space:]]*##' $(MAKEFILE_LIST) | sed 's/:.*##[[:space:]]*/: /'

lint: ## Run ruff linter on the scripts
	ruff check

lint-fix: ## Run ruff linter with auto-fix on the scripts
	ruff check --fix

format: ## Run all formatting chores (lint-fix)
	@echo "Running all formatting chores..."
	ruff format

chore: format lint-fix ## Run all chores (format, lint-fix)

sbom: ## Generate Software Bill of Materials (SBOM) using Syft
	@echo "Generating SBOM using Syft..."
	syft scan uv.lock -o cyclonedx-json=sbom.json

scan: ## Run grype security scan on the SBOM file (requires sbom.json to be present)
	@echo "Running grype security scan on the SBOM file..."
	grype sbom:sbom.json -v --fail-on medium

vuln: sbom scan ## Generate SBOM and run vulnerability scan

test: ## Run tests for the current Python version
	@echo "Running tests for the current Python version..."
	uv run pytest

test-multi: ## Run tests
	@echo "Running tests..."
	@echo "Running tests for Python 3.12, 3.13, and 3.14..."
	@echo "Running pytest for Python 3.12..."
	uv run --python 3.12 pytest
	@echo "Running pytest for Python 3.13..."
	uv run --python 3.13 pytest
	@echo "Running pytest for Python 3.14..."
	uv run --python 3.14 pytest


