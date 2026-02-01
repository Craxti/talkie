# Talkie

A convenient command-line HTTP client for interacting with APIs and web services. Talkie makes working with HTTP in the terminal simple and human-friendly thanks to intuitive syntax and beautiful formatted output.

<p align="center">
  <img src="docs/images/logo.svg" alt="Talkie Logo" width="180" height="180" />
</p>

[![PyPI version](https://img.shields.io/pypi/v/talkie.svg)](https://pypi.org/project/talkie/)
[![Python 3.8+](https://img.shields.io/pypi/pyversions/talkie.svg)](https://pypi.org/project/talkie/)
[![Tests](https://github.com/craxti/talkie/actions/workflows/tests.yml/badge.svg)](https://github.com/craxti/talkie/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/craxti/talkie/graph/badge.svg)](https://codecov.io/gh/craxti/talkie)
[![Pylint](https://github.com/craxti/talkie/actions/workflows/pylint.yml/badge.svg)](https://github.com/craxti/talkie/actions/workflows/pylint.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Quick Start

```bash
# Install
pip install talkie

# Make your first request
talkie get https://jsonplaceholder.typicode.com/posts/1
```

<details>
<summary>📺 See demo output</summary>

```
$ talkie get https://jsonplaceholder.typicode.com/posts/1

HTTP/1.1 200 OK
Content-Type: application/json

{
  "userId": 1,
  "id": 1,
  "title": "sunt aut facere repellat provident occasi...",
  "body": "quia et suscipit\nsuscipit recusandae consequuntur..."
}
```

</details>

<p align="center">
  <img src="docs/images/demo.gif" alt="Talkie demo" width="700" />
</p>

## Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Why Talkie?](#why-talkie)
- [Comparison with Alternatives](#comparison-with-alternatives)
- [Installation](#installation)
- [Usage](#usage)
  - [Basic Requests](#basic-requests)
  - [Headers and Parameters](#headers-and-parameters)
  - [Output and Formatting](#output-and-formatting)
  - [Curl Command Generation](#curl-command-generation)
  - [OpenAPI Inspection](#openapi-inspection)
  - [File Formatting](#file-formatting)
  - [WebSocket](#websocket)
  - [GraphQL Requests](#graphql-requests)
  - [Request History](#request-history)
- [Configuration Management](#configuration-management)
  - [Configuration File](#configuration-file)
  - [Environment Management](#environment-management)
  - [Configuration Examples](#configuration-examples)
- [Development](#development)
  - [Requirements](#requirements)
  - [Project Structure](#project-structure)
  - [Running Tests](#running-tests)
  - [Pre-commit Hooks](#pre-commit-hooks)
  - [Documentation Site](#documentation-site)
  - [API Documentation](#api-documentation)
- [FAQ](#faq)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Contributing](#contributing)

## Features

- 🚀 **Intuitive syntax** for working with HTTP requests
- 🌈 **Beautiful colored output** with syntax highlighting
- 💡 **Automatic content type detection** (JSON, XML, HTML)
- 🔍 **OpenAPI specification inspection** for convenient API work
- 🔄 **Curl command generation** for compatibility
- 📝 **Automatic data formatting** (JSON, XML, HTML, Markdown)
- 🌐 **Environment support** for working with different APIs
- 🔐 **Save and reuse** headers and tokens
- 💾 **Save responses** to files
- 🧰 **Full support** for all HTTP methods
- 🌐 **WebSocket connections** for bidirectional communication
- 📊 **GraphQL requests** for working with GraphQL APIs
- 📜 **Request history** for reuse and analysis
- ⚡ **Parallel request execution** for improved performance

## Why Talkie?

Talkie combines the best of both worlds: the simplicity of HTTPie and the power of curl, while adding features that neither offers out of the box.

**When to choose Talkie over HTTPie:**
- You need **GraphQL** — Talkie has a dedicated `graphql` command with query files and variables
- You work with **WebSocket** — built-in `ws` command, no extra tools
- You explore **OpenAPI** specs — inspect endpoints, schemas, and generate examples
- You run **parallel requests** — batch API calls with configurable concurrency
- You want **searchable history** — find, repeat, and export past requests

**When to choose Talkie over curl:**
- You prefer **human-friendly syntax** — `talkie post /users name=John` instead of `-d '{"name":"John"}'`
- You want **colored, formatted output** — JSON/XML/HTML with syntax highlighting
- You need **environments** — switch between dev/staging/prod with one config
- You don't want to remember curl flags — intuitive `-H`, `-q`, `-o` options

### Unique Features

| Feature | Description |
|---------|-------------|
| **GraphQL** | Native `talkie graphql` with query files, variables, and introspection |
| **WebSocket** | `talkie ws` for real-time connections, no separate client needed |
| **OpenAPI** | Inspect specs, list endpoints, generate request examples |
| **Parallel requests** | `talkie parallel` for batch execution with concurrency control |
| **Request history** | Search, repeat, export/import — full audit trail of your API work |

## Comparison with Alternatives

| Feature | Talkie | HTTPie | curl | wget |
|---------|:------:|:------:|:----:|:----:|
| Intuitive syntax | ✅ | ✅ | ❌ | ⚠️ |
| Colored output | ✅ | ✅ | ❌ | ❌ |
| JSON/XML formatting | ✅ | ✅ | ❌ | ❌ |
| **GraphQL** | ✅ | ❌ | ⚠️ | ❌ |
| **WebSocket** | ✅ | ❌ | ✅ | ❌ |
| **OpenAPI inspection** | ✅ | ❌ | ❌ | ❌ |
| **Parallel requests** | ✅ | ❌ | ❌ | ⚠️ |
| **Request history** | ✅ | ⚠️ | ❌ | ❌ |
| Environment config | ✅ | ⚠️ | ❌ | ❌ |
| Curl command generation | ✅ | ⚠️ | — | — |
| Pre-installed | ❌ | ❌ | ✅ | ✅ |
| Python API | ✅ | ✅ | ❌ | ❌ |

*Legend: ✅ Yes | ⚠️ Partial/Manual | ❌ No | — N/A*

## Installation

### From PyPI

```bash
pip install talkie
```

### From source code

```bash
git clone https://github.com/craxti/talkie.git
cd talkie
pip install -e .
```

## Usage

### Basic Requests

```bash
# GET request
talkie get https://api.example.com/users

# POST request with JSON data (automatic type detection)
talkie post https://api.example.com/users name=John age:=30 is_admin:=true

# PUT request
talkie put https://api.example.com/users/1 name=Peter

# DELETE request
talkie delete https://api.example.com/users/1
```

### Headers and Parameters

```bash
# Adding headers
talkie get https://api.example.com/users \
  -H "Authorization: Bearer token123" \
  -H "Accept: application/json"

# Query parameters
talkie get https://api.example.com/users -q "page=1" -q "limit=10"

# Save response to file
talkie get https://api.example.com/users -o users.json
```

### Output and Formatting

```bash
# Verbose output
talkie get https://api.example.com/users -v

# JSON only
talkie get https://api.example.com/users --json

# Headers only
talkie get https://api.example.com/users --headers

# Response formatting
talkie get https://api.example.com/users --format json
talkie get https://api.example.com/users -f xml
```

### Curl Command Generation

```bash
# Generate curl command for request
talkie curl https://api.example.com/users -H "Authorization: Bearer token123"

# Add curl command to regular request
talkie get https://api.example.com/users --curl

# Configure curl parameters
talkie curl https://api.example.com/users -X POST -d "name=John" -d "age:=30" -v -k
```

### OpenAPI Inspection

```bash
# Inspect OpenAPI specification from URL
talkie openapi https://api.example.com/openapi.json

# Inspect local specification file
talkie openapi ./openapi.yaml

# Show only endpoints
talkie openapi https://api.example.com/openapi.json --endpoints

# Generate request examples
talkie openapi https://api.example.com/openapi.json --examples
```

### File Formatting

```bash
# Format JSON file
talkie format data.json

# Format and save to file
talkie format data.json -o formatted.json

# Format with specific type
talkie format data.txt -t json
```

### WebSocket

```bash
# Connect to WebSocket server
talkie ws wss://echo.websocket.org

# Send message
talkie ws wss://echo.websocket.org --send "Hello"

# Connect with headers
talkie ws wss://api.example.com/ws \
  -H "Authorization: Bearer token123"
```

### GraphQL Requests

```bash
# Simple query
talkie graphql https://api.example.com/graphql \
  -q "query { users { id name } }"

# Query from file
talkie graphql https://api.example.com/graphql -f query.graphql

# Query with variables
talkie graphql https://api.example.com/graphql \
  -f query.graphql -v id=123 -v limit=10
```

### Request History

```bash
# Show history
talkie history list

# Show last 10 requests
talkie history list --limit 10

# Search history
talkie history search --method GET --url users

# Repeat request from history
talkie history repeat 1a2b3c4d

# Search in history
talkie history search --method GET --url users

# Export history to file
talkie history export history.json

# Import history from file
talkie history import history.json
```

### Parallel Request Execution

```bash
# Execute requests from file
talkie parallel -f requests.txt

# File with requests (requests.txt) has format:
# GET https://api.example.com/users/1
# GET https://api.example.com/users/2
# POST https://api.example.com/users name=John

# Execute multiple requests with parallelism limit
talkie parallel -f requests.txt --concurrency 5

# Use delay between requests
talkie parallel -f requests.txt --delay 0.5

# Save results to separate files
talkie parallel -f requests.txt --output-dir ./results

# Execute multiple requests to one URL
talkie parallel -X GET -u "/users/1" -u "/users/2" -u "/posts/1" -b "https://api.example.com"
```

## Configuration Management

### Configuration File

Talkie uses `~/.talkie/config.json` file for storing settings. The file is created automatically on first run.

You can create the file manually:

```bash
mkdir -p ~/.talkie
cat > ~/.talkie/config.json << EOF
{
  "default_headers": {
    "User-Agent": "Talkie/0.1.0",
    "Accept": "application/json"
  },
  "environments": {
    "dev": {
      "name": "dev",
      "base_url": "https://dev-api.example.com",
      "default_headers": {
        "Authorization": "Bearer dev-token"
      }
    },
    "prod": {
      "name": "prod",
      "base_url": "https://prod-api.example.com",
      "default_headers": {
        "Authorization": "Bearer prod-token"
      }
    }
  },
  "active_environment": "dev"
}
EOF
```

Configuration file location can be changed using `TALKIE_CONFIG_DIR` environment variable.

### Environment Management

Environments allow storing settings for different APIs and quickly switching between them.

Example of using environment:

```bash
# Using base URL from active environment
talkie get /users

# Equivalent to (if active environment is dev)
talkie get https://dev-api.example.com/users
```

### Configuration Examples

#### Multiple Headers for All Requests

```json
{
  "default_headers": {
    "User-Agent": "Talkie/0.1.0",
    "Accept": "application/json",
    "X-API-Key": "your-api-key"
  }
}
```

#### Multiple Environment Setup

```json
{
  "environments": {
    "github": {
      "name": "github",
      "base_url": "https://api.github.com",
      "default_headers": {
        "Authorization": "token ghp_xxxxxxxxxxxx"
      }
    },
    "gitlab": {
      "name": "gitlab",
      "base_url": "https://gitlab.com/api/v4",
      "default_headers": {
        "PRIVATE-TOKEN": "glpat-xxxxxxxxxxxx"
      }
    }
  },
  "active_environment": "github"
}
```

## Development

### Requirements

- Python 3.8+
- httpx
- typer
- rich
- pydantic
- pyyaml
- openapi-spec-validator
- pygments
- xmltodict
- html2text
- websockets

### Project Structure

```
talkie/
├── __init__.py          # Package
├── __main__.py          # Entry point
├── cli/                 # Command line interface
│   ├── __init__.py
│   └── main.py          # Command definitions
├── core/                # Application core
│   ├── __init__.py
│   ├── client.py        # HTTP client
│   ├── request_builder.py
│   ├── response_formatter.py
│   └── websocket_client.py  # WebSocket client
└── utils/               # Helper modules
    ├── __init__.py
    ├── config.py        # Configuration management
    ├── formatter.py     # Data formatting
    ├── curl_generator.py
    ├── openapi.py
    ├── graphql.py       # GraphQL support
    ├── history.py       # Request history
    ├── colors.py
    └── logger.py
```

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run tests for specific module
pytest tests/test_formatter.py

# Run with coverage
pytest --cov=talkie
```

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
# Hooks run automatically on git commit (black, isort, mypy)
```

### Documentation Site

```bash
pip install -e ".[dev]"
mkdocs serve
# Open http://127.0.0.1:8000
```

### API Documentation

Documentation is available in the `docs/` folder and via `mkdocs serve`:

- [CLI Reference](docs/cli_reference.md) — Complete command-line options
- [API Reference](docs/api_reference.md) — Python API
- [Architecture](docs/architecture.md) — System design
- [Development Setup](docs/development_setup.md) — Dev environment
- [Development Tools](docs/development_tools.md) — Pre-commit, pytest, etc.

It contains detailed description of all Talkie API components:
- HTTP client and request builder
- WebSocket client
- Utilities for formatting and working with various formats
- GraphQL request interface
- Components for storing and managing request history

## FAQ

### How to save response to file?

Use `-o` or `--output` option:

```bash
talkie get https://api.example.com/data -o response.json
```

### How to use OAuth token?

Add Authorization header:

```bash
talkie get https://api.example.com/profile -H "Authorization: Bearer YOUR_TOKEN"
```

Or save it in configuration:

```json
{
  "environments": {
    "myapi": {
      "base_url": "https://api.example.com",
      "default_headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  },
  "active_environment": "myapi"
}
```

### How to work with WebSocket in async scenarios?

Talkie provides Python API for working with WebSocket:

```python
import asyncio
from talkie.core.websocket_client import WebSocketClient

async def main():
    client = WebSocketClient("wss://echo.websocket.org")
    await client.connect()
    await client.send("Hello")
    response = await client.receive()
    print(f"Received: {response.data}")
    await client.disconnect()

asyncio.run(main())
```

### How to execute complex GraphQL query?

Save query to file and pass it to command:

```bash
talkie graphql https://api.example.com/graphql -f complex_query.graphql -v id=123 -v limit=10
```

## Troubleshooting

### SSL certificate verification failed

If you get `SSLError` or certificate errors when connecting to HTTPS:

```bash
# For development only — disable SSL verification (not recommended for production)
talkie get https://api.example.com --insecure
```

### Command not found: talkie

Ensure Talkie is installed and in your PATH:

```bash
pip install talkie
# Or with user install:
pip install --user talkie
# Verify:
which talkie
```

### Colors not displaying in terminal

Some terminals don't support colors. Try:

```bash
# Force colored output
export FORCE_COLOR=1
talkie get https://api.example.com/users

# Or disable colors
talkie get https://api.example.com/users --no-color
```

### Config file not found

Talkie uses `~/.talkie/config.json` by default. Override with:

```bash
export TALKIE_CONFIG_DIR=/path/to/your/config
talkie get /users
```

### Timeout errors

Increase timeout for slow APIs:

```bash
talkie get https://api.example.com/slow-endpoint --timeout 60
```

## License

MIT

## Contributing

Contributions are welcome! Please create issues and pull requests on GitHub.

1. Fork the repository
2. Create a branch with your changes
3. Submit a pull request

Code guidelines:
- Use black for code formatting
- Add type hints
- Write tests for new functionality 