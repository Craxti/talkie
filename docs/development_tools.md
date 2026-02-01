# Development Tools

Documentation for tools used in Talkie development.

---

## Pre-commit

Pre-commit runs checks automatically before each commit.

### Setup

```bash
pip install pre-commit
pre-commit install
```

### Configuration

File: `.pre-commit-config.yaml`

### Hooks

| Hook | Purpose |
|------|---------|
| **pre-commit-hooks** | trailing-whitespace, end-of-file-fixer, check-yaml, check-json, check-toml |
| **black** | Code formatting |
| **isort** | Import sorting |
| **mypy** | Type checking |

### Commands

```bash
# Run all hooks on staged files
git commit -m "message"   # Runs automatically

# Run on all files
pre-commit run --all-files

# Skip hooks (not recommended)
git commit --no-verify -m "message"

# Update hook versions
pre-commit autoupdate
```

---

## Black

Code formatter — enforces consistent style.

### Configuration

`pyproject.toml`:
```toml
[tool.black]
line-length = 88
target-version = ["py38"]
```

### Usage

```bash
# Format specific files
black talkie/cli/main.py

# Format directory
black talkie tests

# Check without modifying
black --check talkie
```

### Integration

- Runs in pre-commit
- VS Code: set Black as default formatter
- Format on save: recommended

---

## isort

Import sorter — organizes imports alphabetically.

### Configuration

`pyproject.toml`:
```toml
[tool.isort]
profile = "black"
line_length = 88
```

### Usage

```bash
# Sort imports
isort talkie tests

# Check only
isort --check-only talkie
```

---

## mypy

Static type checker.

### Configuration

`pyproject.toml`:
```toml
[tool.mypy]
python_version = "3.8"
warn_return_any = true
disallow_untyped_defs = true
```

### Usage

```bash
# Check package
mypy talkie

# Check with config
mypy --config-file pyproject.toml talkie

# Ignore missing imports
mypy --ignore-missing-imports talkie
```

---

## pytest

Test framework.

### Configuration

`pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "integration: marks tests as integration tests",
    "slow: marks tests as slow running",
]
asyncio_mode = "auto"
```

### Usage

```bash
# Run all tests
pytest

# Verbose
pytest -v

# Specific file
pytest tests/test_cli.py

# Specific test
pytest tests/test_cli.py::test_something

# With coverage
pytest --cov=talkie --cov-report=html

# Skip slow tests
pytest -m "not slow"
```

### Markers

- `@pytest.mark.integration` — Integration tests
- `@pytest.mark.slow` — Slow tests
- `@pytest.mark.asyncio` — Async tests

---

## Pylint

Code linter — finds bugs and style issues.

### Configuration

`pyproject.toml` — see `[tool.pylint.*]` sections.

### Usage

```bash
# Lint package
pylint talkie

# Lint specific file
pylint talkie/cli/main.py

# Generate report
pylint talkie --output-format=text > pylint_report.txt
```

### CI

Pylint runs in GitHub Actions (`.github/workflows/pylint.yml`).

---

## MkDocs

Documentation generator.

### Configuration

`mkdocs.yml`

### Usage

```bash
# Install
pip install mkdocs mkdocs-material

# Serve (live preview)
mkdocs serve
# Open http://127.0.0.1:8000

# Build static site
mkdocs build
# Output in site/
```

### Structure

```
docs/
├── index.md
├── usage.md
├── api_reference.md
├── cli_reference.md
├── architecture.md
├── development_setup.md
├── development_tools.md
├── video_tutorials.md
└── testing.md
```

---

## Coverage

Test coverage measurement.

### Configuration

`pyproject.toml`:
```toml
[tool.coverage.run]
source = ["talkie"]
branch = true

[tool.coverage.report]
exclude_lines = [...]
show_missing = true
```

### Usage

```bash
# Run with coverage
pytest --cov=talkie

# HTML report
pytest --cov=talkie --cov-report=html
# Open htmlcov/index.html

# XML (for CI/Codecov)
pytest --cov=talkie --cov-report=xml
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Format code | `black talkie tests && isort talkie tests` |
| Type check | `mypy talkie` |
| Lint | `pylint talkie` |
| Test | `pytest` |
| Test + coverage | `pytest --cov=talkie` |
| Docs | `mkdocs serve` |
| All checks | `pre-commit run --all-files` |
