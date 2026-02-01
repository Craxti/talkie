# Development Environment Setup

This guide helps you set up a development environment for contributing to Talkie.

## Prerequisites

- **Python 3.8+** — [python.org](https://www.python.org/downloads/)
- **Git** — [git-scm.com](https://git-scm.com/)
- **pip** — Usually included with Python

### Verify Installation

```bash
python3 --version   # 3.8 or higher
git --version
pip --version
```

---

## Quick Setup

### 1. Clone Repository

```bash
git clone https://github.com/craxti/talkie.git
cd talkie
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create venv
python3 -m venv .venv

# Activate (Unix/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### 3. Install in Development Mode

```bash
pip install -e ".[dev]"
```

This installs:
- Talkie in editable mode (changes apply immediately)
- All dev dependencies: pytest, black, isort, mypy, mkdocs, pre-commit, etc.

### 4. Install Pre-commit Hooks

```bash
pre-commit install
```

Hooks run automatically on `git commit` (black, isort, mypy).

### 5. Verify Setup

```bash
# Run tests
pytest

# Run Talkie
talkie get https://jsonplaceholder.typicode.com/posts/1

# Build docs
mkdocs serve
```

---

## Platform-Specific Notes

### macOS

```bash
# If Python 3 not default
brew install python@3.11

# Use system Python
/opt/homebrew/bin/python3 -m venv .venv
```

### Windows

```powershell
# Create venv
py -3 -m venv .venv
.venv\Scripts\activate

# Install
pip install -e ".[dev]"
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
python3 -m venv .venv
source .venv/bin/activate
```

---

## IDE Setup

### VS Code / Cursor

1. Install Python extension
2. Select interpreter: `.venv/bin/python` (or `.venv\Scripts\python.exe` on Windows)
3. Recommended settings:
   - Format on save: enabled
   - Default formatter: Black
   - Linter: Pylint or Ruff

### PyCharm

1. **File → Open** → select `talkie` folder
2. **Configure Python interpreter** → Add → Existing → `.venv/bin/python`
3. **Mark** `talkie` as Sources Root
4. **Run → Edit Configurations** → Add pytest configuration

---

## Project Structure

```
talkie/
├── talkie/           # Main package
│   ├── cli/          # CLI commands
│   ├── core/         # HTTP client, WebSocket
│   └── utils/        # Helpers
├── tests/            # Test files
├── docs/             # Documentation
├── examples/         # Example scripts
├── pyproject.toml    # Project config
└── mkdocs.yml        # Docs config
```

---

## Common Tasks

### Run Tests

```bash
pytest                    # All tests
pytest tests/test_cli.py  # Specific file
pytest -v                 # Verbose
pytest --cov=talkie       # With coverage
```

### Format Code

```bash
black talkie tests
isort talkie tests
```

### Type Check

```bash
mypy talkie
```

### Lint

```bash
pylint talkie
```

### Build Documentation

```bash
mkdocs build
mkdocs serve   # Preview at http://127.0.0.1:8000
```

### Regenerate Demo GIF

```bash
python3 scripts/create_demo_gif.py
```

---

## Troubleshooting

### ModuleNotFoundError

Ensure you're in the project root and venv is activated:
```bash
cd /path/to/talkie
source .venv/bin/activate
pip install -e ".[dev]"
```

### Pre-commit Fails

Run manually to see errors:
```bash
pre-commit run --all-files
```

### Tests Fail

```bash
# Ensure dev deps installed
pip install -e ".[dev]" --force-reinstall

# Run with verbose output
pytest -vv --tb=long
```

### SSL Errors (pip install)

```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -e ".[dev]"
```
