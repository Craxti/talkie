# Talkie Testing Guide

## Contents
1. [Introduction](#introduction)
2. [Setting Up a Test Environment](#setting-up-a-test-environment)
3. [Test Structure](#test-structure)
4. [Running Tests](#running-tests)
5. [Mock Server](#mock-server)
6. [Writing Tests](#writing-tests)
7. [Known Issues](#known-issues)

## Introduction

Talkie uses `pytest` for unit and integration testing. The tests cover all the main components of the application:
- CLI interface
- Building HTTP requests
- Processing responses
- Working with OpenAPI specifications
- Integration tests with a mock server

## Setting up the test environment

1. Install dependencies for testing:
```bash
pip install pytest pytest-httpserver pytest-asyncio pytest-mock pytest-cov
```

2. Make sure that you have installed all the main dependencies of the project:
```bash
pip install -r requirements.txt
```

## Test structure

The tests are organized by modules:
- `tests/test_cli.py` - CLI interface tests
- `tests/test_request_builder.py` - request builder tests
- `tests/test_integration.py` - integration tests
- `tests/test_openapi.py` - tests of working with OpenAPI
- `tests/test_formatter.py` - data formatter tests
- `tests/test_client.py` - HTTP client tests

## Run tests

### Run all tests
```bash
python -m pytest tests/
```

### Run with verbose output
```bash
python -m pytest tests/ -v
```

### Run a specific test
```bash
python -m pytest tests/test_request_builder.py -v
```

### Run with code coverage
```bash
python -m pytest tests/ --cov=talkie
```

## Mock server

`pytest-httpserver` is used for integration tests. Example of mock server setup:

```python
@pytest.fixture
def mock_server(request):
from pytest_httpserver import HTTPServer

server = HTTPServer()
server.start()

# Response setup
server.expect_request("/api/users", method="GET").respond_with_json([
{"id": 1, "name": "User 1"},
{"id": 2, "name": "User 2"}
])

yield server
server.stop()
```

## Test writing

### Basic principles
1. Each test should be independent
2. Use descriptive names for tests
3. Follow the AAA (Arrange-Act-Assert) pattern
4. Use fixtures for common code

### Example test
```python
def test_parse_headers():
"""Header parsing test."""
headers = [
"Content-Type: application/json",
"Authorization: Bearer token123"
]

builder = RequestBuilder(
method="GET",
url="https://example.com/api",
headers=headers
)

assert builder.headers == {
"Content-Type": "application/json",
"Authorization": "Bearer token123"
}
```

### Edge case testing
Make sure to test:
- Empty values
- Incorrect data
- Special characters
- Boundary values
- Duplicate data

## Known issues

1. Warning about deprecated method in OpenAPI validator:
- Fixed by replacing `validate_spec` with `validate`

2. Asynchronous tests:
- When writing asynchronous tests, use `@pytest.mark.asyncio`
- Set up event loop scope in `conftest.py`

3. Temporary files:
- Use `tempfile` to create temporary files
- Make sure files are deleted after tests